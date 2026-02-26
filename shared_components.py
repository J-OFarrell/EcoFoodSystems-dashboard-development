"""
Shared UI components for EcoFoodSystems Dashboard
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from config import brand_colors, tabs_style


# ========================== Sidebar ==========================

sidebar = dbc.Card([
    dbc.Nav([
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
                "color": brand_colors['White'],
                "borderRadius": "8px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.15)",
                "letterSpacing": "0.5px",
                "padding": "6px 4px",
            }, href="#", active="exact"),
            style={"marginBottom": "8px", "textAlign": "center", 'width': '90%'}
        ),
        dbc.NavItem(dbc.NavLink("Food Systems Stakeholders", id="tab-1-stakeholders", href="#", active="exact"), style=tabs_style),
        dbc.NavItem(dbc.NavLink("Food Flows, Supply & Value Chains", id="tab-2-supply", href="#", active="exact"), style=tabs_style),
        dbc.NavItem(dbc.NavLink("Sustainability Metrics & Indicators", id="tab-3-sustainability", href="#", active="exact"), style=tabs_style),
        dbc.NavItem(dbc.NavLink("Multidimensional Poverty", id="tab-4-poverty", href="#", active="exact"), style=tabs_style),
        dbc.NavItem(dbc.NavLink("Labour, Skills & Green Jobs", id="tab-5-labour", href="#", active="exact"), style=tabs_style),
        dbc.NavItem(dbc.NavLink("Resilience to Food System Shocks", id="tab-6-resilience", href="#", active="exact"), style=tabs_style),
        dbc.NavItem(dbc.NavLink("Dietary Mapping & Affordability", id="tab-7-affordability", href="#", active="exact"), style=tabs_style),
        dbc.NavItem(dbc.NavLink("Food Losses & Waste", id="tab-8-losses", href="#", active="exact"), style=tabs_style),
        dbc.NavItem(dbc.NavLink("Food System Policies", id="tab-9-policies", href="#", active="exact"), style=tabs_style),
        dbc.NavItem(dbc.NavLink("Health & Nutrition", id="tab-10-nutrition", href="#", active="exact"), style=tabs_style),
        dbc.NavItem(dbc.NavLink("Environmental Footprints of Food & Diets", id="tab-11-footprints", href="#", active="exact"), style=tabs_style),
        dbc.NavItem(dbc.NavLink("Behaviour Change Tool (AI Chatbot & Game)", id="tab-12-behaviour", href="#", active="exact"), style=tabs_style),
    ], 
    vertical="md", 
    pills=True, 
    fill=True,
    style={"marginTop": "20px",
           "alignItems": "center",
           "textAlign": "center",
           "zIndex": 1000})

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
    "backgroundImage": "url('/assets/photos/urban_food_systems_6.jpg')",  
    "backgroundSize": "cover",        
    "backgroundPosition": "center",  
    "backgroundRepeat": "no-repeat",
})


# ========================== City Selector ==========================

def city_selector(selected_city='addis', visible=True):
    """
    City selector dropdown component.
    Must be included in all layouts for callbacks to work properly.
    Set visible=False to hide it on tab pages.
    """
    return html.Div([
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
                    {'label': '📍 Addis Ababa', 'value': 'addis'},
                    {'label': '📍 Hà Nội', 'value': 'hanoi'}
                ],
                value=selected_city,
                clearable=False,
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
        html.Img(src="/assets/logos/DeSIRA.png", style={'height': '60px', 'margin': '0 30px'}),
        html.Img(src="/assets/logos/IFAD.png", style={'height': '65px', 'margin': '0 30px'}),
        html.Img(src="/assets/logos/Rikolto.png", style={'height': '40px', 'margin': '0 30px'}),
        html.Img(src="/assets/logos/RyanInstitute.png", style={'height': '60px', 'margin': '0 30px'})
    ], style={
        "display": "flex",
        "justifyContent": "center",
        "alignItems": "baseline",
        "margin": "20px 0px",
    })
])
