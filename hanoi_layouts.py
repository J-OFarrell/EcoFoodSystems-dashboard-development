"""
Hà Nội dashboard tab layouts
"""
import json
import os

import numpy as np
import pandas as pd
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import json

from config import brand_colors, header_style, kpi_card_style_2, card_style
from shared_components import sidebar_hanoi as sidebar, city_selector
from dashboard_components import create_nutrition_kpi_card, create_nutrition_kpi_card_hanoi


def _red_graph_loading(children, loading_id=None):
    return dcc.Loading(
        id=loading_id,
        parent_style={"height": "100%", "width": "100%", "position": "relative"},
        style={"height": "100%", "width": "100%"},
        custom_spinner=html.Div(
            dbc.Spinner(color="danger", type="border"),
            style={
                "position": "absolute",
                "inset": "0",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "zIndex": 1000,
                "pointerEvents": "none",
            }
        ),
        children=children,
    )


def hanoi_stakeholders_tab_layout():
    """Hà Nội stakeholders tab layout"""
    import app as main
    df_sh_hanoi = main.df_sh_hanoi
    
    return html.Div([
        city_selector(selected_city='hanoi', visible=False),  # Hidden but present for callback
        
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
                dbc.CardHeader(html.H3("Food System Stakeholder Database", style=header_style)),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='sh_table_hanoi',
                        data=df_sh_hanoi.to_dict('records'),
                        columns=[
                            {"name": str(i), "id": str(i), "presentation": "markdown"} if i == "Website" else {"name": str(i), "id": str(i)}
                            for i in df_sh_hanoi.columns
                        ],
                        page_size=14,
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
                        tooltip_data=[
                            {
                                col: {
                                    'value': str(row[col]) if (col.lower() in ['Abstract', 'Title', 'Keywords'] or len(str(row[col])) > 20) else '',
                                    'type': 'text'
                                }
                                for col in df_sh_hanoi.columns
                            } for row in df_sh_hanoi.to_dict('records')
                        ],
                        tooltip_duration=4000,
                        css=[
                            {
                                'selector': '.dash-table-tooltip',
                                'rule': 'position: fixed !important; background-color: ' + brand_colors['Light green'] + '; color: ' + brand_colors['Black'] + '; border: 2px solid ' + brand_colors['Dark green'] + '; padding: 6px; font-size: 14px; box-shadow: 0 4px 8px ' + brand_colors['Black'] + ';'
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container',
                                'rule': 'overflow-x: scroll !important; scrollbar-width: auto;'
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container::-webkit-scrollbar',
                                'rule': 'height: 14px; width: 14px; -webkit-appearance: none;'
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container::-webkit-scrollbar-track',
                                'rule': 'background: #f0f0f0; border-radius: 8px;'
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container::-webkit-scrollbar-thumb',
                                'rule': 'background: ' + brand_colors['Dark green'] + '; border-radius: 8px; border: 2px solid #f0f0f0;'
                            }
                        ],
                        style_table={
                            'overflowX': 'scroll',
                            'width': '100%',
                            'height': '100%',
                            'overflowY': 'auto'
                        }
                    ,
                        style_as_list_view=True
                    )
                ], style={"flex": "1", "display": "flex", "flexDirection": "column", "minHeight": "0"})
            ], style={"height": "100%", "padding": "10px", "box-shadow": "0 2px 6px rgba(0,0,0,0.1)", "backgroundColor": brand_colors['White'], "border-radius": "10px", "display": "flex", "flexDirection": "column"}),
        ], style={
            "flex": "1 1 85%",
            "height": "96vh",
            "display": "flex",
            "flexDirection": "column",
            "overflow": "hidden",
            "border-radius": "10px",
            "margin": "10px 10px 10px 10px"
        })

    ], style={
        "display": "flex",
        "width": "100%",
        "height": "100vh",
        "backgroundColor": brand_colors['Light green']
    })


