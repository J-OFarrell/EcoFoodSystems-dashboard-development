"""
Chat turn orchestration for the dashboard assistant: runs the tool-call loop
against chatbot_client.ask(), and a simple per-IP rate limiter.
"""

import json
import re
import time
from collections import defaultdict, deque

import chatbot_client
import chatbot_tools
from data_access import PILLARS

_MAX_TOOL_ITERATIONS = 8

_SYSTEM_PROMPT = (
    "You are a helpful assistant embedded in the EcoFoodSystems dashboard, a "
    "food-systems research tool covering Addis Ababa and Hanoi. You help users "
    "(1) navigate the dashboard - find which tab/pillar covers a topic - and "
    "(2) understand the underlying data - what an indicator means, or its "
    "actual value. Use the available tools to look up real information rather "
    "than guessing. Keep answers concise.\n\n"
    "The dashboard's indicators are organized under exactly these pillars, "
    f"and no others: {', '.join(PILLARS)}. When asked what pillars/topics/"
    "categories the dashboard covers, or how it's organized, state these "
    "exact names verbatim - never shorten, paraphrase, or invent a pillar "
    "name (e.g. 'Food Supply' or 'Nutrition' are NOT real pillar names here; "
    "the real ones are 'Food Supply Chains', and nutrition topics live under "
    "the 'Outcomes' pillar as a sub-theme, not as their own pillar). If you "
    "aren't sure an indicator or sub-topic maps to a given pillar, use "
    "describe_indicator or list_available_indicators to confirm rather than "
    "guessing.\n\n"
    "NEVER state which pillar or sub-domain a SPECIFIC named indicator "
    "belongs to unless describe_indicator (or list_available_indicators) "
    "actually returned that pillar for it in this conversation - not from "
    "memory, not from what seems logical. Some indicators - notably the raw "
    "poverty-index variables ('Multidimensional Poverty Index', 'Assets', "
    "'Cooking fuel', 'Drinking water', 'Electricity', 'Housing', "
    "'Sanitation') - exist only in the numeric dataset get_indicator_value "
    "reads from and have NO entry in the atlas describe_indicator searches, "
    "so describe_indicator will correctly return 'No indicator found' for "
    "them. If that happens, say plainly that you don't have a documented "
    "pillar/category for that indicator - do NOT then guess one anyway just "
    "because it sounds plausible (e.g. do not say 'MPI falls under Outcomes' "
    "or 'Cooking fuel is under Individual Factors' unless a tool call in "
    "this conversation actually returned that). You can still offer to look "
    "up its real values with get_indicator_value regardless.\n\n"
    "NEVER name a specific data source, survey, organization, agency, or "
    "publication year for where the dashboard's data comes from (e.g. "
    "'World Bank', 'WHO', 'DHS', 'LSMS', a specific survey year) unless "
    "describe_indicator actually returned that exact string in its "
    "'data_source' field in this conversation. General knowledge about what "
    "sources food-systems dashboards 'typically' use is not this project's "
    "documented sources and must not be presented as if it were - this has "
    "happened before and the fabricated sources were completely wrong "
    "(invented organizations and a fake citation with a made-up year). If "
    "asked broadly 'what are your data sources' without a specific indicator "
    "named, say you'd need to look at a specific indicator to give its real "
    "documented source (via describe_indicator), rather than describing "
    "sources in general terms.\n\n"
    "For 'Life cycle assessment of food items' (Processing and packaging / "
    "Food Supply Chains) or any other question about a food item's "
    "environmental footprint (GHG emissions, freshwater use, acidification, "
    "eutrophication), use get_food_item_environmental_impact, NOT "
    "get_indicator_value - this data is Addis-only, keyed by food item/food "
    "group, not by region, and lives in a separate dataset. If the user "
    "references a food group (e.g. 'Cereals & Grains') rather than one "
    "specific item, pass food_group and summarize the returned set - do not "
    "ask which single item they meant when they've already told you the "
    "group.\n\n"
    "For 'Food outlet accessibility' (Food Environments / Vendor properties) "
    "or any question about what fraction of a population group can reach a "
    "type of food outlet within some travel time, use "
    "get_food_accessibility_value, NOT get_indicator_value - covers both "
    "cities, and needs BOTH a population category (e.g. 'men', 'women', "
    "'total') and an outlet category (e.g. 'amenity_fast_food', "
    "'shop_bakery') to return anything; transport mode (walk/drive/"
    "multimodal) and travel time (5/10/15 minutes only) default sensibly "
    "(walk, 15 minutes) if the user doesn't specify them, so don't withhold "
    "an answer just because those two weren't given - only population and "
    "outlet category are actually required. If no region is given, Addis "
    "returns all 10 districts but Hanoi (126 communes) returns a summary "
    "(average/highest/lowest) instead of every value - mention that's a "
    "summary, not an exhaustive list, if relevant.\n\n"
    "get_indicator_value covers MPI (both cities) plus - Hanoi only - food "
    "affordability and nutrition/diet indicators. For everything else in "
    "Hanoi's per-subdomain time-series data (GRDP growth, population, "
    "literacy rate, trade/self-sufficiency rates, diesel price, food CPI, "
    "market counts, poverty rate, social security coverage, and similar - "
    "anything that's a yearly/quarterly/monthly series rather than a "
    "per-district snapshot), use get_subdomain_indicator_value instead - try "
    "it before concluding an indicator isn't available, since it covers many "
    "more topics than get_indicator_value does. If none of your four data "
    "tools (get_indicator_value, get_subdomain_indicator_value, "
    "get_food_item_environmental_impact, get_food_accessibility_value) "
    "matches, say this indicator's data isn't available through your current "
    "tools rather than concluding the dashboard has no such data at all - a "
    "few real datasets (climate/disaster records, land-use/land-cover) "
    "aren't wired up to you yet. get_subdomain_indicator_value is Hanoi-only "
    "for now; no equivalent per-subdomain data exists for Addis yet.\n\n"
    "IMPORTANT: You have zero visual access to the page - no pixels, no chart "
    "image, no DOM, nothing. You only know two things: (a) the [Current page "
    "context] hint below, if present, naming which indicator is open, and (b) "
    "whatever your tools (list_available_indicators, describe_indicator, "
    "get_indicator_value) literally return as text/numbers.\n\n"
    "You do NOT know, and must NEVER state, any of the following, even as a "
    "generalization, a 'typically' hedge, or a table of 'what this usually "
    "shows': what a bar/line/map/chart looks like; what a bar, color, or map "
    "region 'represents' or 'corresponds to'; how many charts, maps, or panels "
    "are on the page; axis labels or orientation; legends, tooltips, buttons, "
    "filters, or dropdowns; whether something is empty, a placeholder, or has "
    "data. All of these are properties of the page's rendering, which you "
    "cannot see - stating any of them, even hedged, is fabrication. This has "
    "happened repeatedly and every single instance was wrong.\n\n"
    "When asked to 'explain this graph/chart/map/page': (1) resolve the real "
    "indicator via page context + list_available_indicators/describe_indicator, "
    "(2) call get_indicator_value, (3) answer using ONLY two things: what the "
    "indicator conceptually measures (from describe_indicator's text) and its "
    "actual retrieved values by region (from get_indicator_value) - as a plain "
    "sentence or list of region/value pairs, never described as 'the bars' or "
    "'the map colors'. If get_indicator_value errors, its response includes "
    "'available_indicator_keys_for_this_city' - the real, valid keys for that "
    "city. Before concluding no data exists, check that list for anything "
    "clearly related (e.g. the page context mentions poverty and the list has "
    "'Multidimensional Poverty Index' - that's a match, use it) and retry with "
    "it. Only say data isn't available after that list has no plausible match. "
    "Never conclude no data exists just because your first guessed key failed. "
    "If no page context is present and the question is vague, say "
    "plainly you don't know what they currently have open and ask them to "
    "name the indicator."
)

