import os
import numpy as np
import xarray as xr
import rioxarray as rxr
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import matplotlib.colors as colors
import seaborn as sns
import plotly.express as px
import json
#from lorem_text import lorem
import dash
from dash import Dash, html, dcc, Output, Input, State, callback, dash_table
import dash_bootstrap_components as dbc
import random
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
import plotly.graph_objects as go

import warnings
warnings.filterwarnings("ignore")

app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

#colors = {
#  'eco_green': '#AFC912',
#  'forest_green': '#4C7A2E',
#  'earth_brown': '#7B5E34',
#  'harvest_yellow': '#F2D16B',
#  'neutral_light': '#F5F5F5',
#  'dark_text': '#333333',
#  'accent_warm': '#E07A5F'
#}


green_gradient = [
    "#095d40",
    "#206044",
    "#3a6649",
    "#547d5b",
    "#6f946d",
    "#8aa97f",
    "#a5be91",
    "#b8d099",
    "#c1d88e",
    "#d1e7a8"
]

brand_colors = {    'Black':         '#333333',
                    "Brown":         "#313715",
                    "Red":           "#A80050",
                    "Dark green":    "#939f5c",
                    "Mid green":     "#bbce8a",
                    "Light green":   "#E8F0DA",
                    "White":         "#ffffff"  
}

greens_pie_palette = [
    brand_colors['Light green'],   # "#E8F0DA"
    brand_colors['Mid green'],     # "#bbce8a"
    brand_colors['Dark green'],    # "#939f5c"
    "#b7c49a",                     # lighter tint of Dark green
    "#d6e5b8",                     # lighter tint of Mid green
    "#e3f6d5",                     # very light green
    "#c1d88e",                     # soft khaki-green
    "#d1e7a8",                     # pastel green
    "#aabf7e",                     # olive green
    "#8aa97f",                     # muted green
]

reds_pie_palette = [
    "#a80050",   # main brand red
    "#84003d",   # deep accent red
    "#C97A9A",   # soft pink
    "#E07A5F",   # warm accent
    "#F2D16B",   # harvest yellow (for contrast)
    "#F5F5F5",   # neutral light
    "#7B5E34",   # earth brown
    "#C97A9A",   # repeat pink
    "#E07A5F",   # repeat accent
    "#F2D16B"    # repeat yellow
]

plotting_palette_cat = [
    "#a80050",  
    "#84003d",   
    "#F5F5F5",   
    '#E8F0DA',
    "#bbce8a",
    "#939f5c",
    "#E07A5F",   
    "#d33030",
]

tabs = [
        'Food Systems Stakeholders',                #Populated
        'Food Flows, Supply & Value Chains',        #Populated
        'Sustainability Metrics & Indicators',      #Currently empty
        'Multidimensional Poverty',                 #Populated
        'Resilience to Food System Shocks',         #In progress
        'Dietary Mapping & Affordability',          #Semi-Populated (In development)
        'Food Losses & Waste',                      #Currently empty
        'Food System Policies',                     #Currently empty
        'Health & Nutrition',                       #Populated
        'Environmental Footprints of Food & Diets', #Currently empty 
        'Behaviour Change Tool (AI Chatbot & Game)' #Currently empty (In development)
        ]


# -------------------------- Loading and Formatting All Data ------------------------- #

homepath = os.getcwd()

# Loading and Formatting MPI Data
path = homepath + "/assets/data/"
MPI = gpd.read_file(path+"Hanoi_districts_MPI.geojson")#.set_index('Dist_Name')
MPI['Normalized'] = MPI['Normalized'].astype(float)
MPI['Dist_Name'] = MPI['Dist_Name'].astype(str)
geojson = json.loads(MPI.to_json())

# Loading and Formatting MPI CSV Data=
df_mpi = pd.read_csv(path+"Hanoi_districts_MPI_long.csv")
variables = df_mpi['Variable'].unique()

# Loading and Formatting Food Systems Stakeholders Data
df_sh = pd.read_csv(path+"/hanoi_stakeholders.csv").dropna(how='any').astype(str)

# Format Website column as clickable markdown links
if 'Website' in df_sh.columns:
    df_sh['Website'] = df_sh['Website'].apply(
        lambda x: f'[Link Available]({x})' if x and x.startswith('http') else '--'
    )

# Pre-calculate fixed column widths (6px per character, min 80px, max 200px)
column_widths = {}
for col in df_sh.columns:
    max_len = max(len(str(col)), df_sh[col].astype(str).str.len().max())
    column_widths[col] = min(max(max_len * 6, 80), 200)

total_table_width = sum(column_widths.values())

# Loading supply flow data for Sankey Diagram
df_sankey = pd.read_csv(path+'/hanoi_supply.csv')

# Loading affordability data
df_affordability =  pd.read_csv(path+'/hanoi_affordability_cleaned.csv')

# Loading dietary data
df_diet = pd.read_csv(path+'/hanoi_health_nutrition_cleaned.csv')
df_diet_2 = pd.read_csv(path+'hanoi_health_nutrition_cleaned_2.csv')

# Custom styling 
tabs_style = {
                "backgroundColor": brand_colors['Mid green'],
                "color": brand_colors['Brown'],
                "width":"100%",
                "margin-bottom": "4px",
                "borderRadius": "8px",
                "padding": "6px 4px",
                "fontWeight": "bold",
                "textAlign": "left",
                "fontSize": "clamp(0.6em, 1vw, 1.1em)",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.08)",
                "border": "none",
                "textDecoration": "none",
                "whiteSpace": "normal",
                "box-sizing": "border-box",
                "maxWidth": "90%",
                "wordBreak": "normal"
            }