def hanoi_supply_tab_layout():
    """Hà Nội supply tab layout"""
    return html.Div([
        city_selector(selected_city='hanoi', visible=False),  # Hidden but present for callback
        
        html.Div([sidebar], style={
            "width": "15%",
            "height": "100%",
            "display": "flex",
            "vertical-align":'top',
            "flexDirection": "column",
            "justifyContent": "flex-start"}),

        # Left Panel
        html.Div([
            # Intro card
            dbc.Card([
                dbc.CardBody([
                    html.H2("Food Flows & Supply Chains", style=header_style),
                    html.P(
                        "This analysis maps the flow of food commodities into and across Hà Nội, "
                        "tracing supply routes from producing provinces and international sources. "
                        "Understanding where food comes from—and in what quantities—reveals the city's "
                        "dependence on external supply chains and highlights vulnerabilities to disruption. "
                        "It supports evidence-based planning for food system resilience, local sourcing "
                        "strategies, and equitable distribution across urban and peri-urban populations.",
                        style={
                            "margin": "6px 4px 0 4px",
                            "fontSize": "clamp(0.6em, 0.8em, 1.0em)",
                            "whiteSpace": "normal",
                        }
                    ),
                ])
            ], style={
                "flex": "0 0 auto",
                "width": "100%",
                "padding": "6px",
                "marginBottom": "8px",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                "backgroundColor": brand_colors['White'],
                "borderRadius": "10px",
            }),

            # Commodity selector
            dbc.Card([
                dbc.CardBody([
                    html.H6("Commodity", style={
                        "fontWeight": "bold",
                        "color": brand_colors['Brown'],
                        "fontSize": "clamp(0.7em, 0.85em, 1em)",
                        "marginBottom": "6px",
                    }),
                    dcc.Dropdown(
                        id="supply-commodity-dropdown-hanoi",
                        options=[
                            {"label": "Rice", "value": "rice"},
                            {"label": "Other commodities (coming soon)", "value": "coming_soon", "disabled": True},
                        ],
                        value="rice",
                        clearable=False,
                        style={"fontSize": "clamp(0.75em, 0.9em, 1em)"},
                    ),
                ], style={"padding": "8px 10px"}),
            ], style={
                "flex": "0 0 auto",
                "width": "100%",
                "marginBottom": "8px",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                "backgroundColor": brand_colors['White'],
                "borderRadius": "10px",
            }),

            dbc.Card([
                dbc.CardBody([
                    html.H5("Total Flow", className="card-title", style={
                        "fontWeight": "normal",
                        "fontSize": "clamp(0.6em, 0.8em, 1.2em)",
                        "color": brand_colors['Brown'],
                        "marginBottom": "4px"
                    }),
                    html.H1(id="kpi-total-flow-hanoi", className="card-text", style={
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
                    _red_graph_loading(
                        dcc.Graph(id="urban-indicator-hanoi", style={"height": "clamp(80px, 10vh, 200px)"}, config={"displayModeBar": False}),
                        loading_id="loading-urban-indicator-hanoi",
                    )
                ])
            ], style={**kpi_card_style_2}),

        ], style={
            "flex": "0 0 20%",
            "height": "100%",
            "display": "flex",
            "flexDirection": "column",
            "padding": "10px",
            "margin-left":"20px",
            "alignItems": "center",
            "marginBottom": "auto" 
        }),

        # Sankey + Slider (right)
        html.Div([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        _red_graph_loading(
                            dcc.Graph(
                                id="sankey-graph-hanoi", 
                                style={"width": "100%", "height":"70vh"}  
                            ),
                            loading_id="loading-sankey-graph-hanoi",
                        ),
                    ], style={"width": "100%"}),

                    html.Div([
                        dbc.Button("ⓘ", id="sankey-info-btn-hanoi", style={
                            "fontSize": "1.5em",
                            "color": brand_colors['Red'],
                            "background": "none",
                            "border": "none",
                            "padding": "0",
                            "cursor": "pointer"
                        }),
                        dbc.Tooltip(
                            "Data Source: General Statistics Office of Vietnam (GSO). 2025. Production of paddy by province. Consulted on: June 2025. Link: https://www.nso.gov.vn/en/agriculture-forestry-and-fishery/. Estimation method: Trade attractiveness method, including two steps as follows: A) Estimation of Rice Net Supply (Consumption – Production) for every province, based on Consumption (Population * Consumption per person), and Production (Paddy production/Live weight/Raw production * Conversion rate). B) Distribute the rice consumption of Hanoi, considering: Province Production, National Production, and International Import.",
                            target="sankey-info-btn-hanoi",
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
                        id='slider-hanoi', min=2010, max=2022, value=2022, step=2,
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


def hanoi_poverty_tab_layout():
    """Hà Nội poverty tab layout"""
    import app as main
    mpi_vars = main.mpi_vars
    
    return html.Div([
        city_selector(selected_city='hanoi', visible=False),  # Hidden but present for callback
        
        html.Div([sidebar], style={
            "width": "15%",
            "height": "100%",
            "display": "flex",
            "vertical-align":'top',
            "flexDirection": "column",
            "justifyContent": "flex-start",
        }),

        html.Div([
            dbc.Card([
                dbc.CardBody([
                    html.H2("Multidimensional Poverty Index", style=header_style),
                    html.P("The Multidimensional Poverty Index (MPI) assesses poverty across health, education, and living standards using ten indicators including nutrition, schooling, sanitation, water, electricity, and housing. This spatial analysis maps deprivation levels across Hanoi's districts, revealing where households face multiple overlapping disadvantages. These insights identify priority areas for targeted interventions, supporting equitable resource allocation and sustainable poverty reduction strategies aligned with SDG goals.",
                            style={  "margin": "10px 6px", 
                                    "fontSize": 'clamp(0.6em, 0.8em, 1.0em)',
                                    #"textAlign": "justify",
                                    "whiteSpace": "normal",
                                    })
                ])
            ], style={  "flex": "0 0 auto",
                        "padding":"6px" ,
                        "margin-bottom": "5px",
                        "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                        "backgroundColor": brand_colors['White'],
                        "border-radius": "10px"}),

            html.Div([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Dropdown(
                            id='variable-dropdown-hanoi',
                            options=[{'label': v, 'value': v} for v in mpi_vars],
                            value=mpi_vars[0],
                            persistence=True,
                            persistence_type='session',
                            style={"margin-bottom": "12px"}
                        ),
                        _red_graph_loading(
                            dcc.Graph(
                                id='bar-plot-hanoi',
                                config={"displayModeBar": False, "responsive": True},
                                style={
                                    "minHeight": 0,
                                    "width": "100%",
                                    "flex": "1 1 auto",
                                    'padding': '4px',
                                    'margin': '8px',
                                    "border-radius": "8px",
                                    "box-shadow": "0 2px 8px rgba(0,0,0,0.15)",
                                    "overflowY": "auto"
                                }
                            ),
                            loading_id="loading-bar-plot-hanoi",
                        )
                    ], style={
                        "display": "flex",
                        "flexDirection": "column",
                        "flex": "1 1 auto",
                        "minHeight": 0,
                        "overflow": "hidden"
                    })
                ], style={
                    "flex": "1 1 auto",
                    "width": "100%",
                    "padding": "6px",
                    "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                    "backgroundColor": brand_colors['White'],
                    "border-radius": "10px",
                    "overflow": "hidden",
                    "display": "flex",
                    "flexDirection": "column"
                }),

            ], style={
                "height": "100%",
                "backgroundColor": brand_colors['Light green'],
                "border-radius": "0",
                "margin": "0",
                "display": "flex",
                "flexDirection": "column",
                "box-sizing": "border-box",
                "zIndex": 2,
                "position": "relative",
                "overflowY": "auto"
            }),
        ],style={
            "overflowY": "auto",
            "display": "flex",
            "flexDirection": "column",
            "flex": "0 0 40%",
            "minWidth": "40%",
            "height": "100%",
            "minHeight": 0,
            "padding": "10px",
            "backgroundColor": brand_colors['Light green']
        }),

        # Right panel: map
        html.Div([
            _red_graph_loading(
                dcc.Graph(
                    id='map-hanoi',
                    config={"displayModeBar": False, "scrollZoom": True, "responsive": True},
                    style={"height": "100%",
                           "width": "100%",
                           "padding": "0",
                           "margin": "0"}),
                loading_id="loading-map-hanoi",
            )
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
        "height": "100vh"
    })


def hanoi_affordability_tab_layout_arch():
    """Hà Nội affordability tab layout"""
    return html.Div([
        city_selector(selected_city='hanoi', visible=False),  # Hidden but present for callback
        
        html.Div([sidebar], style={
            "width": "15%",
            "height": "100%",
            "display": "flex",
            "vertical-align":'top',
            "flexDirection": "column",
            "justifyContent": "flex-start",
        }),

        # Left Panel
        html.Div([
            dbc.Card([
                dbc.CardBody([
                    html.H2('Dietary Mapping & Affordability', 
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
                            id='affordability-filter-dropdown-hanoi',
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
                    _red_graph_loading(
                        dcc.Graph(id='affordability-trend-hanoi', 
                                style={
                                    "flex": "1 1 auto",
                                    "height":"98%",
                                    'padding': '4px',
                                    'margin': '0',
                                    "border-radius": "8px",
                                    "box-shadow": "0 2px 8px rgba(0,0,0,0.15)",
                                }),
                        loading_id="loading-affordability-trend-hanoi",
                    )
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
        }),

    ], style={
        "display": "flex", 
        "width": "100%", 
        "height": "100%",
        "backgroundColor": brand_colors['Light green']
    })


def hanoi_health_nutrition_tab_layout():
    """Hà Nội health & nutrition tab layout"""
    import app as main
    df_diet_2_hanoi = main.df_diet_2_hanoi
    
    labels = df_diet_2_hanoi['Cat'].unique()
    
    tile_width, lg = 12, 3
    years = list(range(2010, 2024))

    return html.Div([
        city_selector(selected_city='hanoi', visible=False),  # Hidden but present for callback
        
        html.Div([sidebar], style={
            "width": "15%",
            "height": "100%",
            "display": "flex",
            "vertical-align":'top',
            "flexDirection": "column",
            "justifyContent": "flex-start",
        }),

        # KPI cards (left)
        html.Div([
            html.H3("Children under 5 years", style={
                        "color": brand_colors['Brown'],
                        "fontWeight": "bold",
                        "marginTop": "20px",
                        "marginBottom": "15px",
                        "borderBottom": f"3px solid {brand_colors['Mid green']}",
                        "paddingBottom": "10px"
                    }),
            dbc.Row([
                        dbc.Col([create_nutrition_kpi_card_hanoi(
                                        df_diet_2_hanoi[(df_diet_2_hanoi['Cat'] == labels[0]) & (df_diet_2_hanoi['Reg'] == 'Hanoi')][['Year', 'value']],
                                        labels[0].split(' in ')[0], 
                                        df_diet_2_hanoi[(df_diet_2_hanoi['Cat'] == labels[0]) & (df_diet_2_hanoi['Reg'] == 'Hanoi')]['value'].dropna().values[-1], 
                                        df_diet_2_hanoi[(df_diet_2_hanoi['Cat'] == labels[0]) & (df_diet_2_hanoi['Reg'] == 'Vietnam')]['value'].dropna().values[-1], 
                                        lower_is_better=True)], width=tile_width, lg=lg),

                        dbc.Col([create_nutrition_kpi_card_hanoi(
                                        df_diet_2_hanoi[(df_diet_2_hanoi['Cat'] == labels[1]) & (df_diet_2_hanoi['Reg'] == 'Hanoi')][['Year', 'value']],
                                        labels[1].split(' in ')[0], 
                                        df_diet_2_hanoi[(df_diet_2_hanoi['Cat'] == labels[1]) & (df_diet_2_hanoi['Reg'] == 'Hanoi')]['value'].dropna().values[-1], 
                                        df_diet_2_hanoi[(df_diet_2_hanoi['Cat'] == labels[1]) & (df_diet_2_hanoi['Reg'] == 'Vietnam')]['value'].dropna().values[-1], 
                                        lower_is_better=True)], width=tile_width, lg=lg),

                        dbc.Col([create_nutrition_kpi_card_hanoi(
                                        df_diet_2_hanoi[(df_diet_2_hanoi['Cat'] == labels[2]) & (df_diet_2_hanoi['Reg'] == 'Hanoi')][['Year', 'value']],
                                        labels[2].split(' in ')[0], 
                                        df_diet_2_hanoi[(df_diet_2_hanoi['Cat'] == labels[2]) & (df_diet_2_hanoi['Reg'] == 'Hanoi')]['value'].dropna().values[-1], 
                                        df_diet_2_hanoi[(df_diet_2_hanoi['Cat'] == labels[2]) & (df_diet_2_hanoi['Reg'] == 'Vietnam')]['value'].dropna().values[-1], 
                                        lower_is_better=True)], width=tile_width, lg=lg),

                        dbc.Col([create_nutrition_kpi_card_hanoi(
                                        df_diet_2_hanoi[(df_diet_2_hanoi['Cat'] == labels[3]) & (df_diet_2_hanoi['Reg'] == 'Hanoi')][['Year', 'value']],
                                        labels[3].split(' in ')[0], 
                                        df_diet_2_hanoi[(df_diet_2_hanoi['Cat'] == labels[3]) & (df_diet_2_hanoi['Reg'] == 'Hanoi')]['value'].dropna().values[-1], 
                                        df_diet_2_hanoi[(df_diet_2_hanoi['Cat'] == labels[3]) & (df_diet_2_hanoi['Reg'] == 'Vietnam')]['value'].dropna().values[-1], 
                                        lower_is_better=True)], width=tile_width, lg=lg),
                    ]),

            html.H3("Women of reproductive age", style={
                        "color": brand_colors['Brown'],
                        "fontWeight": "bold",
                        "marginTop": "20px",
                        "marginBottom": "15px",
                        "borderBottom": f"3px solid {brand_colors['Mid green']}",
                        "paddingBottom": "10px"
                    }),

            dbc.Row([

                        dbc.Col([create_nutrition_kpi_card_hanoi(
                                        df_diet_2_hanoi[(df_diet_2_hanoi['Cat'] == labels[4]) & (df_diet_2_hanoi['Reg'] == 'Hanoi')][['Year', 'value']],
                                        labels[4].split(' in ')[0], 
                                        df_diet_2_hanoi[(df_diet_2_hanoi['Cat'] == labels[4]) & (df_diet_2_hanoi['Reg'] == 'Hanoi')]['value'].dropna().values[-1], 
                                        df_diet_2_hanoi[(df_diet_2_hanoi['Cat'] == labels[4]) & (df_diet_2_hanoi['Reg'] == 'Vietnam')]['value'].dropna().values[-1], 
                                        lower_is_better=True)], width=tile_width, lg=lg),
                    ]),

        ], style={
            "width": "min(90%)",
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
        }),
    ], style={
        "display": "flex",
        "width": "100%",
        "height": "100%",
        "backgroundColor": brand_colors['Light green']
    })


def hanoi_affordability_tab_layout():
    """Hanoi affordability tab layout"""
    import app as main
    outlets_geojson_files_hanoi = main.outlets_geojson_files_hanoi
    isochrones_geojson_files_hanoi = main.isochrones_geojson_files_hanoi
    data_labels_food_env = getattr(main, 'data_labels_food_env_hanoi', getattr(main, 'data_labels_food_env', []))
    cols_food_env = getattr(main, 'cols_food_env_hanoi', getattr(main, 'cols_food_env', []))
    df_affordability_hanoi = main.df_affordability_hanoi
    
    return html.Div([
        city_selector(selected_city='hanoi', visible=False),  # Hidden but present for callback
        
            html.Div([sidebar], style={
                                "width": "15%",
                                "height": "100%",
                                "display": "flex",
                                "vertical-align":'top',
                                "flexDirection": "column",
                                "justifyContent": "flex-start",
            }),

            # Left Panel
            html.Div([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([ 
                            html.H2("Food Environment Analysis", style=header_style),
                            html.P("This map shows the distribution of healthy and unhealthy food outlets across Hanoi's districts. The obesogenic ratio reveals where unhealthy outlets dominate, indicating areas with limited access to nutritious food. Population exposure metrics highlight which communities face the greatest imbalance, providing evidence to guide equitable food policy interventions. This analysis forms part of a broader assessment integrating socioeconomic and built environment factors.",
                                       style={  "margin": "10px 6px", 
                                                "fontSize": 'clamp(0.7em, 0.9em, 1.0em)',
                                                #"textAlign": "justify",
                                                "whiteSpace": "normal",
                                                })],
                                style={
                                    'margin': '2px 0px',
                                    'zIndex': '1000',
                                    'justifyContent': 'end',
                                    'alignItems': 'center',
                                    'textAlign': 'center'
                    })],style={
                                "display": "flex",
                                "flexDirection": "column",
                                "height": "100%"             
                            })
                ], style={"height": "auto", 
                            "padding":"6px" ,
                            "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                            "backgroundColor": brand_colors['White'],
                            "border-radius": "10px"}),


                # Food outlets selector first (ensure high z-index so dropdown menus render above others)
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                                html.P(["Select food outlets (30-minute walkability zones display automatically)."],
                                       style={"margin": "6px", 'fontSize': 'clamp(0.7em, 1em, 1.0em)',
                                              "textAlign": "center", "whiteSpace": "normal", "fontStyle": "italic"}),
                                dcc.Dropdown(
                                    id="food-outlets-and-isochrones-hanoi",
                                    options=[
                                        {"label": "Select All", "value": "SELECT_ALL"}
                                    ] + [{
                                        "label": f.split('_')[1] if len(f.split('_')) < 4 else f"{f.split('_')[1]} {f.split('_')[2]}",
                                        "value": f
                                    } for f in outlets_geojson_files_hanoi],
                                    value=None,
                                    multi=True,
                                    placeholder="Select outlet layers to display",
                                    style={'zIndex': '5000', 'position': 'relative'})
                                ],
                                style={'margin': '2px 0px', 'justifyContent': 'end', 'alignItems': 'center', 'textAlign': 'center'}),
                    ])
                ], style={"height": "auto", "padding":"6px", "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                            "backgroundColor": brand_colors['White'], "border-radius": "10px",
                            "zIndex": "5000", "position": "relative", "margin-top": "4px"}),

                # Choropleth metric selector below outlets
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                                html.P(["Select a food environment metric to display as a choropleth layer."],
                                       style={"margin": "6px", 'fontSize': 'clamp(0.7em, 1em, 1.0em)',
                                              "textAlign": "center", "whiteSpace": "normal", "fontStyle": "italic"}),
                                dcc.Dropdown(
                                    id="choropleth-select-hanoi",
                                    options=[{"label": label, "value": col} for label, col in zip(data_labels_food_env, cols_food_env)],
                                    multi=False,
                                    #value='ratio_obesogenic' if 'ratio_obesogenic' in cols_food_env else (cols_food_env[0] if cols_food_env else None),
                                    placeholder="Select metric to display",
                                    style={'zIndex': '1900', 'position': 'relative'})
                                ],
                                style={'margin': '2px 0px', 'justifyContent': 'end', 'alignItems': 'center', 'textAlign': 'center'})
                    ])
                ], style={"height": "auto", "padding":"6px", "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                            "backgroundColor": brand_colors['White'], "border-radius": "10px", "margin-top": "4px"}),
                                
                html.H5(" ", style={
                        "color": brand_colors['Brown'],
                        "fontWeight": "bold",
                        "marginTop": "20px",
                        "marginBottom": "15px",
                        "borderBottom": f"3px solid {brand_colors['Mid green']}",
                        "paddingBottom": "10px"
                    }),
                
                dbc.Row([
                    dbc.Col([create_nutrition_kpi_card_hanoi(
                    df_affordability_hanoi[(df_affordability_hanoi['Cat'] == 'foodExp_totalExp') & (df_affordability_hanoi['Reg'] == 'Hanoi')][['Year', 'value']],
                    "Food Expenditure from Total Expenses",
                    df_affordability_hanoi[(df_affordability_hanoi['Cat'] == 'foodExp_totalExp') & (df_affordability_hanoi['Reg'] == 'Hanoi')]['value'].dropna().values[-1],
                    df_affordability_hanoi[(df_affordability_hanoi['Cat'] == 'foodExp_totalExp') & (df_affordability_hanoi['Reg'] == 'Vietnam')]['value'].dropna().values[-1],
                    lower_is_better=True)], width=12, lg=6),
                
                    dbc.Col([create_nutrition_kpi_card_hanoi(
                    df_affordability_hanoi[(df_affordability_hanoi['Cat'] == 'foodExp_totalInc') & (df_affordability_hanoi['Reg'] == 'Hanoi')][['Year', 'value']],
                    "Food Expenditure from Household Income",
                    df_affordability_hanoi[(df_affordability_hanoi['Cat'] == 'foodExp_totalInc') & (df_affordability_hanoi['Reg'] == 'Hanoi')]['value'].dropna().values[-1],
                    df_affordability_hanoi[(df_affordability_hanoi['Cat'] == 'foodExp_totalInc') & (df_affordability_hanoi['Reg'] == 'Vietnam')]['value'].dropna().values[-1],
                    lower_is_better=True)], width=12, lg=6)
                ]),
                
            ], style={
                    "width": "min(40%)",
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
                }),

                # Right panel: map, full height
                html.Div([
                    dcc.Loading(
                        id="loading-affordability-map-hanoi",
                        parent_style={
                            "height": "100%",
                            "width": "100%",
                            "position": "relative"
                        },
                        style={"height": "100%", "width": "100%"},
                        custom_spinner=html.Div(
                            dbc.Spinner(color="danger", type="border"),
                            style={
                                "position": "absolute",
                                "inset": "0",
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "center",
                                "zIndex": 1000,
                                "pointerEvents": "none",
                            }
                        ),
                        children=html.Div(
                            dcc.Graph(
                                id='affordability-map-hanoi',
                                figure=go.Figure().update_layout(
                                    mapbox=dict(
                                        style="white-bg",
                                        layers=[{
                                            "below": "traces",
                                            "sourcetype": "raster",
                                            "source": ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"],
                                        }],
                                        center={"lat": 21.0, "lon": 105.85},
                                        zoom=9
                                    ),
                                    margin=dict(l=0, r=0, t=0, b=0),
                                    paper_bgcolor=brand_colors['White']
                                ),
                                config={"displayModeBar": False, "scrollZoom": True, "responsive": True},
                                style={"height": "100%", "width": "100%", "padding": "0", "margin": "0"}
                            ),
                            style={"height": "100%", "width": "100%"}
                        )
                    )
                ], style={
                    "flex": "1",
                    "height": "100%",
                    "padding": "0",
                    "margin": "0",
                    "backgroundColor": brand_colors['White'],
                    "border-radius": "0",
                    "display": "flex",
                    "flexDirection": "column",
                    "alignItems": "stretch",
                    "justifyContent": "center",
                    "box-sizing": "border-box",
                    "zIndex": 1000,
                    "position": "relative",
                })

        ], style={
                    "display": "flex", 
                    "width": "100%", 
                    "height": "100%",
                    "backgroundColor": brand_colors['Light green']
        })

