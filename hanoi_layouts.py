"""
Hà Nội dashboard tab layouts
"""

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px

from config import brand_colors, header_style, kpi_card_style_2, card_style
from shared_components import sidebar, city_selector


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
                        page_size=13,
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
                                    'value': str(row[col]) if (col.lower() == 'description' or len(str(row[col])) > 60) else '',
                                    'type': 'text'
                                }
                                for col in df_sh_hanoi.columns
                            } for row in df_sh_hanoi.to_dict('records')
                        ],
                        tooltip_duration=4000,
                        css=[{
                            'selector': '.dash-table-tooltip',
                            'rule': 'position: fixed !important; background-color: ' + brand_colors['Light green'] + '; color: ' + brand_colors['Black'] + '; border: 2px solid ' + brand_colors['Dark green'] + '; padding: 6px; font-size: 14px; box-shadow: 0 4px 8px ' + brand_colors['Black'] + ';'
                        }],
                        style_table={
                            'overflowX': 'scroll',
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
            "width":"80%",
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
    variables_hanoi = main.variables_hanoi
    
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
                            id='variable-dropdown-hanoi',
                            options=[{'label': v, 'value': v} for v in variables_hanoi],
                            value=variables_hanoi[0],
                            style={"margin-bottom": "20px"}
                        ),

                        dcc.Graph(id='bar-plot-hanoi',
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

        # Right panel: map
        html.Div([
            dcc.Graph(
                id='map-hanoi',
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
        "height": "100%"
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

        # Left panel
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
                            id='health-filter-dropdown-hanoi',
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
                    dcc.Graph(id='health-trend-hanoi', 
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
        }),

        # Right panel
        html.Div([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='diet-dumbbell-hanoi', style={
                        "flex": "1 1 90vh",
                        "height":"82vh",
                        'padding': '2px',
                        'margin': '0',
                        "border-radius": "8px",
                        "box-shadow": "0 2px 8px rgba(0,0,0,0.15)",
                    }),

                    html.Div([dcc.Slider(
                        id='dumbbell-slider-hanoi', min=2010, max=2023, value=2013, step=2,
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


def hanoi_affordability_tab_layout():
    """Hanoi affordability tab layout"""
    import app as main
    outlets_geojson_files_hanoi = main.outlets_geojson_files_hanoi
    
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
                                                "fontSize": 'clamp(0.7em, 1em, 1.0em)',
                                                "textAlign": "justify",
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

                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                                html.P(["Select food outlet layers to display on the map."],                                    
                                       style={   "margin": "6px", 
                                                'fontSize': 'clamp(0.7em, 1em, 1.0em)',
                                                "textAlign": "center",
                                                "whiteSpace": "normal",
                                                "fontStyle": "italic"
                                                }),
                                dcc.Dropdown(
                                    id="outlets-layer-select-hanoi",
                                    options=[{"label": f.split('_')[1] if len(f.split('_')) < 4 else f"{f.split('_')[1]} {f.split('_')[2]}", 
                                            "value": f} for f in outlets_geojson_files_hanoi],
                                    value=None,  # Default selection
                                    multi=True,
                                    placeholder="Select outlet layers to display",
                                    style={'zIndex': '2000'})
                                ],
                                style={
                                    'margin': '2px 0px',
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
                            "border-radius": "10px",
                            "zIndex": "2000",
                            "position": "relative"}),
                
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
                    dcc.Graph(
                        id='affordability-map-hanoi',
                        figure=go.Figure().update_layout(
                            mapbox=dict(style="carto-positron", center={"lat": 21.0, "lon": 105.85}, zoom=9),
                            margin=dict(l=0, r=0, t=0, b=0),
                            paper_bgcolor=brand_colors['White']
                        ),
                        style={"height": "100%", "width": "100%", "padding": "0", "margin": "0"}
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