kpi_card_style ={"textAlign": "center", 
                "backgroundColor": brand_colors['White'], 
                "color":brand_colors['Brown'],
                "font-weight":"bold",
                "border-radius": "8px",
                "padding":"10px",
                "margin-bottom":"10px",
                "flexDirection": "column",
                "border": "2px solid " + brand_colors['White'],
                }

kpi_card_style_2 = {
                "textAlign": "center",
                "backgroundColor": brand_colors['White'],
                "borderRadius": "12px",
                "boxShadow": "0 4px 16px rgba(0,0,0,0.10)",
                "padding": "clamp(4px, 3vw, 12px)", 
                "padding":"6px",
                "marginBottom": "12px",
                "width": "100%",
                #"maxWidth": "350px",
                "height": "auto",
                #"minWidth": "220px"
            }

header_style = {"color": brand_colors['Brown'], 
                'fontWeight': 'bold',
                "margin": "0", 
                'textAlign': 'center',
                "fontSize": "clamp(0.8em, 3vw, 1.25em)",
                'whiteSpace': 'normal',
                }

card_style = {
    "backgroundColor": brand_colors['White'],
    "border-radius": "10px",
    "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
    "padding": "20px",  # Increase padding for consistency
    "margin-bottom": "15px"
}


# ----------------------- App Layout Components -------------------------- #