def hanoi_sustainability_tab_layout():
    """Hanoi sustainability tab layout - mirrors the Addis sustainability page"""
    import app as main
    df_indicators = main.df_indicators

    display_cols = ['Dimensions', 'Components', 'Indicators', 'SDG impact area/target', 'SDG Numbers']
    df_display = df_indicators[display_cols]

    return html.Div([
        city_selector(selected_city='hanoi', visible=False),  # Hidden but present for callback

        html.Div([sidebar], style={
            "width": "15%",
            "height": "100%",
            "display": "flex",
            "vertical-align": 'top',
            "flexDirection": "column",
            "justifyContent": "flex-start"
        }),

        # Main content area
        html.Div([
            # SDG Filter Buttons at top
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H5("Filter by SDG Goal:", style={
                            "marginBottom": "10px",
                            "fontWeight": "bold",
                            "color": brand_colors['Brown'],
                            "fontSize": "clamp(0.9em, 1.1vw, 1.2em)"
                        }),
                        html.Div([
                            html.Button([
                                html.Img(src=f"/assets/logos/SDG%20logos/SDG%20Web%20Files%20w-%20UN%20Emblem/E%20SDG%20Icons%20Square/E_SDG%20goals_icons-individual-rgb-{str(i).zfill(2)}.png",
                                        style={"height": "80px", "display": "block"}),
                            ],
                            id=f"sdg-filter-{i}",
                            n_clicks=0,
                            style={
                                "border": "3px solid transparent",
                                "borderRadius": "8px",
                                "padding": "5px",
                                "margin": "5px",
                                "cursor": "pointer",
                                "backgroundColor": "transparent",
                                "transition": "all 0.2s"
                            })
                            for i in range(1, 18)
                        ], style={"display": "grid", "gridTemplateColumns": "repeat(9, 1fr)", "gap": "5px", "justifyItems": "center", "maxWidth": "100%"}),
                        html.Button("Clear Filter",
                                   id="sdg-clear-filter",
                                   n_clicks=0,
                                   style={
                                       "marginTop": "10px",
                                       "padding": "8px 20px",
                                       "backgroundColor": brand_colors['Red'],
                                       "color": "white",
                                       "border": "none",
                                       "borderRadius": "5px",
                                       "cursor": "pointer",
                                       "fontWeight": "bold"
                                   }),
                        html.Div(id="sdg-filter-status", style={
                            "marginTop": "10px",
                            "fontSize": "0.9em",
                            "color": brand_colors['Brown'],
                            "fontStyle": "italic"
                        })
                    ])
                ])
            ], style={
                "marginBottom": "15px",
                "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                "backgroundColor": brand_colors['White'],
                "border-radius": "10px",
                "padding": "10px"
            }),

            # Table
            dbc.Card([
                dbc.CardHeader(html.H3("Sustainability Metrics & Indicators", style=header_style)),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='indicators_table',
                        data=df_display.to_dict('records'),
                        columns=[
                            {"name": "SDG Goals" if col == "SDG Numbers" else str(col), "id": str(col)}
                            for col in display_cols
                        ],
                        page_size=14,
                        page_action='native',
                        filter_action='native',
                        sort_action='native',
                        sort_mode='multi',
                        style_cell={
                            'textAlign': 'left',
                            'padding': '8px',
                            'whiteSpace': 'nowrap',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                            'fontSize': 'clamp(0.7em, 1vw, 1em)',
                            'minWidth': '120px',
                            'maxWidth': '250px',
                        },
                        style_cell_conditional=[
                            {
                                'if': {'column_id': 'SDG Numbers'},
                                'minWidth': '100px',
                                'maxWidth': '150px',
                                'textAlign': 'center',
                            }
                        ],
                        style_header={
                            'fontWeight': 'bold',
                            'backgroundColor': brand_colors['Red'],
                            'color': 'white',
                            'textAlign': 'center',
                            'fontSize': 'clamp(0.8em, 1vw, 1.1em)'
                        },
                        style_filter={
                            'backgroundColor': '#f0f0f0',
                            'fontSize': 'clamp(0.7em, 0.9vw, 0.95em)',
                            'padding': '5px'
                        },
                        style_data_conditional=[
                            {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'}
                        ],
                        tooltip_data=[
                            {
                                col: {
                                    'value': str(row[col]) if (col.lower() in ['abstract', 'title', 'keywords'] or len(str(row[col])) > 20) else '',
                                    'type': 'text'
                                } for col in display_cols
                            } for row in df_display.to_dict('records')
                        ],
                        tooltip_duration=None,
                        css=[
                            {
                                'selector': '.dash-table-tooltip',
                                'rule': 'background-color: ' + brand_colors['Light green'] + '; color: ' + brand_colors['Black'] + '; border: 2px solid ' + brand_colors['Dark green'] + '; padding: 6px; font-size: 14px; box-shadow: 0 4px 8px ' + brand_colors['Black'] + ';'
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container',
                                'rule': 'overflow-x: scroll !important; scrollbar-width: auto;'
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container::-webkit-scrollbar',
                                'rule': 'height: 14px; width: 14px; -webkit-appearance: none;'
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container::-webkit-scrollbar-track',
                                'rule': 'background: #f0f0f0; border-radius: 8px;'
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container::-webkit-scrollbar-thumb',
                                'rule': 'background: ' + brand_colors['Dark green'] + '; border-radius: 8px; border: 2px solid #f0f0f0;'
                            }
                        ],
                        style_table={
                            'overflowX': 'scroll',
                            'width': '100%',
                            'height': '100%',
                            'overflowY': 'auto'
                        },
                        style_as_list_view=True
                    )
                ], style={"height": "100%", "display": "flex", "flexDirection": "column", "overflowY": "auto", "overflowX": "auto"})
            ], style={
                "height": "auto",
                "overflowY": "auto",
                "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                "backgroundColor": brand_colors['White'],
                "border-radius": "10px",
                "padding": "10px"
            }),
        ], style={
            "flex": "1 1 85%",
            "height": "90%",
            "display": "flex",
            "flexDirection": "column",
            "overflow": 'auto',
            "border-radius": "10px",
            'margin': "10px 10px 10px 10px"
        })
    ], style={
        "display": "flex",
        "width": "100%",
        "height": "100%",
        "backgroundColor": brand_colors['Light green']
    })


