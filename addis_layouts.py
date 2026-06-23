"""
Addis Ababa dashboard tab layouts
"""

import os
import pandas as pd
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px

from config import brand_colors, header_style, sub_header_style, kpi_card_style_2, card_style, hero_gradient, sidebar_colors
from shared_components import sidebar_addis as sidebar, sidebar_addis_vendor, city_selector
from dashboard_components import create_nutrition_kpi_card, create_price_volatility_kpi_card


_BASEMAP_TILE = [
{
    "below":"traces",
    "sourcetype":"raster",
    "source":[
        "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
    ]
}
]


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


def governance_stakeholders_tab_layout():
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
                            'minWidth': '200px',
                            'width': '200px',
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
                                    'value': str(row[col]) if (col.lower() == 'description' or len(str(row[col])) > 49) else '',
                                    'type': 'text'
                                }
                                for col in df_sh.columns
                            } for row in df_sh.to_dict('records')
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
                            'height': '100%',
                            'width': '100%',
                            'overflowY': 'auto'
                        },
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
        "backgroundColor": brand_colors['Teal']
    })


def storage_distribution_tab_layout():
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



                        _red_graph_loading(
                            dcc.Graph(id="urban-indicator", style={"height": "clamp(80px, 10vh, 200px)"}, config={"displayModeBar": False}),
                            loading_id="loading-urban-indicator-addis",
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

            # Sankey + Slider + Footnote (right)
            html.Div([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            _red_graph_loading(
                                dcc.Graph(
                                    id="sankey-graph", 
                                    style={"width": "100%", "height":"70vh"}  
                                ),
                                loading_id="loading-sankey-graph-addis",
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
                "backgroundColor": brand_colors['Teal'],
                "marginBottom": "auto" 
            }),
        ], style={
                    "display": "flex", 
                    "width": "100%", 
                    "height": "100%",
                    "backgroundColor": brand_colors['Teal']
        })


    # Backward-compatible aliases for existing imports/callbacks.
    stakeholders_tab_layout = governance_stakeholders_tab_layout
    supply_tab_layout = storage_distribution_tab_layout
    poverty_tab_layout = livelihoods_poverty_equity_tab_layout
    sustainability_tab_layout = fcd_indicator_atlas_tab_layout
    policies_tab_layout = governance_policies_tab_layout
    health_nutrition_tab_layout = diets_nutrition_health_tab_layout
    footprints_tab_layout = environment_footprints_tab_layout
    addis_resilience_tab_layout = resilience_tab_layout
    food_env_tab_layout = food_accessibility_vendor_properties_tab_layout


def livelihoods_poverty_equity_tab_layout():
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
                    html.H2("Livelihoods, Poverty, and Equity", style=header_style),
                    html.H4("Multidimensional Poverty Index", style={**header_style, "fontSize": "16px", "margin": "10px"}),
                    html.Hr(style={"borderTop": f"2px solid {brand_colors['Teal']}", "margin": "6px 0"}),
                    html.P("The Multidimensional Poverty Index (MPI) assesses poverty across health, education, and living standards using ten indicators including nutrition, schooling, sanitation, water, electricity, and housing. This spatial analysis maps deprivation levels across Addis Ababa's sub-cities, revealing where households face multiple overlapping disadvantages. These insights identify priority areas for targeted interventions, supporting equitable resource allocation and sustainable poverty reduction strategies aligned with SDG goals.",
                            style={  "margin": "10px 6px", 
                                    "fontSize": "14px",
                                    "textAlign": "justify",
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
                        id='variable-dropdown',
                        options=[{'label': v, 'value': v} for v in variables],
                        value=variables[0],
                        persistence=True,
                        persistence_type='session',
                        style={"margin-bottom": "12px"}
                    ),

                    _red_graph_loading(
                        dcc.Graph(id='bar-plot-addis',
                                config={"displayModeBar": False, "responsive": True},
                                style={
                                    "minHeight": 0,
                                    "width": "100%",
                                    "flex": "1 1 auto",
                                    'padding': '4px',
                                    'margin': '8px',
                                    "border-radius": "8px",
                                    #"box-shadow": "0 2px 8px rgba(0,0,0,0.15)",
                                    "overflowY": "auto"
                                }),
                        loading_id="loading-bar-plot-addis",
                    )
                            ],style={
                                        "display": "flex",
                                        "flexDirection": "column",
                                        "flex": "1 1 auto",
                                        "minHeight": 0,
                                        "overflow": "hidden"
                                    })
                    ], style={
                                "flex": "1 1 auto",
                                "padding":"6px" ,
                                #"box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                                "backgroundColor": brand_colors['White'],
                                "border-radius": "10px",
                                "overflow": "hidden",
                                "display": "flex",
                                "flexDirection": "column"
                    }),

                    ], style={
                        "height": "100%",
                        "backgroundColor": brand_colors['Light Teal'],
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
        "backgroundColor": brand_colors['Light Teal']
        }),

        # Right panel: map, full height
        html.Div([
            _red_graph_loading(
                dcc.Graph(
                    id='addis-mpi-map',
                    config={"displayModeBar": False, "scrollZoom": True, "responsive": True},
                    style={"height": "100%",
                           "width": "100%",
                           "padding": "0",
                           "margin": "0"}),
                loading_id="loading-map-addis",
            )
        ], style={
            "flex": "1",
            "height": "100%",
            "padding": "0",
            "margin": "0",
            "backgroundColor": brand_colors['Light Teal'],
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
        "height": "100vh",
        "backgroundColor": brand_colors['Teal'],
    })