sidebar = dbc.Card([
    #html.Img(src="/assets/logos/temp_efs_logo.png", style={"width": "40%", "margin-bottom": "10px", "justifyContent": "center"}),
    dbc.Nav([
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
    #"backgroundColor": brand_colors['Light green'],
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
    "backgroundRepeat": "no-repeat" ,
})

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
   
# ------------------------- Main app layout ------------------------- #


def landing_page_layout():
    tab_labels = [
        "Food Systems Stakeholders", "Food Flows, Supply & Value Chains", "Sustainability Metrics / Indicators", "Multidimensional Poverty",
        "Labour, Skills & Green Jobs", "Resilience to Food System Shocks", "Dietary Mapping & Affordability", "Food Losses & Waste",
        "Food System Policies", "Health & Nutrition", "Environmental Footprints of Food & Diets", "Behaviour Change Tool (AI Chatbot & Game)"
    ]

    tab_ids = [
        "stakeholders", "supply", "sustainability", "poverty",
        "labour", "resilience", "affordability", "losses",
        "policies", "nutrition", "footprints", "behaviour"]

    white_tab_bg, grey_tab_bg = "rgba(255, 255, 255, 0.7)", "rgba(173, 181, 189, 0.7)"
    background_colours = {
        "stakeholders":white_tab_bg, 
        "supply":white_tab_bg,
        "sustainability":grey_tab_bg, 
        "poverty":white_tab_bg,
        "labour":grey_tab_bg,
        "resilience":grey_tab_bg, 
        "affordability":white_tab_bg, 
        "losses":grey_tab_bg,
        "policies":grey_tab_bg, 
        "nutrition":white_tab_bg, 
        "footprints":grey_tab_bg, 
        "behaviour":grey_tab_bg
    }
    
    # Create grid items
    grid_items = []
    for i, (tab_id, label) in enumerate(zip(tab_ids, tab_labels)):
        grid_items.append(
            dbc.Card([
                dbc.Button(label, id=f"tab-{i+1}-{tab_id}", color="light", 
                           className="dash-landing-btn",
                           style={
                                "width": "100%",
                                "height": "100%",
                                "fontWeight": "bold",
                                "fontSize": "clamp(1.25em, 1.3em, 2.25em)",
                                "color": brand_colors['Brown'],
                                "backgroundColor": background_colours[tab_id],
                                "borderRadius": "10px",
                                "boxShadow": "0 4px 8px rgba(0,0,0,0.08)",
                                "border": f"2px solid {brand_colors['White']}",
                                "whiteSpace": "normal",
                                "padding": "18px 8px",
                }), 
            ], style={
                "height": "25vh",
                "backgroundColor": "rgba(255, 255, 255, 0.5)",
                "borderRadius": "10px",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.08)",
                "margin": "10px"
            })
        )

    # Arrange grid items in 4 columns x 3 rows
    grid_layout = html.Div([
        dbc.Row([
            dbc.Col(grid_items[0], width=3),
            dbc.Col(grid_items[1], width=3),
            dbc.Col(grid_items[2], width=3),
            dbc.Col(grid_items[3], width=3),
        ], style={"marginBottom": "0"}),
        dbc.Row([
            dbc.Col(grid_items[4], width=3),
            dbc.Col(grid_items[5], width=3),
            dbc.Col(grid_items[6], width=3),
            dbc.Col(grid_items[7], width=3),
        ], style={"marginBottom": "0"}),
        dbc.Row([
            dbc.Col(grid_items[8], width=3),
            dbc.Col(grid_items[9], width=3),
            dbc.Col(grid_items[10], width=3),
            dbc.Col(grid_items[11], width=3),
        ], style={"marginBottom": "0"}),
    ], style={"width": "100%", "margin": "0 auto", "padding": "0 4px"})

    return html.Div([
        # Logo and Title
        html.Div([
                html.H1("EcoFoodSystems Dashboard", style={
                    "color": brand_colors['Brown'],
                    "fontWeight": "bold",
                    "fontSize": "2.75em",
                    "margin-bottom": "30px",
                }),

            #html.H3("Exploring Food Systems in Hanoi, Vietnam", style={
            #    "color": brand_colors['Dark green'],
            #    "fontWeight": "bold",
            #    "fontSize": "1.25em",
            #    "textAlign": "center",
            #    "marginBottom": "20px"
            #})

            html.P("EcoFoodSystems takes a food systems research approach to enable transitions towards diets that are more sustainable, healthier and affordable for consumers in city regions",
                style={
                    "color": brand_colors['Brown'],
                    "fontSize": "1em",
                    "textAlign": "center",
                    "maxWidth": "800px",
                    "margin-bottom": "30px",
                }
            ),

        ], style={
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
            "paddingTop": "40px",
        }),

        # Tab Grid
        html.Div([grid_layout], style={ "width": "100%", 
                                        "height":"auto",
                                        "display": "block",
                                        "marginTop": "auto",
                                        "backgroundImage": "url('/assets/photos/hanoi_header.png')",  # <-- Path to your image
                                        "backgroundSize": "cover",        # Image covers the whole area
                                        "backgroundPosition": "center",   # Center the image
                                        "backgroundRepeat": "no-repeat"   # Don't repeat the image
                                            }),

        # Footer logos (optional)
        footer

    ], style={
        "backgroundColor": brand_colors['Light green'],
        "height": "100vh",
        "width": "100vw",
        "padding": "0",
        "margin": "0",
        "boxSizing": "border-box",
        'overflowY':'auto'
    })


#------------------------- App Layout ----------------------- #

app.layout = html.Div([

                    html.Div(id="tab-content", children=landing_page_layout(), style={"width": "100%",
                                                                                            "height": "100%"})

                    # Parent container for full page
                    ], style={
                        "display": "flex",
                        "flexDirection": "column",
                        "height": "100vh",
                        "width": "100vw"
            })


# ------------------------- Defining tab layouts ------------------------- #

def stakeholders_tab_layout():
    # Render the stakeholders database as a full-page interactive table (matching Addis layout)
    return html.Div([
        html.Div([sidebar], style={
            "width": "15%",
            "height": "100%",
            "display": "flex",
            "vertical-align": 'top',
            "flexDirection": "column",
            "justifyContent": "flex-start",
        }),

        # Main content: full-page DataTable for stakeholders
        html.Div([
            dbc.Card([
                dbc.CardBody([
                    dash_table.DataTable(
                        id='sh_table',
                        data=df_sh.to_dict('records'),
                        columns=[
                            {"name": str(i), "id": str(i), "presentation": "markdown"} if i == "Website" else {"name": str(i), "id": str(i)}
                            for i in df_sh.columns
                        ],
                        page_size=20,
                        page_action='native',
                        filter_action='native',
                        sort_action='native',
                        sort_mode='multi',
                        style_cell={
                            'textAlign': 'left',
                            'padding': '2px 6px',                     
                            'whiteSpace': 'nowrap',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                            'fontSize': 'clamp(0.64em, 0.85vw, 0.9em)',
                            'lineHeight': '1.1',                       
                            'minWidth': '120px',
                            'maxWidth': '320px',
                            'height': '36px'                          
                        },
                        style_header={
                            'fontWeight': 'bold',
                            'backgroundColor': brand_colors['Red'],
                            'color': 'white',
                            'textAlign': 'center',
                            'fontSize': 'clamp(0.8em, 1vw, 1.1em)'
                        },
                        style_data_conditional=[
                            {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'}
                        ],
                        # Provide hover tooltips for long text columns (e.g. description)
                        tooltip_data=[
                            {
                                col: {
                                    'value': str(row[col]) if (col.lower() == 'description' or len(str(row[col])) > 60) else '',
                                    'type': 'text'
                                }
                                for col in df_sh.columns
                            } for row in df_sh.to_dict('records')
                        ],
                        tooltip_duration=4000,
                        css=[{
                            'selector': '.dash-table-tooltip',
                            'rule': 'position: fixed !important; background-color: ' + brand_colors['Light green'] + '; color: ' + brand_colors['Black'] + '; border: 2px solid ' + brand_colors['Dark green'] + '; padding: 6px; font-size: 14px; box-shadow: 0 4px 8px ' + brand_colors['Black'] + ';'
                        }],
                        style_table={
                            'overflowX': 'auto',
                            'width': '100%',
                            'height': '100%',
                            'overflowY': 'auto'
                        }
                    )
                ], style={"height": "100%", "display": "flex", "flexDirection": "column"})
            ], style={"height": "90%", "padding": "10px", "box-shadow": "0 2px 6px rgba(0,0,0,0.1)", "backgroundColor": brand_colors['White'], "border-radius": "10px"}),
        ], style={
            "flex": "1 1 85%",
            "height": "100%",
            "display": "flex",
            "overflow": "auto",
            "border-radius": "10px",
            "margin": "10px 10px 10px 10px"
        })

    ], style={
        "display": "flex",
        "width": "100%",
        "height": "100%",
        "backgroundColor": brand_colors['Light green']
    })


def supply_tab_layout():
    return html.Div([

            html.Div([sidebar], style={
                                "width": "15%",
                                "height": "100%",
                                "display": "flex",
                                "vertical-align":'top',
                                "flexDirection": "column",
                                "justifyContent": "flex-start"}), # End of sidebar div

            # Left Panel
            html.Div([
                dbc.Card([
                    dbc.CardBody([
                        html.H2('Rice Flow Estimations', 
                                style=header_style),
                    ])
                ], style={"height": "auto",
                          "width":"100%",
                          "padding":"1px" ,
                          "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                          "backgroundColor": brand_colors['Mid green'],
                          "border-radius": "10px",
                          'margin':"0px 0px 10px 0px",
                          "justifyContent": "center"
                                  }),


                dbc.Card([
                    dbc.CardBody([
                        html.H5("Total Flow", className="card-title", style={
                                                                            "fontWeight": "normal",
                                                                            "fontSize": "clamp(0.6em, 0.8em, 1.2em)",
                                                                            "color": brand_colors['Brown'],
                                                                            "marginBottom": "4px"
                                                                        }),
                        html.H1(id="kpi-total-flow", className="card-text", style={
                                                                                "fontWeight": "bold",
                                                                                "fontSize": "clamp(1.2em, 2em, 2.8em)",
                                                                                "color": brand_colors['Red'],
                                                                                "margin": "0"
                                                                        }),
                        html.H5("tons", style={
                                                    "fontSize": "clamp(0.6em, 0.8em, 1em)",
                                                    "color": brand_colors['Brown'],
                                                    "marginTop": "4px",
                                                    "fontWeight": "normal",
                                                })
                                ])
                            ], style={**kpi_card_style_2}),

                dbc.Card([
                    dbc.CardBody([
                        html.H5("Urban Share", className="card-title", style={
                                                                                "fontWeight": "normal",
                                                                                "fontSize": "clamp(0.6em, 0.8em, 1.2em)",
                                                                                "color": brand_colors['Brown'],
                                                                                "marginBottom": "10px"
                                                                            }),



                        dcc.Graph(id="urban-indicator", style={"height": "clamp(80px, 10vh, 200px)"}, config={"displayModeBar": False})
                                ])
                ], style={**kpi_card_style_2}),

            ], style={
                #"flex": "0 0 30%",  # Changed: Narrow left column for KPI cards
                "width":"80%",
                "height": "100%",
                "display": "flex",
                "flexDirection": "column",
                "padding": "10px",
                "margin-left":"20px",
                "alignItems": "center",
                "marginBottom": "auto" 
            }),

            # Sankey + Slider + Footnote (right)
            html.Div([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            dcc.Loading(
                                type="circle",
                                children=dcc.Graph(
                                    id="sankey-graph", 
                                    style={"width": "100%", "height":"70vh"}  
                                )
                            ),
                        ], style={"width": "100%"}),

                        # Info button (positioned absolute in top right)
                        html.Div([
                            dbc.Button("ⓘ", id="sankey-info-btn", style={
                                "fontSize": "1.5em",
                                "color": brand_colors['Red'],
                                "background": "none",
                                "border": "none",
                                "padding": "0",
                                "cursor": "pointer"
                            }),
                            dbc.Tooltip(
                                "Data Source: General Statistics Office of Vietnam (GSO). 2025. Production of paddy by province. Consulted on: June 2025. Link: https://www.nso.gov.vn/en/agriculture-forestry-and-fishery/. Estimation method: Trade attractiveness method, including two steps as follows: A) Estimation of Rice Net Supply (Consumption – Production) for every province, based on Consumption (Population * Consumption per person), and Production (Paddy production/Live weight/Raw production * Conversion rate). B) Distribute the rice consumption of Hanoi, considering: Province Production, National Production, and International Import.",
                                target="sankey-info-btn",
                                placement="bottom",
                                style={"fontSize": "0.5em", "maxWidth": "500px"}
                            )
                        ], style={
                            "position": "absolute",
                            "top": "12px",
                            "right": "18px",
                            "zIndex": 10
                        }),

                        html.Div([dcc.Slider(
                            id='slider', min=2010, max=2022, value=2022, step=2,
                            marks={year: str(year) for year in range(2010,2023,2)},
                            tooltip={"placement": "bottom", "always_visible": True},
                            updatemode='mouseup'
                            )
                        ], style={"margin-top":"10px", 
                                       "color":brand_colors['Brown'],
                                       "width": "100%", 
                                       "height":"10%"}),

                    ],style={"display": "flex", "flexDirection": "column", "height": "100%"})
                ],style={**card_style, "height": "90vh", "width":"60vw"}),

            ], style={
                "flex": "1 1 60%",  
                "height": "calc(100vh - 20px)",
                "display": "flex",
                "flexDirection": "column",
                "padding": "10px",
                "margin":"0",
                "backgroundColor": brand_colors['Light green'],
                "marginBottom": "auto" 
            }),
        ], style={
                    "display": "flex", 
                    "width": "100%", 
                    "height": "100%",
                    "backgroundColor": brand_colors['Light green']
        })