def hanoi_policies_tab_layout():
    """Hanoi policies tab layout"""
    import app as main
    df_policies = main.df_policies_hanoi
    
    return html.Div([
        city_selector(selected_city='hanoi', visible=False),  # Hidden but present for callback
        
        html.Div([sidebar], style={
            "width": "15%",
            "height": "100%",
            "display": "flex",
            "vertical-align": 'top',
            "flexDirection": "column",
            "justifyContent": "flex-start"
        }),

        # Main content area
        html.Div([
            dbc.Card([
                dbc.CardHeader(html.H3("Food System Policies Database", style=header_style)),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='policies_table',
                        data=df_policies.to_dict('records'),
                        columns=[
                            {"name": str(col), "id": str(col), "presentation": "markdown"} if any(k in str(col).lower() for k in ['link', 'website', 'url']) else {"name": str(col), "id": str(col)}
                            for col in df_policies.columns
                        ],
                        page_size=14,
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
                            'maxWidth': '250px',
                            'height': '36px'
                        },
                        style_header={
                            'fontWeight': 'bold',
                            'backgroundColor': brand_colors['Red'],
                            'color': 'white',
                            'textAlign': 'center',
                            'fontSize': 'clamp(0.8em, 1vw, 1.1em)'
                        },
                        style_filter={
                            'backgroundColor': '#f0f0f0',
                            'fontSize': 'clamp(0.64em, 0.85vw, 0.9em)',
                            'padding': '2px 6px'
                        },
                        style_data_conditional=[
                            {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'}
                        ],
                        tooltip_data=[
                            {
                                col: {
                                    'value': str(row[col]) if (col.lower() in ['Abstract', 'Title', 'Keywords'] or len(str(row[col])) > 20) else '',
                                    'type': 'text'
                                }
                                for col in df_policies.columns
                            } for row in df_policies.to_dict('records')
                        ],
                        tooltip_duration=4000,
                        css=[
                            {
                                'selector': '.dash-table-tooltip',
                                'rule': 'position: fixed !important; background-color: ' + brand_colors['Light green'] + '; color: ' + brand_colors['Black'] + '; border: 2px solid ' + brand_colors['Dark green'] + '; padding: 6px; font-size: 14px; box-shadow: 0 4px 8px ' + brand_colors['Black'] + ';'
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container',
                                'rule': 'overflow-x: scroll !important; scrollbar-width: auto;'
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container::-webkit-scrollbar',
                                'rule': 'height: 14px; width: 14px; -webkit-appearance: none;'
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container::-webkit-scrollbar-track',
                                'rule': 'background: #f0f0f0; border-radius: 8px;'
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container::-webkit-scrollbar-thumb',
                                'rule': 'background: ' + brand_colors['Dark green'] + '; border-radius: 8px; border: 2px solid #f0f0f0;'
                            }
                        ],
                        style_table={
                            'overflowX': 'scroll',
                            'width': '100%',
                            'height': '100%',
                            'overflowY': 'auto'
                        }
                    ,
                        style_as_list_view=True
                    )
                ], style={"flex": "1", "display": "flex", "flexDirection": "column", "minHeight": "0"})
            ], style={"height": "100%", "padding": "10px", "box-shadow": "0 2px 6px rgba(0,0,0,0.1)", "backgroundColor": brand_colors['White'], "border-radius": "10px", "display": "flex", "flexDirection": "column"}),
        ], style={
            "flex": "1 1 85%",
            "height": "96vh",
            "display": "flex",
            "flexDirection": "column",
            "overflow": "hidden",
            "border-radius": "10px",
            "margin": "10px 10px 10px 10px"
        })

    ], style={
        "display": "flex",
        "width": "100%",
        "height": "100vh",
        "backgroundColor": brand_colors['Light green']
    })