_RATE_LIMIT_WINDOW_SECONDS = 60
_RATE_LIMIT_MAX_REQUESTS = 15
_request_log = defaultdict(deque)

# Kept as a hard fallback (not the primary mechanism anymore): in testing, the
# model did not reliably follow a plain "you can't see the screen" prompt
# instruction and confidently fabricated chart details (wrong axes, invented
# buttons/filters that don't exist). Now that real page context is threaded
# through from the dashboard's own navigation state (see page_context below),
# this only fires when the user references "the graph/page/etc." AND we have
# no page context at all to ground an answer in - e.g. they're on the plain
# landing view with nothing specific open.
_SCREEN_REFERENCE_KEYWORDS = [
    "this graph", "the graph", "this chart", "the chart", "this map", "the map",
    "on screen", "on the screen", "on my screen", "in the background",
    "this page", "current page", "this visual", "this image", "this picture",
    "currently showing", "currently displayed", "what i'm looking at",
    "what i am looking at", "in front of me",
]

_CANNOT_SEE_SCREEN_RESPONSE = (
    "I don't have any information about what you currently have open on the "
    "dashboard, so I can't describe a specific chart or page - anything I said "
    "would be a guess. If you tell me the name of the indicator, I can explain "
    "what it measures and look up its actual values for you."
)