def poverty_tab_layout():
    return html.Div([
        html.Div([sidebar], style={
                                        "width": "15%",
                                        "height": "100%",
                                        "display": "flex",
                                        "vertical-align":'top',
                                        "flexDirection": "column",
                                        "justifyContent": "flex-start",}), # End of sidebar div
        html.Div([
        dbc.Card([
                dbc.CardBody([
                    html.H2("Multidimensional Poverty Index", style=header_style),
                    html.P("The Multidimensional Poverty Index (MPI) assesses poverty across health, education, and living standards using ten indicators including nutrition, schooling, sanitation, water, electricity, and housing. This spatial analysis maps deprivation levels across Hanoi's districts, revealing where households face multiple overlapping disadvantages. These insights identify priority areas for targeted interventions, supporting equitable resource allocation and sustainable poverty reduction strategies aligned with SDG goals.",
                            style={  "margin": "10px 6px", 
                                    "fontSize": 'clamp(0.7em, 1em, 1.0em)',
                                    "textAlign": "justify",
                                    "whiteSpace": "normal",
                                    })
                            ])
                    ], style={  "height": "auto", 
                                "padding":"6px" ,
                                "margin-bottom": "5px",
                                "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                                "backgroundColor": brand_colors['White'],
                                "border-radius": "10px"}),

        html.Div([
            dbc.Card([
                dbc.CardBody([
                    dcc.Dropdown(
                        id='variable-dropdown',
                        options=[{'label': v, 'value': v} for v in variables],
                    value=variables[0],
                    style={"margin-bottom": "20px"}),

                    dcc.Graph(id='bar-plot',
                            style={
                            "flex": "1 1 auto",
                            "height":"98%",
                            'padding': '4px',
                            'margin': '8px',
                            "border-radius": "8px",
                            "box-shadow": "0 2px 8px rgba(0,0,0,0.15)",
                            })
                            ],style={
                                        "display": "flex",
                                        "flexDirection": "column",
                                        "height": "100%"             
                                    })
                    ], style={"height": "100%", 
                                "padding":"6px" ,
                                "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                                "backgroundColor": brand_colors['White'],
                                "border-radius": "10px"}),

                    ], style={
                        "height": "100%",
                        "backgroundColor": brand_colors['Light green'],
                        "border-radius": "0",
                        "margin": "0",
                        "display": "flex",
                        "flexDirection": "column",
                        "justifyContent": "flex-start",

                        "box-sizing": "border-box",
                        "zIndex": 2,
                        "position": "relative",
                    }),
                    ],style={
        "overflowY": "auto",
        "display": "flex",
        "flexDirection": "column",
        "width": "min(40%)",
        "height": "100%",
        "padding": "10px",
        "backgroundColor": brand_colors['Light green']
        }),

        # Right panel: map, full height
        html.Div([
            dcc.Graph(
                id='map',
                style={"height": "100%",
                       "width": "100%",  # fill the parent div
                       "padding": "0",
                       "margin": "0"})
        ], style={
            "flex": "1",
            "height": "100%",
            "padding": "0",
            "margin": "0",
            "backgroundColor": brand_colors['White'],
            "border-radius": "0",
            "display": "flex",
            "alignItems": "stretch",
            "justifyContent": "center",
            "box-sizing": "border-box",
            "zIndex": 1000,
            "position": "relative",
        })

    ], style={
        "display": "flex",
        "width": "100vw",
        "height": "100%"
    })


