import dash_bootstrap_components as dbc
from dash import html, dcc

# Your brand colors (import or redefine)
brand_colors = {
    'Black': '#333333',
    "Brown": "#313715",
    "Red": "#A80050",
    "Dark green": "#939f5c",
    "Mid green": "#bbce8a",
    "Light green": "#E8F0DA",
    "White": "#ffffff"  
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
                "height": "auto",
            }

def create_nutrition_kpi_card(outcome_name, addis_value, national_value, lower_is_better=True):
    """
    Create a KPI card comparing Addis Ababa vs National nutrition outcomes.
    
    Parameters:
    - outcome_name: Name of the nutrition indicator
    - addis_value: Percentage value for Addis Ababa
    - national_value: Percentage value for National
    - lower_is_better: True if lower values are better (default), False otherwise
    """
    difference = addis_value - national_value
    
    # Determine if Addis is performing better or worse
    if lower_is_better:
        is_better = difference < 0
    else:
        is_better = difference > 0
    
    # Set colors and symbols based on performance
    if is_better:
        color = brand_colors['Dark green']
        arrow = "↓" if lower_is_better else "↑"
        status_text = "better"
    else:
        color = brand_colors['Red']
        arrow = "↑" if lower_is_better else "↓"
        status_text = "worse"
    
    return dbc.Card([
        dbc.CardBody([
            html.H5(outcome_name, style={
                "fontWeight": "bold",
                "fontSize": "1em",
                "color": brand_colors['Brown'],
                "marginBottom": "10px"
            }),
            
            # Addis Value
            html.Div([
                html.Span("Addis Ababa: ", style={"fontSize": "0.9em", "color": "#666"}),
                html.Span(f"{addis_value}%", style={
                    "fontSize": "1.5em",
                    "fontWeight": "bold",
                    "color": color
                })
            ], style={"marginBottom": "5px"}),
            
            # National Value
            html.Div([
                html.Span("National: ", style={"fontSize": "0.9em", "color": "#666"}),
                html.Span(f"{national_value}%", style={
                    "fontSize": "1.5em",
                    "fontWeight": "bold",
                    "color": "#999"
                })
            ], style={"marginBottom": "10px"}),
            
            # Difference indicator
            html.Div([
                html.Span(f"{arrow} ", style={"fontSize": "1.5em", "color": color}),
                html.Span(f"{abs(difference):.1f}%", style={
                    "fontSize": "1.2em",
                    "fontWeight": "bold",
                    "color": color
                }),
                html.Span(f" {status_text}", style={
                    "fontSize": "0.8em", 
                    "color": "#666", 
                    "marginLeft": "5px"
                })
            ])
        ])
    ], style=kpi_card_style_2)



def create_nutrition_kpi_card_hanoi(timeseries, outcome_name, hanoi_value, national_value, lower_is_better=True):
    import plotly.graph_objects as go
    
    """
    Create a KPI card comparing Hanoi vs National nutrition outcomes.
    
    Parameters:
    - outcome_name: Name of the nutrition indicator
    - hanoi_value: Percentage value for Hanoi
    - national_value: Percentage value for National
    - lower_is_better: True if lower values are better (default), False otherwise
    """
    difference = hanoi_value - national_value
    
    # Determine if Hanoi is performing better or worse
    if lower_is_better:
        is_better = difference < 0
    else:
        is_better = difference > 0

    # Set colors and symbols based on performance
    if is_better:
        color = brand_colors['Dark green']
        arrow = "↓" if lower_is_better else "↑"
        status_text = "better"
    else:
        color = brand_colors['Red']
        arrow = "↑" if lower_is_better else "↓"
        status_text = "worse"

    sparkline = go.Figure()

    timeseries = timeseries.interpolate().dropna()  # Ensure we have a continuous line for the sparkline

    sparkline.add_trace(go.Scatter(
        x=timeseries['Year'], y=timeseries['value'],
        mode="lines",
        marker={    "size": 5,
                    "symbol": "circle",
                    "color": color,
                    "line": {"color": color, "width": 1.5}
                },
        hovertemplate="%{x}: %{y:.1f}<extra></extra>"
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
            html.H5(outcome_name, style={
                "fontWeight": "bold",
                "fontSize": "1em",
                "color": brand_colors['Brown'],
                "marginBottom": "10px"
            }),
            
            # Addis Value
            html.Div([
                html.Span("Hanoi: ", style={"fontSize": "0.9em", "color": "#666"}),
                html.Span(f"{hanoi_value}%", style={
                    "fontSize": "1.5em",
                    "fontWeight": "bold",
                    "color": color
                })
            ], style={"marginBottom": "5px"}),
            
            # National Value
            html.Div([
                html.Span("National: ", style={"fontSize": "0.9em", "color": "#666"}),
                html.Span(f"{national_value}%", style={
                    "fontSize": "1.5em",
                    "fontWeight": "bold",
                    "color": "#999"
                })
            ], style={"marginBottom": "10px"}),
            
            # Difference indicator
            html.Div([
                html.Span(f"{arrow} ", style={"fontSize": "1.5em", "color": color}),
                html.Span(f"{abs(difference):.1f}%", style={
                    "fontSize": "1.2em",
                    "fontWeight": "bold",
                    "color": color
                }),
                html.Span(f" {status_text}", style={
                    "fontSize": "0.8em", 
                    "color": "#666", 
                    "marginLeft": "5px"
                })
            ]),

            html.Div([
            dcc.Graph(
                    figure=sparkline,
                    config={"displayModeBar": False},
                    style={"height": "80px", "width": "60%"},
                ),
            ], style={"marginTop": "10px", "display": "flex", "justifyContent": "center"})

        ])
    ], style=kpi_card_style_2)

