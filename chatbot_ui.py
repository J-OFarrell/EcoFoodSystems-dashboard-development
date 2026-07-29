"""
Floating chat widget UI for the dashboard assistant.

Built once and attached to the global app.layout so it persists across
tab/city navigation (see app.py).
"""

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

                dcc.Loading(
                    type="dot",
                    color=brand_colors["Teal"],
                    children=html.Div(
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
                    "borderRadius": "0 0 12px 12px",
                }),
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


def render_messages(history):
    """Render only the user-facing turns (skip tool calls/results) as chat bubbles."""
    bubbles = []
    for msg in history:
        role = msg.get("role")
        content = msg.get("content")
        if role in ("user", "assistant") and content:
            bubbles.append(_bubble(role, content))
    if not bubbles:
        bubbles = [html.Div(
            "Hi! Ask me where to find something on the dashboard, or about the data itself.",
            style={"color": "#888", "fontSize": "0.85em", "fontStyle": "italic"},
        )]
    return bubbles