def affordability_tab_layout():
    return html.Div([
            html.Div([sidebar], style={
                                "width": "15%",
                                "height": "100%",
                                "display": "flex",
                                "vertical-align":'top',
                                "flexDirection": "column",
                                "justifyContent": "flex-start",
            }), # End of sidebar div

            # Left Panel
            html.Div([
                dbc.Card([
                    dbc.CardBody([
                        html.H2('Dietry Mapping & Affordability', 
                                style=header_style),
                    ])
                ], style={"height": "auto",
                          "width":"100%",
                          "padding":"1px" ,
                          "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                          "backgroundColor": brand_colors['Mid green'],
                          "border-radius": "10px",
                          'margin':"0px 0px 10px 0px",
                          "justifyContent": "center"
                }),
                
                html.Div([
                    dbc.Card([
                        dbc.CardBody([         
                            dcc.Dropdown(
                                id='affordability-filter-dropdown',
                                options=[
                                    {'label': 'Food Expenditure from Total Expenses', 'value': 'foodExp_totalExp'},
                                    {'label': 'Food Expenditure from Household Income', 'value': 'foodExp_totalInc'},
                                    {'label': 'Rice Expenditure from Household Income', 'value': 'riceExp_House'},
                                    {'label': 'Rice Affordability', 'value': 'riceAfford'},
                                ],
                                value='riceAfford',
                                clearable=False,
                                style={"margin-bottom": "0", 
                                        'fontSize': 'clamp(0.8em, 1em, 1.4em)',
                                        'width':'100%'
                            })
                        ], style={  "display":'flex',
                                    "flexDirection":'column',
                                    'width':'100%'
                        })
                    ])
                ], style={  "height": "auto", 
                            "padding":"2px" ,
                            "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                            'margin-bottom': '15px',
                            "backgroundColor": brand_colors['White'],
                            "border-radius": "10px"
            }),

                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id='affordability-trend', 
                                style={
                                    "flex": "1 1 auto",
                                    "height":"98%",
                                    'padding': '4px',
                                    'margin': '0',
                                    "border-radius": "8px",
                                    "box-shadow": "0 2px 8px rgba(0,0,0,0.15)",
                                })
                    ],style={
                            "display": "flex",
                            "flexDirection": "column",
                            "height": "100%"             
                    })
                ], style={"height": "100%", 
                            "padding":"2px" ,
                            "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                            "backgroundColor": brand_colors['White'],
                            "border-radius": "10px"
                })

            ], style={
                    "width": "min(50%)",
                    "height": "100%",
                    "padding": "10px",
                    "backgroundColor": brand_colors['Light green'],
                    "border-radius": "0",
                    "margin": "0",
                    "box-shadow": "0 2px 8px rgba(0,0,0,0.05)",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "flex-start",
                    "overflowY": "auto",
                    "box-sizing": "border-box",
                    "position": "relative",
                }), # End of left panel


        ], style={
                    "display": "flex", 
                    "width": "100%", 
                    "height": "100%",
                    "backgroundColor": brand_colors['Light green']
        })