def _mentions_screen_reference(text):
    lowered = text.lower()
    return any(kw in lowered for kw in _SCREEN_REFERENCE_KEYWORDS)


def _page_context_note(page_context, is_screen_reference_question):
    """Build a grounding hint from the dashboard's own navigation state.

    The 'atlas-open-tab' dcc.Store this comes from has THREE different
    payload shapes depending on which navigation path the user took
    (confirmed by reading app.py's open_atlas_target_tab callback):
      1. Atlas home-card "Explore" buttons:
         {"tab": "subdomain", "subdomain": "income-growth-distribution", "city": ...}
      2. Left sidebar indicator buttons (a separate, equally common path):
         {"tab": "tab-4-poverty", "subview": "...", "city": ...}
      3. Landing-page pillar tab clicks (home-pillar-atlas-btn) - NOTE this
         one is keyed by "section", not "subdomain"/"tab" pointing anywhere
         specific, and its "tab" value is literally "tab-home":
         {"tab": "tab-home", "section": "Cross-Cutting Issues", "city": ...}
         This shape was previously not checked for at all, so page context
         from clicking a landing-page pillar tab was silently discarded
         (treated as "no context") every time - confirmed via a real test
         where the model answered correctly only because the user's own
         question happened to name the pillar, not because this function
         actually surfaced the real page state.
    All are just internal keys, not confirmed indicator names - either way
    the model must still resolve them via list_available_indicators /
    describe_indicator rather than assuming the wording is exact.

    is_screen_reference_question: whether THIS message actually asked about
    what's on the user's screen (see _mentions_screen_reference). The
    "state what you resolved to" opening (e.g. "You're currently viewing
    X for Y") is only appropriate for that kind of question - it was
    previously applied unconditionally whenever page context existed at
    all, which caused it to fire on plain navigation-help requests too
    (e.g. "help me find poverty data"), confidently announcing a screen
    state the user never asked about and that didn't match what they were
    actually looking at.
    """
    if not page_context:
        return None

    city = page_context.get("city") or "addis"

    if is_screen_reference_question:
        opening_instruction = (
            "The user is asking about what's on their screen, so open your "
            "reply by stating the exact indicator/pillar and city you "
            "resolved this to (e.g. 'You're currently viewing [indicator] "
            "for [city].') before anything else - this makes it visible if "
            "the page you're actually on doesn't match what the "
            "conversation implied."
        )
    else:
        opening_instruction = (
            "This is a general navigation/topic question, NOT a request to "
            "explain the current screen - do NOT open with 'You're "
            "currently viewing...'/'You're looking at...' or claim to know "
            "what's on their screen. Just answer their actual question "
            "directly; use this page context only as a soft hint for which "
            "pillar/indicator is relevant, not as something to announce."
        )

    if page_context.get("subdomain"):
        slug = page_context["subdomain"]
        readable_hint = slug.replace("-", " ").replace("_", " ")
    elif page_context.get("section"):
        # Pillar-level overview (landing page), not any one specific
        # indicator - there's no single "graph" to explain here, so the
        # grounded answer is to list what's actually in this pillar, not
        # guess one indicator the way the other two shapes do.
        section = page_context["section"]
        return (
            f"[Current page context: the user is browsing the pillar-level "
            f"overview for pillar='{section}' (city='{city}') on the "
            f"dashboard's home page - this is NOT a specific indicator's "
            f"data or graph, just a list of what's in that pillar. If asked "
            f"to 'explain this page/graph' or similar, do not guess a single "
            f"indicator - call list_available_indicators(city='{city}', "
            f"pillar='{section}') and summarize what's available in this "
            f"pillar instead. Only resolve to one specific indicator if the "
            f"user names one themselves. {opening_instruction}]"
        )
    else:
        tab_id = page_context.get("tab")
        if not tab_id or tab_id == "tab-home":
            return None
        # e.g. "tab-4-poverty" -> "poverty", "tab-11-footprints" -> "footprints"
        slug = re.sub(r"^tab-\d+-", "", tab_id)
        readable_hint = slug.replace("-", " ").replace("_", " ")
        subview = page_context.get("subview")
        if subview:
            readable_hint = f"{readable_hint} - {subview}"

    return (
        f"[Current page context: the user has a dashboard page open for "
        f"city='{city}', internal page key='{slug}' (roughly: '{readable_hint}'). "
        f"This is a hint, not a confirmed indicator name - call "
        f"list_available_indicators(city='{city}') and match the closest real "
        f"indicator to this hint, then call get_indicator_value for it so your "
        f"answer includes real numbers. If nothing matches well, say so rather "
        f"than guessing. Do not describe what a bar/map/chart 'shows' or "
        f"'represents', even generically - only state what the indicator "
        f"means and its real values, as plain facts, never framed as a "
        f"description of the visual. {opening_instruction}]"
    )


