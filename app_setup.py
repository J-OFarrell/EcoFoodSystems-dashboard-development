"""
Dash app instantiation, auth, and the top-level app.layout assembly.

app.py does `from app_setup import app` instead of constructing the Dash
instance inline - this module's job is just to get `app` fully configured
(auth, layout, the one clientside callback tied to layout) before any of
app.py's own @app.callback functions register against it.
"""

import os

import dash_auth
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Output, Input

from tab_layouts import landing_page_layout
from chatbot_ui import chatbot_widget

app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.server.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24).hex()

VALID_USERNAME = os.environ.get('DASH_USERNAME')
VALID_PASSWORD = os.environ.get('DASH_PASSWORD')

if not VALID_USERNAME or not VALID_PASSWORD:
    raise RuntimeError(
        "DASH_USERNAME and DASH_PASSWORD must be set as environment variables "
        "(e.g. via a local .env file - see .env.example)."
    )

auth = dash_auth.BasicAuth(
    app,
    {VALID_USERNAME: VALID_PASSWORD}
)

#------------------------- App Layout ----------------------- #

app.layout = html.Div([
    dcc.Loading(
        id="global-page-loader",
        type="circle",
        fullscreen=True,
        color="#A51E22",  # optional: brand red
        children=html.Div(id="page-content")
    ),
    dcc.Store(id='selected-city', data='addis'),  # default city
    dcc.Store(id='atlas-open-tab', data=None),
    dcc.Store(id='sh-table-page-size-store', data=13),

    dcc.Interval(id='resize-interval', interval=1000, n_intervals=0),
    html.Div(id="tab-content", children=landing_page_layout(selected_city='addis'), style={"width": "100%",
                                                                       "height": "100%"}),
    chatbot_widget(),
    # Parent container for full page
], style={
    "display": "flex",
    "flexDirection": "column",
    "height": "100vh",
    "width": "100vw"
})

# Clientside callback to compute page size based on window height
app.clientside_callback(
    """
    function(n) {
        // Estimate available height for table rows (px)
        var h = window.innerHeight || 800;
        // Reserve space for headers, padding, other UI (approx)
        var reserved = 260; // tweak if needed
        var rowHeight = 44; // approximate row height including padding
        var avail = h - reserved;
        var pageSize = Math.max(5, Math.floor(avail / rowHeight));
        return pageSize;
    }
    """,
    Output('sh-table-page-size-store', 'data'),
    Input('resize-interval', 'n_intervals')
)