def diet_nutrition_layout():
    labels = df_diet_2['Cat'].unique()
    return html.Div([
                # sidebar container
                html.Div([sidebar], style={
                        "width": "15%",
                        "height": "100%",
                        "display": "flex",
                        "vertical-align":'top',
                        "flexDirection": "column",
                        "justifyContent": "flex-start",}), # End of sidebar div


                # Left panel container
                html.Div([
                    dbc.Card([
                        dbc.CardBody([
                            html.H2('Health & Nutrition', 
                                    style=header_style),
                        ])
                    ], style={"height": "auto",
                            "width":"100%",
                            "padding":"1px" ,
                            "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                            "backgroundColor": brand_colors['Mid green'],
                            "border-radius": "10px",
                            'margin':"0px 0px 10px 0px",
                            "justifyContent": "center"
                    }),

                    html.Div([
                        dbc.Card([
                            dbc.CardBody([
                                dcc.Dropdown(
                                    id='health-filter-dropdown',
                                    options=[
                                        {'label': labels[i], 'value': labels[i]} for i in range(len(labels))
                                    ],
                                    value=labels[0],
                                    clearable=False,
                                    style={"margin-bottom": "0", 
                                            'fontSize': 'clamp(0.8em, 1em, 1.4em)',
                                            'width':'100%'
                                })
                            ], style={  "display":'flex',
                                                "flexDirection":'column',
                                                'width':'100%'
                            })
                        ])
                    ], style={  "height": "auto", 
                                "padding":"2px" ,
                                "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                                'margin-bottom': '15px',
                                "backgroundColor": brand_colors['White'],
                                "border-radius": "10px"
                    }),

                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(id='health-trend', 
                                    style={
                                        "flex": "1 1 auto",
                                        "height":"98%",
                                        'padding': '4px',
                                        'margin': '0',
                                        "border-radius": "8px",
                                        "box-shadow": "0 2px 8px rgba(0,0,0,0.15)",
                                    })
                        ],style={
                            "display": "flex",
                            "flexDirection": "column",
                            "height": "100%"             
                        })
                    ], style={"height": "100%", 
                                "padding":"2px" ,
                                "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                                "backgroundColor": brand_colors['White'],
                                "border-radius": "10px"
                    })

                ], style={
                            "width": "min(35%)",
                            "height": "100%",
                            "padding": "10px",
                            "backgroundColor": brand_colors['Light green'],
                            "border-radius": "0",
                            "margin": "0",
                            "box-shadow": "0 2px 8px rgba(0,0,0,0.05)",
                            "display": "flex",
                            "flexDirection": "column",
                            "justifyContent": "flex-start",
                            "overflowY": "auto",
                            "box-sizing": "border-box",
                            "position": "relative",
                }), # End of left panel

                # Right panel container
                html.Div([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(id='diet-dumbell', style={
                            "flex": "1 1 90vh",
                            "height":"82vh",
                            'padding': '2px',
                            'margin': '0',
                            "border-radius": "8px",
                            "box-shadow": "0 2px 8px rgba(0,0,0,0.15)",
                            }),

                            html.Div([dcc.Slider(
                                                    id='dumbell-slider', min=2010, max=2023, value=2013, step=2,
                                                    marks={year: str(year) for year in range(2010,2023,1)},
                                                    tooltip={"placement": "bottom", "always_visible": True},
                                                    updatemode='mouseup'
                                                    )
                                                ], style={  "margin-top":"8px", 
                                                            "color":brand_colors['Brown'],
                                                            "width": "100%", 
                                                            "height":"auto",
                                                            "flex": "0 0 auto",
                                                            'marginBottom': '4px'
                                                        })
                        ], style={
                                "display": "flex",
                                "flexDirection": "column",
                                "height": "100%",
                                "justifyContent": "flex-start"
                            })
                    ])
                ], style={
                    "width": "min(50%)",
                    "height": "100%",
                    "padding": "10px",
                    "backgroundColor": brand_colors['Light green'],
                    "border-radius": "0",
                    "margin": "0",
                    "box-shadow": "0 2px 8px rgba(0,0,0,0.05)",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "flex-start",
                    "overflowY": "auto",
                    "box-sizing": "border-box",
                    "position": "relative",
                })
    
            ], style={
                    "display": "flex", 
                    "width": "100%", 
                    "height": "100%",
                    "backgroundColor": brand_colors['Light green']
        })

# ------------------------- Callbacks ------------------------- #

# Linking the dropdown to the bar chart for the MPI page    
@app.callback(
    Output('bar-plot', 'figure'),
    Input('variable-dropdown', 'value')
)
def update_bar(selected_variable):
    # Sort by selected variable, descending
    filtered_df = df_mpi[df_mpi["Variable"]==selected_variable]
    sorted_df = filtered_df.sort_values('Value', ascending=False)
    fig = px.bar(
        sorted_df,
        x='Value',
        y='Dist_Name',
        orientation='h',
        hover_data=['Dist_Name'],
        labels={'Dist_Name': "District",
                'Value':"Percentage of Deprived Households"},
        color_discrete_sequence=[brand_colors['Red']]
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'},
                      height=25 * len(sorted_df),
                      margin=dict(l=0.15, r=0.1, t=0.15, b=0.3),
                      hoverlabel=dict(
                        bgcolor="white",      # Tooltip background color
                        font_color="black",   # Tooltip text color
    ))

    return fig

# Adding MPI map and linking it to the bar chart via click
@app.callback(
    Output('map', 'figure'),
    Input('bar-plot', 'clickData'),
    Input('variable-dropdown', 'value')
)
def update_map_on_bar_click(clickData, selected_variable):
    center = {
        "lat": MPI.geometry.centroid.y.mean(),
        "lon": MPI.geometry.centroid.x.mean()
    }
    zoom = 7.75

    MPI_display = MPI.copy()
    MPI_display['opacity'] = 0.7
    MPI_display['line_width'] = 0.8

    # If a bar is clicked, zoom to that district
    if clickData and 'points' in clickData:
        selected_dist = clickData['points'][0]['y']  # y is Dist_Name for horizontal bar
        match = MPI[MPI['Dist_Name'] == selected_dist]
        if not match.empty:
            #centroid = match.geometry.centroid
            center = {
                "lat": match.geometry.centroid.y.values[0],
                "lon": match.geometry.centroid.x.values[0]
            }
            #area = match.geometry.area.values[0]
            #zoom = max(8, min(12, 12 - area * 150))  # Zoom in closer
            # Highlight: set opacity and line_width for the selected district

            zoom = 10
            MPI_display.loc[MPI_display['Dist_Name'] == selected_dist, 'opacity'] = 1
            MPI_display.loc[MPI_display['Dist_Name'] == selected_dist, 'line_width'] = 2


    fig = px.choropleth_mapbox(
        MPI,
        geojson=geojson,
        locations="Dist_Name",
        featureidkey="properties.Dist_Name",
        color='Normalized',
        color_continuous_scale="Reds",
        opacity=0.7,
        range_color=(0, 1),
        labels={'Normalized':'MPI','Dist_Name':'District Name'},
        mapbox_style="carto-positron",
        zoom=zoom,
        center=center
    )

    
    fig.update_layout(coloraxis_colorbar=None)
    fig.update_coloraxes(showscale=False)

    fig.update_layout(
    paper_bgcolor=brand_colors['White'],
    plot_bgcolor=brand_colors['White'],
    margin=dict(l=0, r=0, t=0, b=0)
    )

    # Update per-feature opacity and line width upon click to highlight 
    fig.update_traces(
        marker=dict(
            opacity=MPI_display['opacity'],
            line=dict(width=MPI_display['line_width'], color='black')
        )
    )

    return fig