def sdg_indicator_atlas_tab_layout():

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
                                col: {
                                    'value': str(row[col]) if (col.lower() in ['abstract', 'title', 'keywords'] or len(str(row[col])) > 40) else '',
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
                        }
                    ,
                        style_as_list_view=True
                    )
                ], style={"height": "100%", "display": "flex", "flexDirection": "column", "overflowY": "auto", "overflowX": "auto"})
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
        "backgroundColor": brand_colors['Teal']
    })


def governance_policies_tab_layout():
    """Addis Ababa policies tab layout"""
    import app as main
    df_policies = main.df_policies_addis
    df_policies = df_policies[['ID', 'Document URL', 'Title', 'Date of original text', 'Language of document',
        'Primary subjects', 'Domain',
        'Last amended date', 'Available website',
        'Country/Territory', 'Regional organizations',
        'Territorial subdivision', 'Type of text', 'Repealed', 
        'Abstract','Keywords']]
    
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
            _build_policy_documents_content(df_policies, table_id='policies_table'),
        ], style={
            "flex": "1 1 85%",
            "height": "96vh",
            "display": "flex",
            "flexDirection": "column",
            "overflow": "hidden",
            "border-radius": "10px",
            'margin': "10px 10px 10px 10px"
        })
    ], style={
        "display": "flex",
        "width": "100%",
        "height": "100vh",
        "backgroundColor": brand_colors['Teal']
    })