def _format_indicator_value(value):
    if value is None or pd.isna(value):
        return "N/A"
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    if abs(value) >= 100:
        return f"{value:,.1f}"
    return f"{value:,.2f}"


def _build_temporal_time_labels(df):
    if {'Year', 'Quarter', 'Month'}.issubset(df.columns):
        return [f"{int(y)}-Q{int(q)} M{int(m)}" for y, q, m in zip(df['Year'], df['Quarter'], df['Month'])]
    if {'Year', 'Quarter'}.issubset(df.columns):
        return [f"{int(y)}-Q{int(q)}" for y, q in zip(df['Year'], df['Quarter'])]
    if 'Year' in df.columns:
        return [str(int(y)) for y in df['Year']]
    return [str(i + 1) for i in range(len(df))]


def _load_resilience_metadata_df():
    metadata_path = os.path.join(
        os.path.dirname(__file__),
        "assets", "data", "hanoi", "resilience", "resilience_indicators_ref.csv"
    )
    try:
        ref_df = pd.read_csv(metadata_path)
        expected_cols = {"Indicator", "Pillar", "Component", "Unit", "Source"}
        if not expected_cols.issubset(set(ref_df.columns)):
            return pd.DataFrame(columns=["Indicator", "Pillar", "Component", "Unit", "Source"])
        return ref_df[["Indicator", "Pillar", "Component", "Unit", "Source"]].copy()
    except Exception:
        return pd.DataFrame(columns=["Indicator", "Pillar", "Component", "Unit", "Source"])