# Stakeholders table callback removed - now using native DataTable filtering
    
# Update Sankey based on timeslider

@app.callback(
    [Output("kpi-total-flow", "children"),
    #Output("kpi-urban-share", "children"),
     Output("urban-indicator", "figure"),
     Output("sankey-graph", "figure")],
    Input("slider", "value"),
    prevent_initial_call=False)

def update_sankey(value):
    df_sankey_filt = df_sankey[df_sankey['Year']==int(value)]
    flow1 = df_sankey_filt[['province', 'Target', 'Supply to Hanoi']].rename(
        columns={'province':'source', 'Target':'target', 'Supply to Hanoi':'supply'})

    flow2 = df_sankey_filt[['Target', 'Target_1', 'Rice supply']].rename(
        columns={'Target':'source', 'Target_1':'target', 'Rice supply':'supply'})

    df_sankey_final = pd.concat([flow1.drop_duplicates(), flow2.groupby(['source','target']).sum().reset_index()], ignore_index=True)
    labels = list(pd.unique(df_sankey_final[['source','target']].values.ravel('K')))

    # Map sources and targets to indices
    source_indices = df_sankey_final['source'].apply(lambda x: labels.index(x))
    target_indices = df_sankey_final['target'].apply(lambda x: labels.index(x))
    weights = df_sankey_final['supply']

    node_colors = [brand_colors['Red'] for l in labels]
    link_colors = ["rgba(209, 231, 168, 0.5)" for link in df_sankey_final['source']]


    # Calculating KPIs 
    total_flow = flow1.drop_duplicates()["supply"].sum()
    total_flow_text = f"{total_flow:,.0f}"

    total = flow2.groupby(['source','target']).sum().reset_index()['supply'].sum()
    urban_only = flow2.groupby(['source','target']).sum().reset_index().set_index('target').loc['Hanoi urban'].values[1]
    urban_share = urban_only/total *100
    urban_share_text = f"{urban_share:.1f}%"

    fig = go.Figure(go.Sankey(
        node=dict(label=labels, color=node_colors, pad=15, thickness=20),
        link=dict(source=source_indices, target=target_indices, value=weights, color=link_colors, 
                  hovertemplate='From %{source.label} → %{target.label}<br>Flow: %{value}<extra></extra>')
    ))

    fig.update_layout(
        hovermode='x',
        font=dict(size=12, color='black'),
        paper_bgcolor=brand_colors['White'],
        plot_bgcolor=brand_colors['White'],
        margin=dict(l=10, r=10, t=20, b=20), 
        width=None)

    urban_fig = go.Figure(go.Pie(
        values=[urban_share, 100-urban_share],
        hole=0.6,
        marker=dict(colors=[brand_colors['Red'], brand_colors['Light green']]),
        textinfo="none",
        labels=["Urban", "Rural"],  # Add labels for clarity
        hoverinfo="label+percent",  # Show label, percent, and value on hover
        hovertext=[f"Urban: {urban_share:.1f}%", f"Rural: {100-urban_share:.1f}%"]  # Custom hover text
    ))
    
    urban_fig.update_layout(showlegend=False, margin=dict(l=0,r=0,t=0,b=0.1),
                            paper_bgcolor="rgba(0,0,0,0)",  
                            plot_bgcolor="rgba(0,0,0,0)")


    return total_flow_text, urban_fig, fig


@app.callback(
    Output('affordability-trend','figure'),
    Input('affordability-filter-dropdown','value')
)

def update_affordability_trend(selected_variable):

    titles = {
        'foodExp_totalExp': 'Food Expenditure from Total Expenses (%)',
        'foodExp_totalInc': 'Food Expenditure from Household Income (%)',
        'riceExp_House': 'Rice Expenditure from Household Income (%)',
        'riceAfford': 'Rice Affordability'
    }

    y_labels = {
        'foodExp_totalExp': '%',
        'foodExp_totalInc': '%',
        'riceExp_House': '%',
        'riceAfford': '%'
    }

    df_filt = df_affordability[df_affordability['Cat']==selected_variable]

    fig = px.line(df_filt, 
                  x='Year', 
                  y='value', 
                  color='Reg', 
                  markers=True,
                  labels={selected_variable: selected_variable.replace('_',' ').title(), 'Year':'Year'},
                  color_discrete_sequence=[brand_colors['Red'], brand_colors['Dark green']],
                  #title=titles[selected_variable]
                  )
    
    fig.update_traces(marker=dict(size=8))
    fig.update_layout(
        margin=dict(l=0.25, r=0, t=0, b=0.25),
        hoverlabel=dict(bgcolor="white", font_color="black"),
        legend=dict(
            title=None,
            x=1.1, y=1.1,
            xanchor='right', yanchor='top',
            bgcolor='rgba(255,255,255,0.7)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1,
            font=dict(size=12)
        )
    )
    fig.update_xaxes(title_text=None)  
    fig.update_yaxes(title_text=y_labels[selected_variable]) #titles[selected_variable])  
    return fig


