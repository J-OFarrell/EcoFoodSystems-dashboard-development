"""
Shared UI components for EcoFoodSystems Dashboard
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from config import brand_colors, tabs_style


# ========================== Sidebar ==========================

_SIDEBAR_TABS = [
    ("Food Systems Stakeholders",                    "tab-1-stakeholders",      "stakeholders"),
    ("Food Flows & Supply Chains",                   "tab-2-supply",            "supply"),
    ("Sustainability Metrics",                       "tab-3-sustainability",    "sustainability"),
    ("Multidimensional Poverty",                     "tab-4-poverty",           "poverty"),
    ("Labour, Skills & Green Jobs",                  "tab-5-labour",            "labour"),
    ("Resilience",                                   "tab-6-resilience",        "resilience"),
    ("Food Environments",                            "tab-7-food-environments", "food-environments"),
    ("Food Losses & Waste",                          "tab-8-losses",            "losses"),
    ("Policies & Regulation",                        "tab-9-policies",          "policies"),
    ("Nutrition & Health",                           "tab-10-nutrition",        "nutrition"),
    ("Environmental Footprints",                     "tab-11-footprints",       "footprints"),
    ("Behaviour Change Tool (AI Chatbot & Game)",    "tab-12-behaviour",        "behaviour"),
]


def make_sidebar(selected_city='hanoi'):
    import hanoi_config
    import addis_config
    tab_backgrounds = hanoi_config.TAB_BACKGROUNDS if selected_city == 'hanoi' else addis_config.TAB_BACKGROUNDS

    nav_items = [
        dbc.NavItem(
            dbc.NavLink([
                html.Img(
                    src="/assets/logos/home_button.svg",
                    alt="Home",
                    style={
                        "height": "28px",
                        "width": "28px",
                        "verticalAlign": "middle",
                        "marginRight": "8px",
                        "marginBottom": "3px"
                    }
                ),
                html.Span("Home", style={
                    "verticalAlign": "middle",
                    "fontWeight": "bold",
                    "fontSize": "1.08em"
                })
            ], id="tab-home", style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "backgroundColor": brand_colors['Light green'],
                "color": brand_colors['Brown'],
                "borderRadius": "8px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.15)",
                "letterSpacing": "0.5px",
                "padding": "6px 4px",
            }, href="#", active="exact"),
            style={"marginBottom": "8px", "textAlign": "center", 'width': '90%'}
        ),
    ]

    for label, tab_id, bg_key in _SIDEBAR_TABS:
        is_coming_soon = tab_backgrounds.get(bg_key, "#ffffff") == "#f4f4f4"
        link_content = html.Div([
            html.Span(label),
            html.Span("Coming soon", className="dash-landing-btn-coming-soon") if is_coming_soon else None,
        ])
        nav_link_style = {
            "opacity": "0.45",
            "cursor": "default",
            "pointerEvents": "none",
        } if is_coming_soon else {}
        nav_items.append(
            dbc.NavItem(
                dbc.NavLink(link_content, id=tab_id, href="#", active="exact", style=nav_link_style),
                style=tabs_style
            )
        )

    return dbc.Card([
        dbc.Nav(
            nav_items,
            vertical="md",
            pills=True,
            fill=True,
            style={
                "marginTop": "20px",
                "alignItems": "center",
                "textAlign": "center",
                "zIndex": 1000,
            }
        ),
    ], style={
        "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
        "borderRadius": "12px",
        "padding": "10px",
        "height": "100%",
        "width": "100%",
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "flex-start",
        "overflowY": "auto",
        "backgroundImage": "url('/assets/photos/sidebar_img_compressed.jpg')",
        "backgroundSize": "cover",
        "backgroundPosition": "center",
        "backgroundRepeat": "no-repeat",
    })


sidebar_hanoi = make_sidebar('hanoi')
sidebar_addis = make_sidebar('addis')
sidebar = sidebar_hanoi  # backward-compat for app.py import


# ========================== City Selector ==========================

def city_selector(selected_city='addis', visible=True):
    """
    City selector dropdown component.
    Must be included in all layouts for callbacks to work properly.
    Set visible=False to hide it on tab pages.
    """
    return html.Div([
        # Indicator Atlas button
        html.Div([
            dbc.Button(
                "Indicator Atlas",
                id='atlas-top-button',
                color='danger',
                n_clicks=0,
                style={
                    "fontSize": "1.1em",
                    "fontWeight": "bold",
                    "borderRadius": "10px",
                    "border": "none",
                    "color": brand_colors['Brown'],
                    "backgroundColor": brand_colors['Mid green'],
                    "padding": "12px 20px",
                    "boxShadow": "0 4px 10px rgba(0,0,0,0.12)",
                    "minWidth": "160px",
                }
            )
        ], style={
            "position": "absolute",
            "left": "2%",
            "top": "50%",
            "transform": "translateY(-50%)",
            "display": "flex" if visible else "none",
            "alignItems": "center",
        }),

        # Dropdown selector
        html.Div([
            html.Label("City:", style={
                "color": brand_colors['Brown'],
                "fontSize": "0.9em",
                "marginRight": "8px",
                "fontWeight": "600"
            }),
            dcc.Dropdown(
                id='city-selector',
                options=[
                    {'label': 'Addis Ababa', 'value': 'addis'},
                    {'label': 'Hanoi', 'value': 'hanoi'}
                ],
                value=selected_city,
                clearable=False,
                searchable=False,
                style={
                    "width": "200px",
                    "fontSize": "0.95em"
                }
            )
        ], style={
            "position": "absolute",
            "right": "2%",
            "top": "50%",
            "transform": "translateY(-50%)",
            "display": "flex" if visible else "none",
            "alignItems": "center",
            "gap": "3px"
        })
    ])


# ========================== Footer ==========================

footer = html.Footer([
    html.Div([
        html.Img(src="/assets/logos/EcoFoodSystems.svg", style={'height': '45px', 'margin': '0 30px'}),
        html.Img(src="/assets/logos/WUR.png", style={'height': '50px', 'margin': '0px 30px'}),
        html.Img(src="/assets/logos/DeSIRA.png", style={'height': '50px', 'margin': '0 30px'}),
        html.Img(src="/assets/logos/IFAD.png", style={'height': '50px', 'margin': '0 30px'}),
        html.Img(src="/assets/logos/Rikolto.png", style={'height': '30px', 'margin': '0 30px'}),
        html.Img(src="/assets/logos/RyanInstitute.png", style={'height': '60px', 'margin': '0 30px'})
    ], style={
        "display": "flex",
        "justifyContent": "center",
        "alignItems": "flex-end",
        "margin": "20px 0px",
    })
])
