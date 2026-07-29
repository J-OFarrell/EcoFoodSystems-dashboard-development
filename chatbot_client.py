"""
LLM client for the dashboard assistant chatbot.

All calls to the underlying LLM provider go through this module only.
Switching providers later (e.g. to Claude) means rewriting this file only -
nothing else in the app talks to the provider directly.
"""

import os

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
    response = _client.chat.completions.create(**kwargs)
    return response.choices[0].message
