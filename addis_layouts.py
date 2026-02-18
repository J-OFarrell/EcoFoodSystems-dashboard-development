"""
Addis Ababa dashboard tab layouts
"""

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px

from config import brand_colors, header_style, kpi_card_style_2, card_style
from shared_components import sidebar, city_selector
from dashboard_components import create_nutrition_kpi_card


def stakeholders_tab_layout():
    """Addis Ababa stakeholders tab layout"""
    # Import data at runtime to avoid circular imports
    import app as main
    df_sh = main.df_sh
    
    return html.Div([
        city_selector(selected_city='addis', visible=False),  # Hidden but present for callback
        
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
                        id='sh_table',
                        data=df_sh.to_dict('records'),
                        columns=[
                            {"name": str(i), "id": str(i), "presentation": "markdown"} if i == "Website" else {"name": str(i), "id": str(i)}
                            for i in df_sh.columns
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
                                    'value': str(row[col]) if (col.lower() == 'description' or len(str(row[col])) > 120) else '',
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
                            'overflowX': 'scroll',
                            'overflowY': 'auto',
                            'height': '100%'
                        },
                        style_as_list_view=True
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
    """Addis Ababa supply tab layout"""
    return html.Div([
        city_selector(selected_city='addis', visible=False),  # Hidden but present for callback
        
            html.Div([sidebar], style={
                                "width": "15%",
                                "height": "100%",
                                "display": "flex",
                                "vertical-align":'top',
                                "flexDirection": "column",
                                "justifyContent": "flex-start"}),

            # Left Panel
            html.Div([

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
                "flex": "0 0 20%",
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
    """Addis Ababa poverty tab layout"""
    import app as main
    variables = main.variables
    
    return html.Div([
        city_selector(selected_city='addis', visible=False),  # Hidden but present for callback
        
        html.Div([sidebar], style={
                                        "width": "15%",
                                        "height": "100%",
                                        "display": "flex",
                                        "vertical-align":'top',
                                        "flexDirection": "column",
                                        "justifyContent": "flex-start",}),

        # Left Panel: text, dropdown, bar chart
        html.Div([
        dbc.Card([
                dbc.CardBody([
                    html.H2("Multidimensional Poverty Index", style=header_style),
                    html.P("The Multidimensional Poverty Index (MPI) assesses poverty across health, education, and living standards using ten indicators including nutrition, schooling, sanitation, water, electricity, and housing. This spatial analysis maps deprivation levels across Addis Ababa's sub-cities, revealing where households face multiple overlapping disadvantages. These insights identify priority areas for targeted interventions, supporting equitable resource allocation and sustainable poverty reduction strategies aligned with SDG goals.",
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
                            })
                            ],style={
                                        "display": "flex",
                                        "flexDirection": "column",
                                        "height": "100%"             
                                    })
                    ], style={
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


def affordability_tab_layout():
    """Addis Ababa affordability tab layout"""
    import app as main
    outlets_geojson_files = main.outlets_geojson_files_addis
    data_labels_food_env = main.data_labels_food_env
    cols_food_env = main.cols_food_env
    
    return html.Div([
        city_selector(selected_city='addis', visible=False),  # Hidden but present for callback
        
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
                            html.P("This map shows the distribution of healthy and unhealthy food outlets across Addis Ababa's sub-cities. The obesogenic ratio reveals where unhealthy outlets dominate, indicating areas with limited access to nutritious food. Population exposure metrics highlight which communities face the greatest imbalance, providing evidence to guide equitable food policy interventions. This analysis forms part of a broader assessment integrating socioeconomic and built environment factors.",
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
                                    id="outlets-layer-select",
                                    options=[{"label": f.split('_')[1] if len(f.split('_')) < 4 else f"{f.split('_')[1]} {f.split('_')[2]}", 
                                            "value": f} for f in outlets_geojson_files],
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

                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                                html.P(["Select a food environment metric to display as a choropleth layer."],                                    
                                       style={   "margin": "6px", 
                                                'fontSize': 'clamp(0.7em, 1em, 1.0em)',
                                                "textAlign": "center",
                                                "whiteSpace": "normal",
                                                "fontStyle": "italic"
                                                }),
                                dcc.Dropdown(
                                    id="choropleth-select",
                                    options=[{"label": label, "value": col} 
                                            for label, col in zip(data_labels_food_env, cols_food_env)],
                                    multi=False,
                                    value='ratio_obesogenic',
                                    placeholder="Select metric to display",
                                    style={'zIndex': '1900'})
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
                            "border-radius": "10px"}),
                
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
                        id='affordability-map',
                        figure=go.Figure().update_layout(
                            mapbox=dict(style="carto-positron", center={"lat": 9.1, "lon": 38.7}, zoom=10),
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


def sustainability_tab_layout():
    """Addis Ababa sustainability tab layout"""
    import app as main
    df_indicators = main.df_indicators
    
    display_cols = ['Dimensions', 'Components', 'Indicators', 'SDG impact area/target', 'SDG Numbers']
    df_display = df_indicators[display_cols]
    
    return html.Div([
        city_selector(selected_city='addis', visible=False),  # Hidden but present for callback
        
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
                                column: {'value': str(row[column]), 'type': 'text'}
                                for column in display_cols
                            } for row in df_display.to_dict('records')
                        ],
                        tooltip_duration=None,
                        css=[{
                            'selector': '.dash-table-tooltip',
                            'rule': 'background-color: ' + brand_colors['Light green'] + '; color: ' + brand_colors['Black'] + '; border: 2px solid ' + brand_colors['Dark green'] + '; padding: 6px; font-size: 14px; box-shadow: 0 4px 8px ' + brand_colors['Black'] + ';'
                        }],
                        style_table={
                            'overflowX': 'auto',
                            'width': '100%',
                        }
                    )
                ], style={"height": "100%", "display": "flex", "flexDirection": "column", "overflowY": "auto"})
            ], style={
                "height": "auto",
                "overflowY":"auto",
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


def policies_tab_layout():
    """Addis Ababa policies tab layout"""
    import app as main
    df_policies = main.df_policies
    
    return html.Div([
        city_selector(selected_city='addis', visible=False),  # Hidden but present for callback
        
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
                            {"name": str(col), "id": str(col)}
                            for col in df_policies.columns
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
                        style_table={
                            'overflowX': 'auto',
                            'width': '100%',
                        }
                    )
                ], style={"height": "100%", "display": "flex", "flexDirection": "column"})
            ], style={
                "height": "auto",
                "overflowY":"auto",
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
            "overflow": 'hidden',
            "border-radius": "10px",
            'margin': "10px 10px 10px 10px"
        })
    ], style={
        "display": "flex",
        "width": "100%",
        "height": "100%",
        "backgroundColor": brand_colors['Light green']
    })


def health_nutrition_tab_layout():
    """Addis Ababa health & nutrition tab layout"""
    tile_width, lg = 12, 4
    
    return html.Div([
        city_selector(selected_city='addis', visible=False),  # Hidden but present for callback
        
                html.Div([sidebar], style={
                                        "width": "15%",
                                        "height": "100%",
                                        "display": "flex",
                                        "vertical-align":'top',
                                        "flexDirection": "column",
                                        "justifyContent": "flex-start",}),

                # Main content area
                html.Div([
                    # CHILDREN Section (6 cards)
                    html.H3("Children Aged 0-59 Months", style={
                        "color": brand_colors['Brown'],
                        "fontWeight": "bold",
                        "marginTop": "20px",
                        "marginBottom": "15px",
                        "borderBottom": f"3px solid {brand_colors['Mid green']}",
                        "paddingBottom": "10px"
                    }),
                    dbc.Row([
                        dbc.Col([create_nutrition_kpi_card("Stunting", 13.9, 40.9, lower_is_better=True)], width=tile_width, lg=lg),
                        dbc.Col([create_nutrition_kpi_card("Wasting", 3.8, 11.2, lower_is_better=True)], width=tile_width, lg=lg),
                        dbc.Col([create_nutrition_kpi_card("Concurrent Stunting and Wasting", 0.7, 2.9, lower_is_better=True)], width=tile_width, lg=lg),
                        dbc.Col([create_nutrition_kpi_card("Underweight", 5.5, 23.3, lower_is_better=True)], width=tile_width, lg=lg),
                        dbc.Col([create_nutrition_kpi_card("Overweight", 6.9, 3.9, lower_is_better=True)], width=tile_width, lg=lg),
                        dbc.Col([create_nutrition_kpi_card("Malnutrition", 21.9, 51.5, lower_is_better=True)], width=tile_width, lg=lg),
                    ]),

                    # ADOLESCENT GIRLS Section (4 cards)
                    html.H3("Adolescent Girls (10-19 Years)", style={
                        "color": brand_colors['Brown'],
                        "fontWeight": "bold",
                        "marginTop": "30px",
                        "marginBottom": "15px",
                        "borderBottom": f"3px solid {brand_colors['Mid green']}",
                        "paddingBottom": "10px"
                    }),
                    dbc.Row([
                        dbc.Col([create_nutrition_kpi_card("Underweight (BMI)", 5.3, 9.3, lower_is_better=True)], width=tile_width, lg=lg),
                        dbc.Col([create_nutrition_kpi_card("Overweight (BMI)", 12.5, 5.1, lower_is_better=True)], width=tile_width, lg=lg),
                        dbc.Col([create_nutrition_kpi_card("Obese (BMI)", 3.5, 1, lower_is_better=True)], width=tile_width, lg=lg),
                    ]),
                    
                    # WOMEN Section (2 cards)
                    html.H3("Women (15-49 Years)", style={
                        "color": brand_colors['Brown'],
                        "fontWeight": "bold",
                        "marginTop": "30px",
                        "marginBottom": "15px",
                        "borderBottom": f"3px solid {brand_colors['Mid green']}",
                        "paddingBottom": "10px"
                    }),
                    dbc.Row([
                        dbc.Col([create_nutrition_kpi_card("Underweight", 10.7, 20.1, lower_is_better=True)], width=tile_width, lg=lg),
                        dbc.Col([create_nutrition_kpi_card("Overweight", 35.8, 11.4, lower_is_better=True)], width=tile_width, lg=lg),
                    ]),
                ], style={  "overflowY": "auto",
                            "flex": "1 1 85%",
                            "padding": "10px",
                            "backgroundColor": brand_colors['Light green']})
    
        ], style={
                    "display": "flex", 
                    "width": "100%", 
                    "height": "100%",
                    "backgroundColor": brand_colors['Light green']
        })


def footprints_tab_layout():
    """Addis Ababa environmental footprints tab layout"""
    import app as main
    df_lca = main.df_lca
    
    return html.Div([
        city_selector(selected_city='addis', visible=False),  # Hidden but present for callback
        
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
            # Dropdown card to select food group
            dbc.Card([
                dbc.CardBody([
                    html.H5("Select Food Group:", style={
                        "fontSize": "clamp(0.9em, 1.1vw, 1.2em)",
                        "marginBottom": "10px",
                        "color": brand_colors['Brown']
                    }),
                    dcc.Dropdown(
                        id='food-group-select',
                        options=[
                            {'label': group.split('-')[1] if '-' in group else group, 'value': group}
                            for group in sorted(df_lca['Food Group'].dropna().unique())
                        ],
                        value=sorted(df_lca['Food Group'].dropna().unique())[0],
                        clearable=False,
                        style={"fontSize": "clamp(0.8em, 1vw, 1.1em)"}
                    )
                ])
            ], style={
                "marginBottom": "20px",
                "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                "backgroundColor": brand_colors['White'],
                "border-radius": "10px",
                "padding": "10px"
            }),
            
            # Container for food item cards (populated by callback)
            html.Div(id='food-items-container', style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fill, minmax(300px, 1fr))",
                "gap": "15px",
                "width": "100%"
            }),

        ], style={
            "flex": "1 1 85%",
            "overflowY":'auto',
            "padding": "20px",
            "display": "flex",
            "flexDirection": "column"
        })
        
    ], style={
        "display": "flex",
        "width": "100%",
        "height": "100%",
        "backgroundColor": brand_colors['Light green']
    })