@app.callback(
    Output('health-trend','figure'),
    Input('health-filter-dropdown','value')
)

def update_health_trend(selected_variable):
    df_filt = df_diet_2[df_diet_2['Cat']==selected_variable]

    fig = px.line(df_filt, 
                  x='Year', 
                  y='value', 
                  color='Reg', 
                  markers=True,
                  labels={selected_variable: selected_variable, 'Year':'Year'},
                  color_discrete_sequence=[brand_colors['Red'], brand_colors['Dark green']],
                  #title=titles[selected_variable]
                  )
    
    fig.update_traces(marker=dict(size=8))
    fig.update_layout(
        margin=dict(l=0.25, r=0, t=0, b=0.25),
        hoverlabel=dict(bgcolor="white", font_color="black"),
        legend=dict(
            title=None,
            x=1.1, y=1.1,
            xanchor='right', yanchor='top',
            bgcolor='rgba(255,255,255,0.7)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1,
            font=dict(size=12)
        )
    )

    fig.update_xaxes(title_text=None)  
    fig.update_yaxes(title_text=selected_variable) #titles[selected_variable])  
    return fig


@app.callback(Output('diet-dumbell', 'figure'),
              Input('dumbell-slider', 'value'))

def update_diet_dumbell(year_start):
    categories = df_diet['Cat'].unique()
  
    line_x, line_y, x_2013, x_2023, y_labels = [], [], [], [], []

    for cat in categories:
        val_2013 = df_diet.loc[(df_diet.Year == year_start) & (df_diet.Cat == cat), "value"].values[0]
        val_2023 = df_diet.loc[(df_diet.Year == 2023) & (df_diet.Cat == cat), "value"].values[0]
        line_x.extend([val_2013, val_2023, None])
        line_y.extend([cat, cat, None])
        x_2013.append(val_2013)
        x_2023.append(val_2023)
        y_labels.append(cat)

    fig = go.Figure()

    # Line connecting 2013 and 2023
    fig.add_trace(go.Scatter(
        x=line_x,
        y=line_y,
        mode="lines",
        line=dict(color="grey"),
        showlegend=False
    ))

    # 2013 markers
    fig.add_trace(go.Scatter(
        x=x_2013,
        y=y_labels,
        mode="markers",
        name=str(year_start),
        marker=dict(
                    color=brand_colors['Red'],
                    size=8,
                    symbol="circle",
                    line=dict(
                        color=brand_colors['Brown'],  # outline color
                        width=2                      # outline thickness
                    )
                )
    ))

    # 2023 markers
    fig.add_trace(go.Scatter(
        x=x_2023,
        y=y_labels,
        mode="markers",
        name="2023",
        marker=dict(
                    color=brand_colors['Light green'],
                    size=8,
                    symbol="circle",
                    line=dict(
                        color=brand_colors['Brown'],  # outline color
                        width=2                      # outline thickness
                    )
                )
    ))

    # Optional: Add arrows as annotations for direction
    for x0, x1, y in zip(x_2013, x_2023, y_labels):
        if pd.notnull(x0) and pd.notnull(x1):
            fig.add_annotation(
                x=x1, y=y,
                ax=x0, ay=y,
                xref="x", yref="y",
                axref="x", ayref="y",
                showarrow=True,
                arrowhead=3,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor=brand_colors['Brown'],
            )

    fig.update_layout(
    yaxis=dict(
        tickfont=dict(size=12),
        automargin=True,
        ticklabelposition="outside right",
        showgrid=True,                # Show horizontal grid lines
        gridcolor='#949494',  
        gridwidth=0.7                  
    ),
    xaxis=dict(
        showgrid=True,               
        gridcolor="#949494",
        gridwidth=0.7
    ),
    margin=dict(l=120, r=20, t=40, b=20),
    paper_bgcolor=brand_colors['White'],
    plot_bgcolor=brand_colors['White'],
    #title_text="Health and Nutrition trends from selected year to 2023", 
    #title_x=0.5
    )

    return fig

# Linking the tabs to page content loading 
@app.callback(
    Output("tab-content", "children"),
    [
        Input("tab-1-stakeholders", "n_clicks"),
        Input("tab-2-supply", "n_clicks"),
        Input("tab-3-sustainability", "n_clicks"),
        Input("tab-4-poverty", "n_clicks"),
        Input("tab-5-labour", "n_clicks"),
        Input("tab-6-resilience", "n_clicks"),
        Input("tab-7-affordability", "n_clicks"),
        Input("tab-8-losses", "n_clicks"),
        Input("tab-9-policies", "n_clicks"),
        Input("tab-10-nutrition", "n_clicks"),
        Input("tab-11-footprints", "n_clicks"),
        Input("tab-12-behaviour", "n_clicks"),
    ]
)
def render_tab_content(n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12):
    ctx = dash.callback_context
    if not ctx.triggered:
        return landing_page_layout()
    tab_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if tab_id == "tab-1-stakeholders":
        return stakeholders_tab_layout()
    
    elif tab_id == "tab-2-supply":
        return supply_tab_layout()
    
    elif tab_id == "tab-4-poverty":
        return poverty_tab_layout()
    
    elif tab_id == "tab-7-affordability":
        return affordability_tab_layout()

    elif tab_id == "tab-10-nutrition":
        return diet_nutrition_layout()

    else:
        return html.Div([html.H2("Coming soon...")])


if __name__ == '__main__':
    app.run(debug=True, port=8051)