def _build_policy_documents_content(df_policies, table_id='policies_table'):
    return dbc.Card([
        dbc.CardHeader(html.H3("Food System Policies Database", style=header_style)),
        dbc.CardBody([
            dash_table.DataTable(
                id=table_id,
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
                style_cell_conditional=[
                            {
                                'if': {'column_id': 'Title'},
                                'width': '30vw',
                                'minWidth': '30vw',
                                'maxWidth': '30vw'
                            }
                        ], 
                style_header={
                    'fontWeight': 'bold',
                    'backgroundColor': hero_gradient['50%'],
                    'color': 'white',
                    'textAlign': 'center',
                    'fontSize': 'clamp(0.8em, 1vw, 1.1em)'
                },
                style_filter={
                    'backgroundColor': sidebar_colors['Hover (dark card)'],
                    'fontSize': 'clamp(0.64em, 0.85vw, 0.9em)',
                    'padding': '5px 6px'
                },
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'}
                ],
                tooltip_data=[
                    {
                        col: {
                            'value': str(row[col]) if (col.lower() == 'description' or len(str(row[col])) > 40) else '',
                            'type': 'text'
                        }
                        for col in df_policies.columns
                    } for row in df_policies.to_dict('records')
                ],
                tooltip_duration=4000,
                css=[
                    {
                        'selector': '.dash-table-tooltip',
                        'rule': 'position: fixed !important; background-color: ' + sidebar_colors['Hover (dark card)'] + '; color: ' + brand_colors['Black'] + '; border: 2px solid ' + hero_gradient['0%'] + '; padding: 6px; font-size: 14px; box-shadow: 0 4px 8px ' + brand_colors['Black'] + ';'
                    },
                    {
                        'selector': '.dash-table-container .dash-spreadsheet-container',
                        'rule': 'overflow-x: scroll !important; scrollbar-width: auto;'
                    },
                    {
                        'selector': '.dash-table-container .dash-spreadsheet-container::-webkit-scrollbar',
                        'rule': 'height: 14px; width: 24px; -webkit-appearance: none;'
                    },
                    {
                        'selector': '.dash-table-container .dash-spreadsheet-container::-webkit-scrollbar-track',
                        'rule': 'background: #f0f0f0; border-radius: 8px;'
                    },
                    {
                        'selector': '.dash-table-container .dash-spreadsheet-container::-webkit-scrollbar-thumb',
                        'rule': 'background: ' + hero_gradient['0%'] + '; border-radius: 8px; border: 2px solid #f0f0f0;'
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
        ], style={"flex": "1", "display": "flex", "flexDirection": "column", "minHeight": "0"})
    ], style={
        "height": "100%",
        "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
        "backgroundColor": brand_colors['White'],
        "border-radius": "10px",
        "padding": "10px",
        "display": "flex",
        "flexDirection": "column"
    })


def _build_socio_economic_shocks_content(df_volatility, df_ufpri):
    if df_volatility.empty or df_ufpri.empty:
        return html.Div("No price volatility or UFPRI data available.", style={"color": "#999"})

    commodities = sorted(df_volatility['commodity'].unique())
    kpi_cards = []
    for commodity in commodities:
        commodity_vol_data = df_volatility[df_volatility['commodity'] == commodity].copy()
        commodity_vol_data = commodity_vol_data.sort_values('date')
        commodity_ufpri = df_ufpri[df_ufpri['commodity'] == commodity]

        if commodity_vol_data.empty or commodity_ufpri.empty:
            continue

        current_volatility = commodity_vol_data['rolling_volatility'].iloc[-1]
        ufpri_score = commodity_ufpri['ufpri_score'].iloc[0]
        shock_frequency = commodity_ufpri['shock_frequency'].iloc[0]

        kpi_card = create_price_volatility_kpi_card(
            commodity_vol_data[['date', 'rolling_volatility']],
            commodity,
            current_volatility,
            ufpri_score,
            shock_frequency
        )
        kpi_cards.append(dbc.Col([kpi_card], width=12, lg=3))

    return html.Div([
        dbc.Row(kpi_cards) if kpi_cards else html.Div("No price volatility or UFPRI data available.", style={"color": "#999"}),
    ])


def render_addis_resilience_view(selected_view='Socio-Economic Shocks'):
    import app as main

    if selected_view == 'Socio-Economic Shocks':

        volatility_csv_path = os.path.join(
            os.path.dirname(__file__),
            'assets/data/addis/resilience/addis_rolling_price_volatility.csv'
        )
        ufpri_csv_path = os.path.join(
            os.path.dirname(__file__),
            'assets/data/addis/resilience/addis_ufpri_scores.csv'
        )

        try:
            df_volatility = pd.read_csv(volatility_csv_path)
        except Exception:
            df_volatility = pd.DataFrame()

        try:
            df_ufpri = pd.read_csv(ufpri_csv_path)
        except Exception:
            df_ufpri = pd.DataFrame()

        return _build_socio_economic_shocks_content(df_volatility, df_ufpri)


def diets_nutrition_health_tab_layout(selected_city='addis'):
    """Addis Ababa health & nutrition tab layout"""
    tile_width, lg = 12, 4
    
    return html.Div([
        city_selector(selected_city=selected_city, visible=False),  # Hidden but present for callback
        
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
                            "marginLeft": "14px",
                            "padding": "10px",
                            "backgroundColor": brand_colors['White']})
    
        ], style={
                    "display": "flex", 
                    "width": "100%", 
                    "height": "100%",
                    "backgroundColor": brand_colors['Teal']
        })


def environment_footprints_tab_layout(selected_city='addis'):
    """Addis Ababa processing and packing (LCA) tab layout"""
    import app as main
    df_lca = main.df_lca
    
    return html.Div([
        city_selector(selected_city=selected_city, visible=False),  # Hidden but present for callback
        
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
        "backgroundColor": brand_colors['Teal']
    })