def _create_resilience_temporal_kpi_card(df, indicator_col, time_labels, line_color, unit=None, source=None):
    values = pd.to_numeric(df[indicator_col], errors='coerce')
    valid = values.dropna()
    latest_value = valid.iloc[-1] if not valid.empty else np.nan

    sparkline = go.Figure()
    sparkline.add_trace(go.Scatter(
        x=list(range(len(values))),
        y=values,
        mode="lines+markers",
        line=dict(color=line_color, width=2),
        marker=dict(size=4, color=line_color),
        text=time_labels,
        hovertemplate="%{text}: %{y:.3f}<extra></extra>"
    ))
    sparkline.update_layout(
        height=80,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    return dbc.Card([
        dbc.CardBody([
            html.H5(indicator_col, style={
                "fontWeight": "bold",
                "fontSize": "0.95em",
                "color": brand_colors['Brown'],
                "marginBottom": "10px",
                "lineHeight": "1.25",
                "minHeight": "48px"
            }),
            html.Div(_format_indicator_value(latest_value), style={
                "fontSize": "2.0em",
                "fontWeight": "bold",
                "color": brand_colors['Red'],
                "lineHeight": "1.2",
                "marginBottom": "8px",
                "minHeight": "32px"
            }),
            html.Div(unit if unit else "", style={
                "fontSize": "0.85em",
                "color": brand_colors['Brown'],
                "fontStyle": "italic",
                "minHeight": "18px",
                "marginBottom": "6px"
            }),
            dcc.Graph(
                figure=sparkline,
                config={"displayModeBar": False},
                style={"height": "80px", "width": "100%"},
            ),
            html.Div(source if source else "", style={
                "fontSize": "0.7em",
                "color": "#888888",
                "fontStyle": "italic",
                "textAlign": "right",
                "marginTop": "4px",
                "minHeight": "14px",
            })
        ])
    ], style={**kpi_card_style_2, "height": "100%"})


def _build_temporal_pillar_section(title, csv_filename, line_color, pillar_num, ref_df):
    data_path = os.path.join(
        os.path.dirname(__file__),
        "assets", "data", "hanoi", "resilience", csv_filename
    )

    try:
        df = pd.read_csv(data_path)
    except Exception as exc:
        return dbc.Card([
            dbc.CardBody([
                html.H3(title, style={
                    "color": brand_colors['Brown'],
                    "fontWeight": "bold",
                    "marginBottom": "8px",
                }),
                html.P(f"Could not load {csv_filename}: {exc}", style={"color": brand_colors['Red']})
            ])
        ], style={"padding": "8px", "marginBottom": "12px", "backgroundColor": brand_colors['White'], "borderRadius": "10px"})

    sort_cols = [c for c in ["Year", "Quarter", "Month"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols).reset_index(drop=True)

    time_labels = _build_temporal_time_labels(df)
    indicator_cols = [c for c in df.columns if c not in ["Year", "Quarter", "Month"]]

    # Population should only appear under pillar 1.
    if pillar_num in [2, 3]:
        indicator_cols = [c for c in indicator_cols if c != "Population"]

    meta_lookup = ref_df.set_index("Indicator") if not ref_df.empty else pd.DataFrame()

    # Group indicators by component and sort indicators alphabetically within each component.
    component_groups = {}
    for col in indicator_cols:
        component = "Other"
        if not isinstance(meta_lookup, pd.DataFrame) or meta_lookup.empty:
            component = "Other"
        elif col in meta_lookup.index:
            component_val = meta_lookup.loc[col, "Component"]
            if isinstance(component_val, pd.Series):
                component_val = component_val.iloc[0]
            if pd.notna(component_val) and str(component_val).strip() != "":
                component = str(component_val).strip()
        component_groups.setdefault(component, []).append(col)

    section_children = []
    for component in sorted(component_groups.keys(), key=lambda x: x.lower()):
        cards = []
        for col in sorted(component_groups[component], key=lambda x: x.lower()):
            unit = None
            source = None
            if isinstance(meta_lookup, pd.DataFrame) and not meta_lookup.empty and col in meta_lookup.index:
                unit_val = meta_lookup.loc[col, "Unit"]
                if isinstance(unit_val, pd.Series):
                    unit_val = unit_val.iloc[0]
                unit = str(unit_val).strip() if pd.notna(unit_val) and str(unit_val).strip() != "" else None

                source_val = meta_lookup.loc[col, "Source"]
                if isinstance(source_val, pd.Series):
                    source_val = source_val.iloc[0]
                source = str(source_val).strip() if pd.notna(source_val) and str(source_val).strip() != "" else None

            numeric_vals = pd.to_numeric(df[col], errors='coerce')
            if numeric_vals.notna().sum() == 0:
                continue
            df_plot = df.copy()
            df_plot[col] = numeric_vals
            cards.append(
                dbc.Col(
                    _create_resilience_temporal_kpi_card(df_plot, col, time_labels, brand_colors['Dark green'], unit=unit, source=source),
                    xs=12,
                    md=6,
                    lg=4,
                    style={"display": "flex"}
                )
            )

        if cards:
            section_children.append(
                dbc.Card([
                    dbc.CardHeader(
                        html.H5(component, style={
                            "color": brand_colors['White'],
                            "fontWeight": "bold",
                            "margin": "0",
                        }),
                        style={"backgroundColor": brand_colors['Mid green'], "borderRadius": "7px 7px 0 0"}
                    ),
                    dbc.CardBody([
                        dbc.Row(cards, className="g-3")
                    ], style={"padding": "12px"})
                ], style={
                    "marginBottom": "12px",
                    "borderRadius": "8px",
                    "backgroundColor": brand_colors['Light green'],
                    "border": f"1px solid {brand_colors['Mid green']}",
                    "boxShadow": "0 1px 4px rgba(0,0,0,0.08)",
                })
            )

    body_children = [
        html.H3(title, style={
            "color": brand_colors['Brown'],
            "fontWeight": "bold",
            "marginBottom": "14px",
            "borderBottom": f"3px solid {brand_colors['Mid green']}",
            "paddingBottom": "8px"
        })
    ]
    if section_children:
        body_children.extend(section_children)
    else:
        body_children.append(html.P("No numeric indicators available."))

    return dbc.Card([
        dbc.CardBody(body_children)
    ], style={
        "padding": "8px",
        "marginBottom": "14px",
        "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
        "backgroundColor": brand_colors['White'],
        "border-radius": "10px"
    })


def _load_sos_data():
    """Load Resilience_SOS.csv and return annual-averaged DataFrame."""
    sos_path = os.path.join(
        os.path.dirname(__file__),
        "assets", "data", "hanoi", "resilience", "Resilience_SOS.csv"
    )
    try:
        df = pd.read_csv(sos_path)
        res_ann = (
            df.groupby(['Year', 'Pillar'])[['Index', 'SOS', 'Residual']]
            .mean()
            .reset_index()
        )
        res_ann['Index'] = res_ann['Index'] #- 1
        res_ann['SOS'] = res_ann['SOS'] #- 1
        return res_ann
    except Exception:
        return pd.DataFrame()


def _create_sos_figure(pillar_num, title, res_ann, show_legend=False):
    """Create a Plotly Safe Operating Space chart for one pillar."""
    mid_green = brand_colors['Mid green']   # #bbce8a
    red = brand_colors['Red']               # #A80050
    dark = brand_colors['Brown']            # #313715

    if res_ann.empty:
        return go.Figure()

    df_sub = res_ann[res_ann['Pillar'] == pillar_num].copy()
    if df_sub.empty:
        return go.Figure()

    years = df_sub['Year'].tolist()
    index_vals = df_sub['Index'].tolist()
    sos_vals = df_sub['SOS'].tolist()
    residuals = df_sub['Residual'].tolist()

    within_x = [y for y, r in zip(years, residuals) if r >= 0]
    within_y = [v for v, r in zip(index_vals, residuals) if r >= 0]
    outside_x = [y for y, r in zip(years, residuals) if r < 0]
    outside_y = [v for v, r in zip(index_vals, residuals) if r < 0]

    fig = go.Figure()

    # Invisible baseline at y=1 for fill reference (SOS fill is between SOS line and 1)
    fig.add_trace(go.Scatter(
        x=years, y=[2] * len(years),
        fill=None, mode='lines',
        line=dict(color='rgba(0,0,0,0)'),
        showlegend=False, hoverinfo='skip'
    ))

    # SOS filled area between sos_vals and y=1
    fig.add_trace(go.Scatter(
        x=years, y=sos_vals,
        fill='tonexty',
        fillcolor='rgba(187,206,138,0.35)',
        mode='lines',
        line=dict(color=mid_green, width=1.5, dash='dot'),
        name='Safe Operating Space',
        showlegend=show_legend,
        hovertemplate='%{x}: SOS = %{y:.3f}<extra></extra>'
    ))

    # Resilience Index line
    fig.add_trace(go.Scatter(
        x=years, y=index_vals,
        mode='lines',
        line=dict(color=dark, width=2),
        name='Resilience Index',
        showlegend=show_legend,
        hovertemplate='%{x}: Index = %{y:.3f}<extra></extra>'
    ))

    # Within SOS scatter (Mid green)
    if within_x:
        fig.add_trace(go.Scatter(
            x=within_x, y=within_y,
            mode='markers',
            marker=dict(color=mid_green, size=9, line=dict(color=dark, width=1)),
            name='Within SOS',
            showlegend=show_legend,
            hovertemplate='%{x}: %{y:.3f}<extra></extra>'
        ))

    # Outside SOS scatter (Red)
    if outside_x:
        fig.add_trace(go.Scatter(
            x=outside_x, y=outside_y,
            mode='markers',
            marker=dict(color=red, size=9, line=dict(color=dark, width=1)),
            name='Outside SOS',
            showlegend=show_legend,
            hovertemplate='%{x}: %{y:.3f}<extra></extra>'
        ))

    legend_margin_b = 80 if show_legend else 40
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=12, color=dark, weight='bold'),
            x=0.5, xanchor='center'
        ),
        margin=dict(l=40, r=20, t=40, b=legend_margin_b),
        height=260 + (40 if show_legend else 0),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=11),
        showlegend=show_legend,
        legend=dict(
            orientation='h', yanchor='bottom', y=-0.5,
            xanchor='center', x=0.5, font=dict(size=9)
        ),
        xaxis=dict(
            tickmode='linear', dtick=5,
            gridcolor='#e8e8e8', title=None
        ),
        yaxis=dict(
            gridcolor='#e8e8e8', title=None,
            zeroline=True, zerolinecolor='#aaaaaa', zerolinewidth=1
        ),
    )
    return fig