def get_provider_quota_status():
    """Passthrough to chatbot_client's last-known Groq TPM/TPD quota snapshot -
    kept here so app.py only ever imports chatbot_engine, not the provider
    client directly (same layering as the rest of this module)."""
    return chatbot_client.get_quota_status()


def check_rate_limit(key):
    """Simple in-memory sliding-window rate limit, keyed by e.g. client IP.

    Per-process only - fine for a single-worker internal tool; a multi-worker
    gunicorn deployment would need a shared store instead (each worker would
    otherwise keep its own separate counter).
    """
    now = time.time()
    q = _request_log[key]
    while q and now - q[0] > _RATE_LIMIT_WINDOW_SECONDS:
        q.popleft()
    if len(q) >= _RATE_LIMIT_MAX_REQUESTS:
        return False
    q.append(now)
    return True


def _message_to_dict(msg):
    d = {"role": msg.role, "content": msg.content}
    if msg.tool_calls:
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in msg.tool_calls
        ]
    return d


# Tools route_tools() is allowed to pick among - deliberately only the four
# "data" tools (the expensive, verbose ones); describe_indicator and
# list_available_indicators are cheap and load-bearing for the hallucination
# guardrails above, so they're always included below regardless of what the
# router decides, rather than trusting a small/fast model with that call too.
_ROUTABLE_TOOL_CATALOG = [
    ("get_indicator_value", "Look up MPI (both cities), or - Hanoi only - food-affordability/nutrition values."),
    ("get_subdomain_indicator_value", "Look up Hanoi per-subdomain time-series values - GRDP, population, literacy, trade rates, diesel price, food CPI, poverty rate, social protection, etc."),
    ("get_food_item_environmental_impact", "Look up a food item's environmental footprint (GHG, freshwater, acidification, eutrophication) - Addis only."),
    ("get_food_accessibility_value", "Look up what % of a population group can reach a food outlet type within a travel time, by district/commune."),
]
_ALWAYS_INCLUDED_TOOLS = {"describe_indicator", "list_available_indicators"}
_TOOL_DEFINITIONS_BY_NAME = {t["function"]["name"]: t for t in chatbot_tools.TOOL_DEFINITIONS}

# How many PAST questions stay in context - the new question being asked
# right now is added on top of this, so in practice a turn sees up to this
# many old exchanges plus the current one. A deliberately simple fix for
# conversations that grow large enough to approach Groq's per-minute token
# limit on their own (confirmed live: a 4-question conversation hit 7839/8000
# TPM even with per-question tool routing already in place, since every new
# message resends the entire history so far). Summarizing old turns instead
# of dropping them (what Claude Code itself does for long conversations) was
# considered and deliberately deferred - a wrong summary silently feeding bad
# context into later answers is a harder failure mode to catch in testing
# than "it forgot something from 5 questions ago," and there wasn't time to
# test that properly before the workshop deadline.
_MAX_HISTORY_QUESTIONS = 4