def resilience_tab_layout(selected_city='addis', default_view='Socio-Economic Shocks'):
    """Addis Ababa resilience tab layout with Socio-Economic Shocks (price volatility)"""
    selected_view = default_view or 'Socio-Economic Shocks'
    
    # Define resilience view options
    view_options = [
        'Socio-Economic Shocks',
        #'Biophysical Shocks (coming soon)',
        'Resilience Indicator Trends (coming soon)',
    ]
    
    return html.Div([
        city_selector(selected_city=selected_city, visible=False),
        
        html.Div([sidebar], style={
            "width": "15%",
            "height": "100%",
            "display": "flex",
            "vertical-align": 'top',
            "flexDirection": "column",
            "justifyContent": "flex-start",
        }),
        
        # Content area with dropdown and KPI cards
        html.Div([
            dbc.CardHeader(
                dcc.Dropdown(
                    id="addis-resilience-view-select",
                    options=[
                        {"label": opt, "value": opt, "disabled": "(coming soon)" in opt}
                        for opt in view_options
                    ],
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
            
            # KPI cards container for Socio-Economic Shocks view
            html.Div(
                id="addis-resilience-view-container",
                children=render_addis_resilience_view(selected_view),
                style={"flex": "1", "display": "flex", "minHeight": 0, "flexDirection": "column", "overflowY": "auto"}
            ),
        ], style={
            "flex": "1", "height": "100%", "display": "flex", "flexDirection": "column",
            "backgroundColor": brand_colors['Teal'], "padding": "10px",
            "overflowY": "auto", "boxSizing": "border-box",
        }),
        
    ], style={"display": "flex", "width": "100vw", "height": "100%", 'backgroundColor': brand_colors['Teal']})


def food_accessibility_vendor_properties_tab_layout(selected_city='addis'):
    """Addis Ababa accessibility tab layout"""
    import app as main
    outlets_geojson_files = main.outlets_geojson_files_addis
    #data_labels_food_env = main.data_labels_food_env
    #cols_food_env = main.cols_food_env
    #walking_segs = main.walking_segments_addis
    sub_city_level_metrics = main.sub_city_level_metrics
    cols_labels_hex_vars = main.cols_labels_hex_vars

    if selected_city == 'addis':
        cityname = 'Addis Ababa'
    elif selected_city == 'hanoi':
        cityname = 'Hanoi'

    walking = html.Img(src="/assets/data/logos/walking.svg")
    bus = html.Img(src="/assets/data/logos/bus.svg")
    car = html.Img(src="/assets/data/logos/car.svg")
    population_options = getattr(main, "accessibility_population_options_addis", [])
    outlet_options = getattr(main, "accessibility_outlet_options_addis", [])
    population_default = population_options[0]["value"] if population_options else None
    
    return html.Div([
            city_selector(selected_city=selected_city, visible=False),  # Hidden but present for callback
            dcc.Store(id="transport-mode", data="walk"),
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
                            html.H2("Food Vendor Analysis", style={**header_style, "fontSize": "22px", "fontWeight": "700", "color": "#1d574f"}),
                            html.P(f"This map shows a number of urban food vendor metrics across {cityname}'s sub-cities regions. These metrics include food outlet density, and highlights areas accessible through a combination of walking, public transportation or driving to identify areas of the city that have prominent food deserts and swamps. Additional layers can be added to the map using the dropdowns below, such as average land-surface temperature and canopy cover, which are important indicators of urban heat island effects and green space access that can further exacerbate food environment inequities.",
                                       style={  "margin": "10px 6px",
                                                "fontSize": "14px",
                                                "color": "#4B5563",
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
                                "height": "100%",
                                "padding": "14px 24px",
                            })
                ], style={"height": "auto",
                            "padding": "0",
                            "boxShadow": "0 2px 12px rgba(0,0,0,0.08)",
                            "backgroundColor": "#FFFFFF",
                            "borderRadius": "12px",
                            "marginBottom": "16px"}),

                    dbc.Card([
                        dbc.CardBody([
                            html.H3(["Vendor Accessibility Layers"], style={
                                "fontSize": "16px",
                                "fontWeight": "600",
                                "color": "#1d574f",
                                "justifyContent": 'center',
                                "alignItems": 'center',
                                "textAlign": 'center'
                            }),
                            html.Div([
                                html.Div([
                                    html.Div([
                                        dbc.ButtonGroup([
                                                        dbc.Button(
                                                            html.Img(src="/assets/logos/walking.svg", height="28px"),
                                                            id="btn-walk",
                                                            outline=True,
                                                            color="primary",
                                                            n_clicks=0,
                                                            active=True,
                                                        ),
                                                        dbc.Button(
                                                            html.Img(src="/assets/logos/bus.svg", height="28px"),
                                                            id="btn-transit",
                                                            outline=True,
                                                            color="primary",
                                                            n_clicks=0,
                                                        ),
                                                        dbc.Button(
                                                            html.Img(src="/assets/logos/car.svg", height="28px"),
                                                            id="btn-drive",
                                                            outline=True,
                                                            color="primary",
                                                            n_clicks=0,
                                                        ),
                                                    ],
                                                    size="lg")
                                    ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'marginBottom': '15px'}),
                                
                                        dcc.Slider(
                                            id="outlet-travel-time",
                                            min=0,
                                            max=2,
                                            marks={0: "5-minutes", 1: "10-minutes", 2: "15-minutes"},
                                            value=2,
                                            step=None,
                                            tooltip={"always_visible": False},
                                            updatemode="mouseup",
                                            vertical=False,
                                            verticalHeight=300,
                                            included=False,
                                            className="dcc-slider",
                                            persistence=True,
                                            persistence_type="session")],
                                            style={'zIndex': '9000', 'width': '100%', 'margin': '20px 0'}
                                        ),

                                        dcc.Dropdown(
                                            id="food-outlets-isochrones",
                                            options=outlet_options,
                                            value=[],  # Default to empty (no selection)
                                            multi=True,
                                            placeholder="Choose outlet layers by group",
                                            style={'zIndex': '6000'}),
                                    ],
                                    style={
                                        'margin': '2px 0px',
                                        'justifyContent': 'end',
                                        'alignItems': 'center',
                                        'textAlign': 'center',
                                        'zIndex': '6000'
                        })],style={
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "height": "100%",
                                    "padding": "14px 24px",
                                })
                    ], style={"height": "auto",
                                "padding": "0",
                                "boxShadow": "0 2px 12px rgba(0,0,0,0.08)",
                                "backgroundColor": "#FFFFFF",
                                "borderRadius": "12px",
                                "position": "relative",
                                "marginBottom": "16px"}),


                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H3(["Population In Accessibility Zones"], style={"fontSize": "16px", "fontWeight": "600", "color": "#1d574f", 'marginBottom': '5px'}),
                            dcc.Dropdown(
                                id="population-category-select",
                                options=population_options,
                                value=population_default,
                                clearable=False,
                                placeholder="Select a population category",
                                style={'zIndex': '3000'}
                            ),
                            dcc.Graph(
                                id="accessibility-population-bar-chart",
                                config={"displayModeBar": False, "responsive": True},
                                style={"height": "380px", "width": "100%"}
                            ),
                        ], style={
                            'margin': '2px 0px',
                            'justifyContent': 'end',
                            'alignItems': 'center',
                            'textAlign': 'center'
                        })
                    ], style={
                        "display": "flex",
                        "flexDirection": "column",
                        "height": "100%",
                        "padding": "14px 24px",
                    })
                ], style={"height": "auto",
                            "padding": "0",
                            "boxShadow": "0 2px 12px rgba(0,0,0,0.08)",
                            "backgroundColor": "#FFFFFF",
                            "borderRadius": "12px",
                            "marginBottom": "16px"}),


                dbc.Card([
                    dbc.CardBody([
                        html.Div([

                                html.H3(["Contextual Layers"], style={"fontSize": "16px", "fontWeight": "600", "color": "#1d574f", 'marginBottom': '5px'}),
                                dcc.Dropdown(
                                    id="contextual-layer-select",
                                    options=[{"label": label, "value": col} 
                                            for col, label in cols_labels_hex_vars.items()],
                                    multi=False,
                                    value=None,
                                    placeholder="Select contextual layers to display",
                                    style={'zIndex': '6000', 'position': 'relative'})

                            ],
                                style={
                                    'margin': '2px 0px',
                                    'justifyContent': 'end',
                                    'alignItems': 'center',
                                    'textAlign': 'center'
                    })],style={
                                "display": "flex",
                                "flexDirection": "column",
                                "height": "100%",
                                "padding": "14px 24px",
                            })
                ], style={"height": "auto",
                            "padding": "0",
                            "boxShadow": "0 2px 12px rgba(0,0,0,0.08)",
                            "backgroundColor": "#FFFFFF",
                            "borderRadius": "12px",
                            'marginBottom': "16px"}),
                            
                #dbc.Card([
                #    dbc.CardBody([
                #        html.Div([
                #            html.H3(["Administrative Level Summary"], style={**sub_header_style, 'marginBottom': '5px'}),
                #                html.P(["Select a sub-city level summary metric to display."],                                    
                #                       style={   "margin": "6px", 
                #                               'fontSize': 'clamp(0.7em, 1em, 1.0em)',
                #                               "textAlign": "center",
                #                               "whiteSpace": "normal",
                #                               "fontStyle": "italic"
                #                               }),
                #                dcc.Dropdown(
                #                    id="choropleth-select",
                #                    options=[{"label": label, "value": col} 
                #                            for col, label in sub_city_level_metrics.items()],
                #                    multi=False,
                #                    value='average land surface temperature',
                #                    placeholder="Select metric to display",
                #                    style={'zIndex': '1900'})
                #                ],
                #                style={
                #                    'margin': '2px 0px',
                #                    'justifyContent': 'end',
                #                    'alignItems': 'center',
                #                    'textAlign': 'center'
                #                })],style={
                #            "display": "flex",
                #            "flexDirection": "column",
                #            "height": "100%"             
                #            })
                #], style={"height": "auto", 
                #            "padding":"6px" ,
                #            "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                #            "backgroundColor": brand_colors['White'],
                #            "border-radius": "10px"}),
                
            ], style={
                    "width": "min(40%)",
                    "height": "100%",
                    "padding": "10px",
                    "backgroundColor": "#1d574f",
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
                        id="loading-affordability-map-addis",
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
                                id='accessibility-map-addis',
                                figure=go.Figure().update_layout(
                                    mapbox=dict(
                                        style="carto-positron",
                                        center={"lat": 9.0192, "lon": 38.752},
                                        zoom=11
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
                    "backgroundColor": "#1d574f"
        })




# NEW TAB LAYOUTS ==== DRIVERS ===

def environment_climate_change_tab():
    """
    For Hanoi this page contains the Biophysical Shocks view 
    This is not developed for Addis yet!
    For Hanoi, we can ammend the drop-down to just include Biophysical shocks and LULC data
    """
    
    return 'coming-soon'

def income_growth_distribution_tab():
    """Can repurpose MPI tab layout for this and add in any additional indicators available to sub-tabs?"""
    return livelihoods_poverty_equity_tab_layout() 

def policies_leadership_tab():
    """Can repurpose food price resilience indicator tab layout for this piece
    """
    return governance_policies_tab_layout()

def population_growth_migration_tab():
    return 'coming-soon'

def socio_cultural_context_tab():
    return 'coming-soon'

# NEW TAB LAYOUTS ==== FOOD ENVIRONMENTS ====

def food_availability_tab():
    """ Refers to food nutrient availability, not developed yet
    """
    return "coming-soon"

def food_affordability_tab():
    return "coming-soon"

def vendor_properties_tab():
    return food_accessibility_vendor_properties_tab_layout(selected_city='addis')

# NEW TAB LAYOUTS ==== FOOD SUPPLY CHAINS ====

def processing_packing_tab():
    """ For now the only available indicator is the LCA analysis so will use this """
    return environment_footprints_tab_layout()

def production_systems_input_supply_tab():
    return 'coming-soon'

def retail_markerting_tab():
    return 'coming-soon'

def storage_distrbution_tab():
    return 'coming-soon'

# NEW TAB LAYOUTS ==== INDIVIDUAL FACTORS ====

def economic_tab():
    return 'coming-soon'

# NEW TAB LAYOUTS ==== CROSS-CUTTING FACTORS ====

def governance_tab():
    """
    Will need to combine policies and stakeholder database pages, perhaps sub-tab dropdown
    """
    return governance_stakeholders_tab_layout()

def resilience_tab():
    """ Right now the SDG database is the only thing that fits exclusively here"""
    return resilience_tab_layout(selected_city='addis', default_view='Socio-Economic Shocks')
    #return sdg_indicator_atlas_tab_layout()


# NEW TAB LAYOUTS ==== OUTCOMES ====

def food_security_tab():
    return 'coming-soon'

def livelihoods_poverty_equity_tab():
    return livelihoods_poverty_equity_tab_layout()

def noncommunicable_diseases_tab():
    return 'coming-soon'

def nutrional_status_tab():
    return diets_nutrition_health_tab_layout(selected_city='addis')
