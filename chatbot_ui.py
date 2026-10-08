"""
Floating chat widget UI for the dashboard assistant.

Built once and attached to the global app.layout so it persists across
tab/city navigation (see app.py).
"""

import time

from dash import html, dcc

from config import brand_colors

# The button and panel are both positioned relative to this single wrapper
# (position: fixed, dragged as one unit) rather than each having their own
# independent `position: fixed` - two separately-draggable elements is
# exactly the bug that made them drift apart when dragged individually.
WRAPPER_STYLE_BASE = {
    "position": "fixed",
    "bottom": "24px",
    "left": "24px",
    "zIndex": "1000",
}

PANEL_STYLE_BASE = {
    "position": "absolute",
    "bottom": "66px",
    "left": "0",
    "width": "340px",
    "backgroundColor": "white",
    "borderRadius": "12px",
    "boxShadow": "0 6px 24px rgba(0,0,0,0.25)",
    "overflow": "hidden",
}


def chatbot_widget():
    """Floating toggle button + collapsible chat panel - one draggable unit."""
    return html.Div(
        id="chatbot-widget-wrapper",
        style=WRAPPER_STYLE_BASE,
        children=[
        dcc.Store(id="chatbot-history", storage_type="session", data=[]),
        # Set by the fast "show my message now" callback, consumed by the
        # slower "get the real answer" callback - this is what lets sending
        # feel instant even though the actual LLM call can take 10-40s. Each
        # send sets a unique value (not just the text) so re-sending the same
        # question twice in a row still triggers the second callback.
        dcc.Store(id="chatbot-pending-trigger", storage_type="memory", data=None),
        # Raw quota snapshot (see chatbot_client.get_quota_status) - the
        # rendered display text only actually gets fresher numbers when a
        # real message is sent (Groq doesn't expose a way to check quota
        # without spending tokens), but the "as of Xs/m ago" age wording
        # should keep ticking up in between - chatbot-quota-tick's callback
        # re-renders from this stored raw data without any new API call.
        dcc.Store(id="chatbot-quota-raw", storage_type="memory", data=None),
        dcc.Interval(id="chatbot-quota-tick", interval=15 * 1000, n_intervals=0),

        html.Button(
            "\U0001F4AC",
            id="chatbot-toggle-btn",
            n_clicks=0,
            title="Dashboard Assistant",
            style={
                "position": "absolute",
                "bottom": "0",
                "left": "0",
                "width": "56px",
                "height": "56px",
                "borderRadius": "50%",
                "backgroundColor": brand_colors["Teal"],
                "color": "white",
                "border": "none",
                "fontSize": "24px",
                "boxShadow": "0 4px 12px rgba(0,0,0,0.25)",
                "cursor": "pointer",
            },
        ),

        html.Div(
            id="chatbot-panel",
            children=[
                html.Div([
                    html.Span("Dashboard Assistant", style={
                        "fontWeight": "bold", "color": "white", "fontSize": "1em",
                    }),
                    html.Button(
                        "×",
                        id="chatbot-close-btn",
                        n_clicks=0,
                        style={
                            "background": "none", "border": "none", "color": "white",
                            "fontSize": "20px", "cursor": "pointer", "float": "right",
                            "lineHeight": "1", "padding": "0",
                        },
                    ),
                ], id="chatbot-panel-header", style={
                    "backgroundColor": brand_colors["Teal"],
                    "padding": "10px 14px",
                    "borderRadius": "12px 12px 0 0",
                    "cursor": "move",
                }),

                # No dcc.Loading overlay here on purpose - the "Thinking..." bubble
                # (see chatbot_ui.render_pending_turn / app.py's two-stage send
                # callbacks) shows inline in the message flow instead, the same way
                # Claude/ChatGPT do it, rather than a spinner overlaying the whole panel.
                html.Div(
                    id="chatbot-messages",
                    style={
                        "height": "360px",
                        "overflowY": "auto",
                        "padding": "12px",
                        "backgroundColor": "white",
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "8px",
                    },
                ),

                html.Div(
                    id="chatbot-error-banner",
                    style={"display": "none", "padding": "6px 12px", "color": "#a80050",
                           "fontSize": "0.85em", "backgroundColor": "white"},
                ),

                html.Div([
                    dcc.Input(
                        id="chatbot-input",
                        type="text",
                        placeholder="Ask about the dashboard or data...",
                        autoComplete="off",
                        style={
                            "flex": "1", "borderRadius": "8px",
                            "border": "1px solid #ccc", "padding": "8px",
                        },
                        n_submit=0,
                    ),
                    html.Button("Send", id="chatbot-send-btn", n_clicks=0, style={
                        "marginLeft": "8px",
                        "backgroundColor": brand_colors["Teal"],
                        "color": "white",
                        "border": "none",
                        "borderRadius": "8px",
                        "padding": "8px 14px",
                        "cursor": "pointer",
                    }),
                ], style={
                    "display": "flex",
                    "padding": "10px",
                    "borderTop": "1px solid #eee",
                    "backgroundColor": "white",
                }),

                html.Div(
                    id="chatbot-quota-display",
                    style={
                        "padding": "4px 12px 8px",
                        "fontSize": "0.72em",
                        "color": "#999",
                        "backgroundColor": "white",
                        "borderRadius": "0 0 12px 12px",
                    },
                ),
            ],
            style={**PANEL_STYLE_BASE, "display": "none"},
        ),
        ],
    )


