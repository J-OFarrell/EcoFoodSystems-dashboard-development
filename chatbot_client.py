"""
LLM client for the dashboard assistant chatbot.

All calls to the underlying LLM provider go through this module only.
Switching providers later (e.g. to Claude) means rewriting this file only -
nothing else in the app talks to the provider directly.
"""

import os
import re
import time

import groq
from groq import Groq

# llama-3.3-70b-versatile was tried first but unreliably emitted malformed
# pseudo-function-call text instead of proper structured tool calls (Groq
# rejected it with "tool_use_failed"). gpt-oss-120b handles tool calling
# reliably in testing.
MODEL = "openai/gpt-oss-120b"

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY must be set as an environment variable "
        "(e.g. via a local .env file - see .env.example)."
    )

_client = Groq(api_key=GROQ_API_KEY)

# Best-effort snapshot of the last known Groq quota state, for showing users
# how close they are to a rate limit. TPM (tokens per minute) updates on
# EVERY successful call, since Groq returns it in response headers. TPD
# (tokens per day) only updates when a TPD-specific rate-limit error actually
# occurs - Groq does not expose daily usage in normal response headers, only
# in the 429 error body - so the daily figure can go stale between such
# errors and is labeled as such when displayed.
_last_known_quota = {"tpm": None, "tpd": None}

_QUOTA_ERROR_RE = re.compile(
    r"tokens per (minute|day) \((?:TPM|TPD)\): Limit (\d+), Used (\d+), Requested (\d+)\. "
    r"Please try again in ([\w.]+)"
)


def _record_quota_from_headers(headers):
    try:
        limit = int(headers.get("x-ratelimit-limit-tokens"))
        remaining = int(headers.get("x-ratelimit-remaining-tokens"))
    except (TypeError, ValueError):
        return
    _last_known_quota["tpm"] = {
        "limit": limit,
        "remaining": remaining,
        "checked_at": time.time(),
    }


def _record_quota_from_error(error_text):
    match = _QUOTA_ERROR_RE.search(error_text)
    if not match:
        return
    period, limit, used, _requested, retry_after = match.groups()
    entry = {
        "limit": int(limit),
        "used": int(used),
        "retry_after": retry_after.rstrip("."),
        "checked_at": time.time(),
    }
    if period == "minute":
        _last_known_quota["tpm"] = {
            "limit": entry["limit"],
            "remaining": entry["limit"] - entry["used"],
            "checked_at": entry["checked_at"],
        }
    else:
        _last_known_quota["tpd"] = entry


def get_quota_status():
    """Return the last known {'tpm': {...} | None, 'tpd': {...} | None} snapshot."""
    return dict(_last_known_quota)


def ask(messages, tools=None):
    """
    Send a chat completion request to the LLM.

    messages: list of {"role": ..., "content": ...} dicts.
    tools: optional list of tool definitions (JSON schema, function-calling format).

    Returns the response message object (attributes: .content, .tool_calls).
    """
    kwargs = {"model": MODEL, "messages": messages}
    if tools:
        kwargs["tools"] = tools

    try:
        raw = _client.with_raw_response.chat.completions.create(**kwargs)
    except groq.RateLimitError as exc:
        _record_quota_from_error(str(exc))
        raise

    response = raw.parse()
    _record_quota_from_headers(raw.headers)
    return response.choices[0].message
