"""
Hà Nội dashboard tab layouts
"""
import json

import numpy as np
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import json

from config import brand_colors, header_style, kpi_card_style_2, card_style
from shared_components import sidebar, city_selector
from dashboard_components import create_nutrition_kpi_card, create_nutrition_kpi_card_hanoi


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
            #dbc.Card([
            #    dbc.CardBody([
            #        html.H2('Rice Flow Estimations', 
            #                style=header_style),
            #    ])
            #], style={"height": "auto",
            #          "width":"100%",
            #          "padding":"1px" ,
            #          "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
            #          "backgroundColor": brand_colors['Mid green'],
            #          "border-radius": "10px",
            #          'margin':"0px 0px 10px 0px",
            #          "justifyContent": "center"
            #}),

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
                    dcc.Graph(id="urban-indicator-hanoi", style={"height": "clamp(80px, 10vh, 200px)"}, config={"displayModeBar": False})
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
                        dcc.Graph(
                            id="sankey-graph-hanoi", 
                            style={"width": "100%", "height":"70vh"}  
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
            dcc.Graph(
                id='map-hanoi',
                config={"displayModeBar": False, "scrollZoom": True, "responsive": True},
                style={"height": "100%",
                       "width": "100%",
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
                    dcc.Graph(id='affordability-trend-hanoi', 
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
    
    tile_width, lg = 12, 4
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
                    ]),

            dbc.Row([
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
                            "zIndex": "5000", "position": "relative"}),

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
                                    value='ratio_obesogenic' if 'ratio_obesogenic' in cols_food_env else (cols_food_env[0] if cols_food_env else None),
                                    placeholder="Select metric to display",
                                    style={'zIndex': '1900', 'position': 'relative'})
                                ],
                                style={'margin': '2px 0px', 'justifyContent': 'end', 'alignItems': 'center', 'textAlign': 'center'})
                    ])
                ], style={"height": "auto", "padding":"6px", "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                            "backgroundColor": brand_colors['White'], "border-radius": "10px"}),
                
            ], style={
                    "width": "min(30%)",
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
                                    mapbox=dict(style="carto-positron", center={"lat": 21.0, "lon": 105.85}, zoom=9),
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


def hanoi_resilience_tab_layout(all_quarters):
    """Hà Nội climate tab layout - Multi-dimensional Climate Stress Indicators"""

    n = len(all_quarters)
    max_tick_labels = 11  # target number of visible labels
    step = max(1, int(np.ceil((n - 1) / max(1, (max_tick_labels - 1)))))

    quarter_marks = {
        i: {"label": all_quarters[i][:4], "style": {"fontSize": "10px", "color": "#8c8590"}}
        for i in range(0, n, step)
    }
    quarter_marks[0] = {"label": all_quarters[0][:4], "style": {"fontSize": "10px", "color": "#8c8590"}}
    #quarter_marks[n - 1] = {"label": all_quarters[-1][:4], "style": {"fontSize": "10px", "color": "#8c8590"}}


    climate_indicator_options = [
        {"label": "── Vegetation ──", "value": "divider_veg", "disabled": True},
        {"label": "Vegetative Stress (VCI)", "value": "vci_severe_pct"},
        {"label": "Vegetation Drought Resistance", "value": "drought_resistance"},  
       #{"label": "Vegetation Flood Resistance", "value": "flood_resistance"},  
        {"label": "── Water ──", "value": "divider_water", "disabled": True},
        {"label": "Water Storage Anomalies", "value": "grace_trend"},
        {"label": "Soil Moisture Stress (coming soon)", "value": "soil_moisture", "disabled": True},
        {"label": "── Precipitation Deficit (SPEI) ──", "value": "divider_spei", "disabled": True},
        {"label": "SPEI-3 Moderate Drought", "value": "class_-3_months_SPEI3"},
        {"label": "SPEI-3 Severe Drought", "value": "class_-2_months_SPEI3"},
        {"label": "SPEI-3 Extreme Drought", "value": "class_-1_months_SPEI3"},
        {"label": "SPEI-6 Moderate Drought", "value": "class_-3_months_SPEI6"},
        {"label": "SPEI-6 Severe Drought", "value": "class_-2_months_SPEI6"},
        {"label": "SPEI-6 Extreme Drought", "value": "class_-1_months_SPEI6"},
        {"label": "SPEI-12 Moderate Drought", "value": "class_-3_months_SPEI12"},
        {"label": "SPEI-12 Severe Drought", "value": "class_-2_months_SPEI12"},
        {"label": "SPEI-12 Extreme Drought", "value": "class_-1_months_SPEI12"},
        #{"label": "SPEI-24  (Long-term, 24-month)", "value": "spei24"},
    ]

    # Descriptions shown in the info card per indicator
    indicator_descriptions = {
        "vci_severe_pct": "The Vegetation Condition Index (VCI) measures relative vegetation health compared to historical conditions. Quantiles are applied to calculate indicators of stress; this map shows the percentage of each district under severe vegetative stress.",
        "drought_resistance": "Vegetation Drought Resistance measures how well cropland vegetation maintained healthy VCI during SPEI6 drought events, weighted by how severe the stress conditions were. Higher values indicate crops sustained better health under equivalent stress. Grey districts recorded no drought that year.",
       # "flood_resistance": "Vegetation Flood Resistance measures how well cropland vegetation maintained healthy VCI during flood events, weighted by how severe the stress conditions were. Higher values indicate crops sustained better health under equivalent stress. Grey districts recorded no flood that year.",
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
        #"spei24": "SPEI-24 reveals long-term (2-year) drought trends, indicating persistent structural water deficits that threaten multi-season food production.",
    }

    return html.Div([
        city_selector(selected_city='hanoi', visible=False),
        dcc.Store(id="climate-indicator-descriptions", data=indicator_descriptions),
        html.Script(f"window.quarterLookup = {json.dumps(all_quarters)};"),


        html.Div([sidebar], style={
            "width": "15%",
            "height": "100%",
            "display": "flex",
            "vertical-align": 'top',
            "flexDirection": "column",
            "justifyContent": "flex-start",
        }),

        # ── Left panel ──────────────────────────────────────────
        html.Div([

            dbc.Card([
                dbc.CardBody([
                    html.H2("Climate Stress Indicators", style=header_style),
                    html.P(
                        "This page provides a multi-dimensional view of climate stress and biophysical shocks across Hanoi's districts and nationally," \
                        "integrating climate resilience for vegetation health in key production areas, water availability trends, and districts most " \
                        "frequently impacted by severe water deficits. "
                        "Select an indicator below to explore how different aspects of climate have evolved over time. ",
                        style={
                            "margin": "10px 6px",
                            "fontSize": 'clamp(0.6em, 0.9em, 1.0em)',
                            #"textAlign": "justify",
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

                    # Indciator description card, updated dynamically based on selection, with initial content for VCI
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
                    })
                    ,
                    # (removed horizontal colorbar placeholder — colorbar is now on the map)
                ])
            ], style={
                "height": "auto", "padding": "6px", "marginBottom": "10px",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                "backgroundColor": brand_colors['White'], "borderRadius": "10px",
                "zIndex": "2000", "position": "relative"
            }),

            # ── Date slider (VCI + other monthly indicators) ──────────────────
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

            # EMDAT natural disasters summary (bottom of left panel)
            dbc.Card([
                dbc.CardBody([
                    html.H6("EMDAT Natural Disasters (2000-2026)", style={"marginBottom": "6px", "fontSize": "0.9em", "fontWeight": "bold"}),
                    html.Div("Summary of natural disaster events and total affected (source: EMDAT)", style={"fontSize": "0.8em", "color": "#444", "marginBottom": "6px"}),
                    dcc.Graph(
                        id='resilience-emdat-graph',
                        config={"displayModeBar": False},
                        style={"flex": "1 1 auto", "minHeight": "0", "height": "600px", "width": "100%"}
                    )
                ], style={"display": "flex", "flexDirection": "column", "flex": "1 1 auto", "minHeight": "0"})
            ], style={
                "height": "auto",
                "padding": "6px",
                "marginTop": "10px",
                "box-shadow": "0 2px 6px rgba(0,0,0,0.08)",
                "backgroundColor": brand_colors['White'],
                "border-radius": "10px",
                "display": "flex",
                "flexDirection": "column"
            }),

        ], style={
            "width": "min(40%)", "height": "100%", "padding": "10px",
            "backgroundColor": brand_colors['Light green'], "borderRadius": "0", "margin": "0",
            "display": "flex", "flexDirection": "column", "justifyContent": "flex-start",
            "overflowY": "auto", "boxSizing": "border-box", "position": "relative",
        }),

        # ── Right panel: map ─────────────────────────────────────
        html.Div(
            dcc.Loading(
                id="loading-drought-map",
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
                    id="drought-map-container",
                    style={"height": "100%", "width": "100%"},
                ),
            ),
            style={"flex": "1", "height": "100%", "minHeight": "calc(100vh - 140px)"}
        ),


    ], style={"display": "flex", "width": "100vw", "height": "100%"})