def _bubble(role, text):
    is_user = role == "user"
    bubble_style = {
        "alignSelf": "flex-end" if is_user else "flex-start",
        "backgroundColor": brand_colors["Mid green"] if is_user else "#f0f0f0",
        "color": brand_colors["Brown"] if is_user else "#222",
        "padding": "8px 12px",
        "borderRadius": "12px",
        "maxWidth": "80%",
        "fontSize": "0.9em",
    }
    if is_user:
        # User input is plain text, not interpreted as markdown.
        return html.Div(text, style={**bubble_style, "whiteSpace": "pre-wrap"})
    return dcc.Markdown(text, style=bubble_style, className="chatbot-assistant-bubble")


def _history_bubbles(history):
    """Render only the user-facing turns (skip tool calls/results) as chat bubbles - no
    empty-state placeholder, since callers differ on whether one is wanted here."""
    return [
        _bubble(msg.get("role"), msg.get("content"))
        for msg in history
        if msg.get("role") in ("user", "assistant") and msg.get("content")
    ]


def _thinking_bubble():
    return html.Div(
        "Thinking...",
        style={
            "alignSelf": "flex-start",
            "backgroundColor": "#f0f0f0",
            "color": "#888",
            "padding": "8px 12px",
            "borderRadius": "12px",
            "maxWidth": "80%",
            "fontSize": "0.9em",
            "fontStyle": "italic",
        },
    )


def render_messages(history):
    """Render the full committed conversation as chat bubbles (empty-state placeholder
    shown when there's nothing yet)."""
    bubbles = _history_bubbles(history)
    if not bubbles:
        bubbles = [html.Div(
            "Hi! Ask me where to find something on the dashboard, or about the data itself.",
            style={"color": "#888", "fontSize": "0.85em", "fontStyle": "italic"},
        )]
    return bubbles


def render_pending_turn(history, user_text):
    """Render the committed history plus the just-sent user message and a 'Thinking...'
    placeholder for the not-yet-ready reply - shown immediately on send (optimistic UI),
    before the slower second-stage callback comes back with the real answer."""
    return _history_bubbles(history) + [_bubble("user", user_text), _thinking_bubble()]


def _quota_color(used, limit):
    """Green/orange/red by how much headroom is left - not by absolute value,
    since 'plenty left' vs 'nearly exhausted' matters more than the raw count."""
    if not limit:
        return "#999"
    fraction_remaining = 1 - (used / limit)
    if fraction_remaining > 0.5:
        return "#2e7d32"
    if fraction_remaining > 0.15:
        return "#e65100"
    return "#c62828"


def _format_age(checked_at):
    age_seconds = time.time() - checked_at
    if age_seconds < 15:
        return "just now"
    if age_seconds < 60:
        return f"~{int(age_seconds)}s ago"
    if age_seconds < 3600:
        return f"~{int(age_seconds // 60)}m ago"
    return f"~{int(age_seconds // 3600)}h ago"


def render_quota_status(quota):
    """Render the last-known Groq TPM/TPD quota snapshot (see
    chatbot_client.get_quota_status) as a small color-coded status line.

    Neither figure is ever truly "live" in the polling sense - Groq only
    reveals quota state as a side effect of an actual request, so both are
    labeled with how long ago they were last confirmed. The 'as of' wording
    is refreshed periodically by chatbot-quota-tick even between messages
    (see app.py), but the token counts themselves only change when a real
    message is actually sent.
    """
    if not quota:
        return ""

    tpm = quota.get("tpm")
    tpd = quota.get("tpd")
    parts = []

    if tpm:
        tpm_age_seconds = time.time() - tpm["checked_at"]
        if tpm_age_seconds >= 60:
            # TPM is a rolling 60-second window - once that much time has
            # passed with no new reading, this window's usage has genuinely
            # reset, even though we haven't made a new request to confirm it.
            # Showing the stale pre-reset number here would be actively
            # misleading (exactly what looked like a bug/outdated display).
            parts.append(html.Span(
                f"0/{tpm['limit']} tokens this minute (reset - last checked {_format_age(tpm['checked_at'])})",
                style={"color": _quota_color(0, tpm["limit"])},
            ))
        else:
            used = tpm["limit"] - tpm["remaining"]
            parts.append(html.Span(
                f"{used}/{tpm['limit']} tokens this minute ({_format_age(tpm['checked_at'])})",
                style={"color": _quota_color(used, tpm["limit"])},
            ))

    if tpd:
        parts.append(html.Span(
            f"~{tpd['used']}/{tpd['limit']} tokens today (as of {_format_age(tpd['checked_at'])})",
            style={"color": _quota_color(tpd["used"], tpd["limit"])},
        ))

    if not parts:
        return ""

    children = []
    for i, part in enumerate(parts):
        if i > 0:
            children.append(html.Span(" · ", style={"color": "#999"}))
        children.append(part)
    return children