def render_temporal_resilience_layout():
    """Temporal (city-level indicators) sub-layout for the resilience tab."""
    sections = [
        (1, "Pillar 1: Resilience Capacities", "resilience_indicators_p1.csv", brand_colors['Dark green']),
        (2, "Pillar 2: System Structure & Connectivity", "resilience_indicators_p2.csv", brand_colors['Mid green']),
        (3, "Pillar 3: System Stability & Shocks", "resilience_indicators_p3.csv", brand_colors['Brown']),
    ]
    ref_df = _load_resilience_metadata_df()
    res_ann = _load_sos_data()

    pillar_labels = [
        (1, "Pillar 1: Resilience Capacities"),
        (2, "Pillar 2: Structure & Connectivity"),
        (3, "Pillar 3: Stability & Shocks"),
    ]

    sos_section = dbc.Card([
        dbc.CardHeader(
            html.H4("Composite Resilience Index & Safe Operating Space", style={
                "color": brand_colors['White'],
                "fontWeight": "bold",
                "margin": "0",
            }),
            style={
                "backgroundColor": brand_colors['Dark green'],
                "borderRadius": "9px 9px 0 0"
            }
        ),
        dbc.CardBody([
            #html.P(
            #    "The Resilience Index is plotted relative to 1 (the baseline). "
            #    "The shaded area shows the Safe Operating Space (SOS). "
            #    "Green markers indicate years within the SOS; red markers indicate years outside it.",
            #    style={"fontSize": "0.85em", "marginBottom": "10px", "color": brand_colors['Brown']}
            #),
            dbc.Row([
                dbc.Col(
                    _red_graph_loading(
                        dcc.Graph(
                            figure=_create_sos_figure(num, label, res_ann, show_legend=(num == 2)),
                            config={'displayModeBar': False},
                            style={"width": "100%"}
                        ),
                        loading_id=f"loading-sos-pillar-{num}",
                    ),
                    xs=12, md=4
                )
                for num, label in pillar_labels
            ], className="g-2")
        ], style={"padding": "12px"})
    ], style={
        "marginBottom": "14px",
        "borderRadius": "10px",
        "backgroundColor": brand_colors['White'],
        "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
    })

    return html.Div([
        #dbc.Card([
        #    dbc.CardBody([
        #        html.H2("Temporal Resilience Indicators", style=header_style),
        #        html.P(
        #            "This view summarizes city-level resilience indicators over time. "
        #            "Each card shows the latest value and a sparkline of the historical trend.",
        #            style={
        #                "margin": "10px 6px",
        #                "fontSize": 'clamp(0.7em, 0.9em, 1.0em)',
        #                "whiteSpace": "normal",
        #            }
        #        )
        #    ])
        #], style={
        #    "height": "auto", "padding": "6px", "marginBottom": "10px",
        #    "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
        #    "backgroundColor": brand_colors['White'], "borderRadius": "10px"
        #}),

        sos_section,

        *[
            _build_temporal_pillar_section(title, filename, color, pillar_num, ref_df)
            for pillar_num, title, filename, color in sections
        ]
    ], style={
        "height": "100%",
        "overflowY": "auto",
        "padding": "6px",
        "backgroundColor": brand_colors['Light green']
    })


def render_spatial_resilience_layout(climate_indicator_options, indicator_descriptions, n, quarter_marks):
    """Spatial (map) sub-layout for the resilience tab."""
    return html.Div([

        # ── Left panel ──────────────────────────────────────────
        html.Div([

            dbc.Card([
                dbc.CardBody([
                    html.H2("Biophysical Shocks", style=header_style),
                    html.P(
                        "This page provides a multi-dimensional view of biophysical shocks across Hanoi's districts and nationally, "
                        "integrating climate resilience for vegetation health in key production areas, water availability trends, and districts most "
                        "frequently impacted by severe water deficits. "
                        "Select an indicator below to explore how different aspects of biophysical shocks have evolved over time. ",
                        style={
                            "margin": "10px 6px",
                            "fontSize": 'clamp(0.6em, 0.9em, 1.0em)',
                            "whiteSpace": "normal",
                        }
                    )
                ])
            ], style={
                "height": "auto", "padding": "6px", "marginBottom": "10px",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                "backgroundColor": brand_colors['White'], "borderRadius": "10px"
            }),

            dbc.Card([
                dbc.CardBody([
                    html.P("Select a climate stress indicator:",
                           style={"margin": "6px", "fontSize": 'clamp(0.7em, 1em, 1.0em)',
                                  "textAlign": "center", "fontStyle": "italic"}),
                    dcc.Dropdown(
                        id="climate-indicator-select",
                        options=climate_indicator_options,
                        value="vci_severe_pct",
                        clearable=False,
                        style={"zIndex": "2000", "marginBottom": "6px"}
                    ),
                    dbc.Card([
                        dbc.CardBody([
                            html.Div(
                                id="climate-indicator-description",
                                children=indicator_descriptions.get("vci_severe_pct", ""),
                                style={
                                    "padding": "2px 4px",
                                    "fontSize": "clamp(0.65em, 0.85em, 0.95em)",
                                    "color": brand_colors['Brown'],
                                    "fontStyle": "italic",
                                    "lineHeight": "1.4"
                                }
                            )
                        ])
                    ], id="climate-indicator-description-card", style={
                        "height": "auto", "padding": "6px", "marginBottom": "10px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                        "backgroundColor": brand_colors['Light green'], "borderRadius": "10px"
                    }),
                ])
            ], style={
                "height": "auto", "padding": "6px", "marginBottom": "10px",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                "backgroundColor": brand_colors['White'], "borderRadius": "10px",
                "zIndex": "2000", "position": "relative"
            }),

            # ── Date slider ──────────────────────────────────────
            dbc.Card([
                dbc.CardBody([
                    html.P("Select a date:",
                           style={"margin": "6px", "fontSize": 'clamp(0.7em, 1em, 1.0em)',
                                  "textAlign": "center", "fontStyle": "italic"}),
                    html.Label(
                        id="drought-slider-label",
                        style={
                            'fontWeight': 'bold', 'textAlign': 'center', 'display': 'block',
                            'color': brand_colors['Red'],
                            'fontSize': 'clamp(0.9em, 1.1em, 1.4em)', 'marginBottom': '8px'
                        }
                    ),
                    dcc.Slider(
                        id="drought-date-slider",
                        min=0,
                        max=n - 1,
                        step=1,
                        value=50,
                        marks=quarter_marks,
                        updatemode="mouseup",
                    ),
                ])
            ], id="date-slider-card", style={
                "height": "auto", "padding": "6px", "marginBottom": "10px",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                "backgroundColor": brand_colors['White'], "borderRadius": "10px"
            }),

            html.Div(id="region-kpi-cards", className="mt-3"),

            # EMDAT natural disasters summary
            dbc.Card([
                dbc.CardBody([
                    html.H6("EMDAT Natural Disasters (2000-2026)", style={"marginBottom": "6px", "fontSize": "0.9em", "fontWeight": "bold"}),
                    html.Div("Summary of natural disaster events and total affected (source: EMDAT)", style={"fontSize": "0.8em", "color": "#444", "marginBottom": "6px"}),
                    _red_graph_loading(
                        dcc.Graph(
                            id='resilience-emdat-graph',
                            config={"displayModeBar": False},
                            style={"flex": "1 1 auto", "minHeight": "0", "height": "600px", "width": "100%"}
                        ),
                        loading_id="loading-resilience-emdat-hanoi",
                    )
                ], style={"display": "flex", "flexDirection": "column", "flex": "1 1 auto", "minHeight": "0"})
            ], style={
                "height": "auto", "padding": "2px", "marginTop": "10px",
                "box-shadow": "0 2px 6px rgba(0,0,0,0.08)",
                "backgroundColor": brand_colors['White'], "border-radius": "10px",
                "display": "flex", "flexDirection": "column"
            }),

        ], style={
            "width": "min(50%)", "height": "100%", "padding": "10px",
            "backgroundColor": brand_colors['Light green'], "borderRadius": "0", "margin": "0",
            "display": "flex", "flexDirection": "column", "justifyContent": "flex-start",
            "overflowY": "auto", "boxSizing": "border-box", "position": "relative",
        }),

        # ── Right panel: map ─────────────────────────────────────
        html.Div(
            dcc.Loading(
                id="loading-drought-map",
                parent_style={"height": "100%", "width": "100%", "position": "relative"},
                style={"height": "100%", "width": "100%"},
                custom_spinner=html.Div(
                    dbc.Spinner(color="danger", type="border"),
                    style={
                        "position": "absolute", "inset": "0", "display": "flex",
                        "alignItems": "center", "justifyContent": "center",
                        "zIndex": 1000, "pointerEvents": "none",
                    }
                ),
                children=html.Div(
                    id="drought-map-container",
                    style={"height": "100%", "width": "100%"},
                ),
            ),
            style={"flex": "1", "height": "100%", "minHeight": "calc(100vh - 140px)"}
        ),

    ], style={"display": "flex", "width": "100%", "height": "100%"})