def _cap_history(messages):
    """Keep only the most recent _MAX_HISTORY_QUESTIONS user-question
    exchanges (plus the original system prompt), dropping everything from
    earlier turns - including any stale page-context system notes those
    turns added, which are no longer relevant anyway.
    """
    user_indices = [i for i, m in enumerate(messages) if m.get("role") == "user"]
    if len(user_indices) <= _MAX_HISTORY_QUESTIONS:
        return messages

    cutoff = user_indices[-_MAX_HISTORY_QUESTIONS]
    system_prompt_msg = messages[0] if messages and messages[0].get("role") == "system" else None
    kept = messages[cutoff:]
    return ([system_prompt_msg] if system_prompt_msg else []) + kept


def _select_tools_for_turn(user_message):
    """Return the subset of TOOL_DEFINITIONS worth sending to MODEL for this
    question - always the two cheap atlas tools, plus whichever data tools
    ROUTER_MODEL thinks are relevant. Falls back to every tool (the original,
    pre-routing behaviour) if the router call fails or returns nothing
    usable, so a router hiccup degrades to "slightly more tokens", never to
    "missing a tool the question needed"."""
    routed_names = chatbot_client.route_tools(user_message, _ROUTABLE_TOOL_CATALOG)
    if routed_names is None:
        return chatbot_tools.TOOL_DEFINITIONS

    selected_names = _ALWAYS_INCLUDED_TOOLS | {
        name for name in routed_names if name in _TOOL_DEFINITIONS_BY_NAME
    }
    return [_TOOL_DEFINITIONS_BY_NAME[name] for name in selected_names]


def run_chat_turn(history, user_message, page_context=None):
    """
    history: list of prior message dicts (may include tool_calls/tool entries).
    user_message: the new user input string.
    page_context: optional raw 'atlas-open-tab' store payload describing which
        indicator page (if any) the user currently has open - lets the bot
        ground "explain this graph" questions in the real, currently-open
        indicator instead of just declining. See _page_context_note().

    Returns the updated message list (history + new turn), ready to be stored
    and re-sent as-is on the next turn. Older turns beyond
    _MAX_HISTORY_QUESTIONS are dropped here, not just excluded from this
    call's API requests - so this also bounds how much keeps accumulating in
    the browser's session storage across a long conversation.
    """
    messages = _cap_history(list(history))
    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": _SYSTEM_PROMPT}] + messages

    is_screen_reference = _mentions_screen_reference(user_message)
    context_note = _page_context_note(page_context, is_screen_reference)

    if is_screen_reference and not context_note:
        messages.append({"role": "user", "content": user_message})
        messages.append({"role": "assistant", "content": _CANNOT_SEE_SCREEN_RESPONSE})
        return messages

    if context_note:
        messages.append({"role": "system", "content": context_note})
    messages.append({"role": "user", "content": user_message})

    # Decided once per user turn (not re-run per tool-call iteration, since
    # the question's intent doesn't change mid-loop) - cuts MODEL's per-call
    # token overhead by only sending the tool definitions this question
    # plausibly needs, instead of all six on every single round trip.
    turn_tools = _select_tools_for_turn(user_message)

    got_final_answer = False
    for _ in range(_MAX_TOOL_ITERATIONS):
        response_message = chatbot_client.ask(messages, tools=turn_tools)
        messages.append(_message_to_dict(response_message))

        if not response_message.tool_calls:
            got_final_answer = True
            break

        for tool_call in response_message.tool_calls:
            fn = chatbot_tools.TOOL_FUNCTIONS.get(tool_call.function.name)
            if fn is None:
                result = {"error": f"Unknown tool '{tool_call.function.name}'"}
            else:
                try:
                    args = json.loads(tool_call.function.arguments)
                    result = fn(**args)
                except Exception as exc:
                    result = {"error": str(exc)}
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "content": json.dumps(result),
            })

    # Hard guarantee: if the tool-call budget ran out mid-loop (the last
    # message is still a tool result, not a text answer), force one final
    # call with tools disabled so the user always gets a written response -
    # this is exactly the bug that caused the widget to "load and stop" with
    # nothing displayed (the conversation ended on a tool-role message, which
    # render_messages() never shows as a bubble).
    if not got_final_answer:
        wrapup_messages = messages + [{
            "role": "user",
            "content": (
                "Based on everything you've found above, answer my original "
                "question now in plain text - do not call any more tools."
            ),
        }]
        response_message = chatbot_client.ask(wrapup_messages)
        messages.append(_message_to_dict(response_message))

    return messages