def render_lulc_resilience_layout(lulc_indicator_options):
    """Land-use & Land-cover sub-layout for the resilience tab."""
    default_value = None
    if lulc_indicator_options:
        default_value = lulc_indicator_options[0].get("value")

    return html.Div([

        html.Div([
            dbc.Card([
                dbc.CardBody([
                    html.H2("Land-use & Land-cover", style=header_style),
                    html.P(
                        "Explore district-level land-use and land-cover indicators for Hanoi. "
                        "Select a variable to display the corresponding district pattern on the map.",
                        style={
                            "margin": "10px 6px",
                            "fontSize": 'clamp(0.6em, 0.9em, 1.0em)',
                            "whiteSpace": "normal",
                        }
                    )
                ])
            ], style={
                "height": "auto", "padding": "6px", "marginBottom": "10px",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                "backgroundColor": brand_colors['White'], "borderRadius": "10px"
            }),

            dbc.Card([
                dbc.CardBody([
                    html.P(
                        "Select a land-cover indicator:",
                        style={
                            "margin": "6px", "fontSize": 'clamp(0.7em, 1em, 1.0em)',
                            "textAlign": "center", "fontStyle": "italic"
                        }
                    ),
                    dcc.Dropdown(
                        id="lulc-indicator-select",
                        options=lulc_indicator_options,
                        value=default_value,
                        clearable=False,
                        style={"zIndex": "2000", "marginBottom": "6px"}
                    ),
                ])
            ], style={
                "height": "auto", "padding": "6px", "marginBottom": "10px",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                "backgroundColor": brand_colors['White'], "borderRadius": "10px",
                "zIndex": "2000", "position": "relative"
            }),
        ], style={
            "width": "min(50%)", "height": "100%", "padding": "10px",
            "backgroundColor": brand_colors['Light green'], "borderRadius": "0", "margin": "0",
            "display": "flex", "flexDirection": "column", "justifyContent": "flex-start",
            "overflowY": "auto", "boxSizing": "border-box", "position": "relative",
        }),

        html.Div(
            dcc.Loading(
                id="loading-lulc-map",
                parent_style={"height": "100%", "width": "100%", "position": "relative"},
                style={"height": "100%", "width": "100%"},
                custom_spinner=html.Div(
                    dbc.Spinner(color="danger", type="border"),
                    style={
                        "position": "absolute", "inset": "0", "display": "flex",
                        "alignItems": "center", "justifyContent": "center",
                        "zIndex": 1000, "pointerEvents": "none",
                    }
                ),
                children=html.Div(
                    id="lulc-map-container",
                    style={"height": "100%", "width": "100%"},
                ),
            ),
            style={"flex": "1", "height": "100%", "minHeight": "calc(100vh - 140px)"}
        ),

    ], style={"display": "flex", "width": "100%", "height": "100%"})


def hanoi_resilience_tab_layout(all_quarters, default_view='Biophysical shocks'):
    """Hà Nội climate tab layout - Multi-dimensional Climate Stress Indicators"""

    n = len(all_quarters)
    max_tick_labels = 11  # target number of visible labels
    step = max(1, int(np.ceil((n - 1) / max(1, (max_tick_labels - 1)))))

    quarter_marks = {
        i: {"label": all_quarters[i][:4], "style": {"fontSize": "10px", "color": "#8c8590"}}
        for i in range(0, n, step)
    }
    quarter_marks[0] = {"label": all_quarters[0][:4], "style": {"fontSize": "10px", "color": "#8c8590"}}

    climate_indicator_options = [
        {"label": "── Vegetation ──", "value": "divider_veg", "disabled": True},
        {"label": "Vegetative Stress (VCI)", "value": "vci_severe_pct"},
        {"label": "Vegetation Drought Resistance", "value": "drought_resistance"},
        {"label": "── Water ──", "value": "divider_water", "disabled": True},
        {"label": "Water Storage Anomalies", "value": "grace_trend"},
        {"label": "Soil Moisture Stress (coming soon)", "value": "soil_moisture", "disabled": True},
        {"label": "── Precipitation Deficit (SPEI) ──", "value": "divider_spei", "disabled": True},
        {"label": "Short-term Moderate Drought", "value": "class_-3_months_SPEI3"},
        {"label": "Short-term Severe Drought", "value": "class_-2_months_SPEI3"},
        {"label": "Short-term Extreme Drought", "value": "class_-1_months_SPEI3"},
        {"label": "Seasonal Moderate Drought", "value": "class_-3_months_SPEI6"},
        {"label": "Seasonal Severe Drought", "value": "class_-2_months_SPEI6"},
        {"label": "Seasonal Extreme Drought", "value": "class_-1_months_SPEI6"},
        {"label": "Long-term Moderate Drought", "value": "class_-3_months_SPEI12"},
        {"label": "Long-term Severe Drought", "value": "class_-2_months_SPEI12"},
        {"label": "Long-term Extreme Drought", "value": "class_-1_months_SPEI12"},
    ]

    indicator_descriptions = {
        "vci_severe_pct": "The Vegetation Condition Index (VCI) measures relative vegetation health compared to historical conditions. Quantiles are applied to calculate indicators of stress; this map shows the percentage of each district under severe vegetative stress.",
        "drought_resistance": "Vegetation Drought Resistance measures how well cropland vegetation maintained healthy VCI during SPEI6 drought events, weighted by how severe the stress conditions were. Higher values indicate crops sustained better health under equivalent stress. Grey districts recorded no drought that year.",
        "grace_trend": "GRACE Terrestrial Water Storage Anomalies (TWSA) capture changes in total water storage — including groundwater, surface water, and soil moisture — relative to a long-term baseline. Negative anomalies signal depletion.",
        "soil_moisture": "Soil Moisture Stress reflects root-zone water availability for crops. Severe deficits indicate conditions where plants cannot access sufficient water, directly threatening agricultural yields.",
        "class_-3_months_SPEI3": "SPEI-3 Moderate Drought captures the short-term water balance deficits aggregated by number of months since 1990.",
        "class_-2_months_SPEI3": "SPEI-3 Severe Drought captures the short-term water balance deficits aggregated by number of months since 1990.",
        "class_-1_months_SPEI3": "SPEI-3 Extreme Drought captures the short-term water balance deficits aggregated by number of months since 1990.",
        "class_-3_months_SPEI6": "SPEI-6 Moderate Drought captures the seasonal water balance deficits aggregated by number of months since 1990.",
        "class_-2_months_SPEI6": "SPEI-6 Severe Drought captures the seasonal water balance deficits aggregated by number of months since 1990.",
        "class_-1_months_SPEI6": "SPEI-6 Extreme Drought captures the seasonal water balance deficits aggregated by number of months since 1990.",
        "class_-3_months_SPEI12": "SPEI-12 Moderate Drought captures the long-duration water balance deficits aggregated by number of months since 1990.",
        "class_-2_months_SPEI12": "SPEI-12 Severe Drought captures the long-duration water balance deficits aggregated by number of months since 1990.",
        "class_-1_months_SPEI12": "SPEI-12 Extreme Drought captures the long-duration water balance deficits aggregated by number of months since 1990.",
    }

    view_options = ['Biophysical shocks', 'Resilience Indicator Trends', 'Land-use & Land-cover']
    selected_view = default_view if default_view in view_options else 'Biophysical shocks'

    if selected_view == 'Resilience Indicator Trends':
        initial_view_content = render_temporal_resilience_layout()
    elif selected_view == 'Land-use & Land-cover':
        initial_view_content = render_lulc_resilience_layout([])
    else:
        initial_view_content = render_spatial_resilience_layout(climate_indicator_options, indicator_descriptions, n, quarter_marks)

    return html.Div([
        city_selector(selected_city='hanoi', visible=False),
        dcc.Store(id="climate-indicator-descriptions", data=indicator_descriptions),
        dcc.Store(id="resilience-spatial-data", data={
            "n": n,
            "quarter_marks": quarter_marks,
            "climate_indicator_options": climate_indicator_options,
            "indicator_descriptions": indicator_descriptions,
        }),
        html.Script(f"window.quarterLookup = {json.dumps(all_quarters)};"),

        html.Div([sidebar], style={
            "width": "15%",
            "height": "100%",
            "display": "flex",
            "vertical-align": 'top',
            "flexDirection": "column",
            "justifyContent": "flex-start",
        }),

        # ── Content area: toggle + dynamic view container ────────
        html.Div([
            dbc.CardHeader(
                dcc.Dropdown(
                    id="resilience_view-select",
                    options=view_options,
                    value=selected_view,
                    clearable=False,
                    style={"zIndex": "2000", "marginBottom": "0", 'fontSize': 'clamp(0.8em, 1em, 1.4em)', 'width': '100%'}
                ),
                style={
                    "height": "auto", "padding": "6px", "marginBottom": "10px",
                    "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                    "backgroundColor": brand_colors['White'], "borderRadius": "10px"
                }
            ),
            html.Div(
                id="resilience-view-container",
                children=initial_view_content,
                style={"flex": "1", "display": "flex", "minHeight": 0}
            ),
        ], style={
            "flex": "1", "height": "100%", "display": "flex", "flexDirection": "column",
            "backgroundColor": brand_colors['Light green'], "padding": "10px",
            "overflowY": "auto", "boxSizing": "border-box",
        }),

    ], style={"display": "flex", "width": "100vw", "height": "100%"})