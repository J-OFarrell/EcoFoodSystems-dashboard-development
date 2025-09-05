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
from lorem_text import lorem
from dash import Dash, html, dcc, Output, Input, State, callback, dash_table
import dash_bootstrap_components as dbc

import warnings
warnings.filterwarnings("ignore")

app = Dash(__name__, suppress_callback_exceptions=True)

#colors = {
#  'eco_green': '#AFC912',
#  'forest_green': '#4C7A2E',
#  'earth_brown': '#7B5E34',
#  'harvest_yellow': '#F2D16B',
#  'neutral_light': '#F5F5F5',
#  'dark_text': '#333333',
#  'accent_warm': '#E07A5F'
#}

brand_colors = {
    "Medium violet red": "#af245c",
    "Dark khaki": "#aabf7e",
    "Mid khaki": "#c1d88e",
    "Seagreen": "#095d40",
    "Dark slate grey": "#0080a3",
    "White": "#ffffff",
    "Black": "#000000"
}

tabs = [
        'Food Systems Stakeholders',
        'Multidimensional Poverty',
        'Dietry Mapping & Affordability',
        'Health & Nutrition',
        'Food Flows, Supply & Value Chain',
        'Climate Shocks and Resilience'
        ]

tabs_brief = [
        'Stakeholders',
        'Poverty',
        'Affordability',
        'Nutrition',
        'Supply',
        'Shocks'        
]

# -------------------------- Loading and Formatting All Data ------------------------- #

# Loading and Formatting MPI Data
path = "/Users/jemim/app_dev_EFS/assets/data/"
MPI = gpd.read_file(path+"Hanoi_districts_MPI.geojson")#.set_index('Dist_Name')
MPI['Normalized'] = MPI['Normalized'].astype(float)
MPI['Dist_Name'] = MPI['Dist_Name'].astype(str)
geojson = json.loads(MPI.to_json())

# Loading and Formatting MPI CSV Data=
df_mpi = pd.read_csv(path+"Hanoi_districts_MPI_long.csv")
variables = df_mpi['Variable'].unique()

# Loading and Formatting Food Systems Stakeholders Data
df_sh = pd.read_csv(path+"/hanoi_stakeholders.csv").dropna(how='any').astype(str)


# ------------------------- Preloading Figures ------------------------- #
# Adding MPI Choropleth to the map
fig_ch = px.choropleth_mapbox(MPI, geojson=geojson, 
                    locations="Dist_Name", 
                    featureidkey="properties.Dist_Name",
                    color='Normalized',
                    color_continuous_scale="Reds",
                    opacity=0.7,
                    range_color=(0, 1),
                    labels={'Normalized':'MPI',
                            'Dist_Name':'District Name'},

                    mapbox_style="carto-positron",
                    zoom=8,
                    center={"lat": MPI.geometry.centroid.y.mean(), 
                            "lon": MPI.geometry.centroid.x.mean()}
                    )

fig_ch.update_layout(coloraxis_colorbar=None)
fig_ch.update_coloraxes(showscale=False)

fig_ch.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=0, r=0, t=0, b=0)
)

# Initialising the stakeholder piechart
df_sh_area_count = pd.DataFrame(df_sh['Area of Activity in the food system'].value_counts()).reset_index()
df_sh_area_count.columns = ['name','count']
initial_piechart_1 = px.pie(df_sh_area_count, values='count', names='name', hole=0, 
                color_discrete_sequence=px.colors.sequential.Reds)
initial_piechart_1.update(layout_showlegend=False)
initial_piechart_1.update_traces(hoverinfo='percent', textinfo='label', textposition='inside', insidetextorientation='radial')
initial_piechart_1.update_layout(margin = dict(t=0.25, l=0.25, r=0.25, b=0.25))

# Custom styling for tabs
tab_style = {
    'borderBottom': '1px solid #000000',
    'backgroundColor': brand_colors['Dark khaki'],
    'flex' : '1 1 11%',
    'text-align' : 'center',
    'padding': '6px',
}

tab_selected_style = {
    'borderTop': '1px solid #000000',
    'borderBottom': '1px solid #ffffff',
    'borderLeft': '1px solid #ffffff',
    'backgroundColor': brand_colors['Mid khaki'],
    'text-align' : 'center',
    'color': 'black',
    'padding': '6px',
    'fontWeight': 'bold'
}


# ------------------------- Defining tab layouts ------------------------- #

def poverty_tab_layout():
    return html.Div([
        # Left Panel: text, dropdown, bar chart
        html.Div([

                html.H2("Multidimensional Poverty Dashboard", style={"color": brand_colors['Black'], "margin": "0"}),
                html.P(str(lorem.words(60)), style={"padding": "0", "textAlign": "justify"}),
                html.P('Please select a variable from the dropdown menu:'),
                dcc.Dropdown(
                    id='variable-dropdown',
                    options=[{'label': v, 'value': v} for v in variables],
                value=variables[0],
                style={"margin-bottom": "20px"}),
                dcc.Graph(id='bar-plot',
                        style={
                        'padding': '0',
                        'margin': '0',
                        "border-radius": "8px",
                        "box-shadow": "0 2px 8px rgba(0,0,0,0.15)",
                        })
                ], style={
                    "width": "min(50vw)",
                    "height": "100vh", 
                    "padding": "10px",
                    "backgroundColor": "#f9f9f9",
                    "border-radius": "0",
                    "margin": "0",
                    #"box-shadow": "0 2px 8px rgba(0,0,0,0.05)",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "flex-start",
                    "overflowY": "auto",
                    "box-sizing": "border-box",
                    "zIndex": 2,
                    "position": "relative",
                }),

        # Right panel: map, full height
        html.Div([
            dcc.Graph(
                id='map',
                figure=fig_ch,
                style={"height": "100%",
                       "width": "100%",  # fill the parent div
                       "padding": "0",
                       "margin": "0"})
        ], style={
            "flex": "1",
            "height": "100vh",
            "padding": "0",
            "margin": "0",
            "backgroundColor": brand_colors['White'],
            "border-radius": "0",
            "display": "flex",
            "alignItems": "stretch",
            "justifyContent": "center",
            "box-sizing": "border-box",
            "zIndex": 1,
            "position": "relative",
        })

    ], style={
        "display": "flex",
        "width": "90vw",
        "height": "100vh"
    })

def stakeholders_tab_layout():
        return html.Div([
                    # Left Panel: text, stakeholder plots etc.
                    html.Div([  html.H2("Food Systems Stakeholders"),
                                html.P(str(lorem.words(30)), style={"padding": "0", "textAlign": "justify"}),

                                html.Label("Filter Database by: "),
                                dcc.Dropdown(
                                            id='pie-filter-dropdown',
                                            options=[
                                                {'label': 'Area of Activity', 'value': 'Area'},
                                                {'label': 'Stakeholder Category', 'value': 'Category'}
                                            ],
                                            value='Area',
                                            clearable=False,
                                            style={"margin-bottom": "20px"}
                                        ),

                                dcc.Graph(id='piechart', figure=initial_piechart_1, style={'padding':'2px',
                                                                                         "box-shadow": "0 1px 2px rgba(0,0,0,0.05)"}),

                                dcc.Store(id='selected_slice', data=None)

                    ], style={
                    "flex": "1 1 40%",
                    "height": "100%", 
                    "padding": "10px",
                    "backgroundColor": "#f9f9f9",
                    "border-radius": "0",
                    "margin": "0",
                    #"box-shadow": "0 2px 8px rgba(0,0,0,0.05)",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "flex-start",
                    "overflowY": "auto",
                    "box-sizing": "border-box",
                    "zIndex": 2,
                    "position": "relative",
                    }),
            
                    # Table panel container
                    html.Div([
                        dbc.Container([
                            dash_table.DataTable(
                                data=df_sh.to_dict('records'), 
                                columns=[{"name": str(i), "id": str(i)} for i in df_sh.columns],
                                id='sh_table',
                                style_cell={
                                    'textAlign': 'left',
                                    'padding': '1px',
                                    'whiteSpace': 'normal',
                                    'height': 'auto',
                                    'minWidth': '15vw',
                                    'width': '15vw',
                                    'maxWidth': '20vw',
                                    'overflow': 'hidden',
                                    'textOverflow': 'ellipsis'
                                },
                                style_data={'whiteSpace': 'normal', 'height': 'auto', 'padding':"1px"},
                                style_header={
                                    'fontWeight': 'bold', 
                                    'backgroundColor': brand_colors['Medium violet red'], 
                                    'color': 'white',
                                    'textAlign': 'center',
                                    'padding': '5px'
                                },
                                fixed_rows={'headers': True, 'data': 0},
                                style_table={
                                    'height': '100%',
                                    'width': '100%',
                                    'overflowY': 'scroll',
                                    'padding':'0',
                                    'margin':'0',
                                    'flex': '1 1 auto'
                                },
                                virtualization=False
                            )
                        ], fluid=True, style={"padding": "10px", "margin": "0", "height": "100%", "width": "100%", "flex": "1 1 auto"})
                    ], style={
                        "flex": "1 1 50%",
                        "height": "100%",
                        "padding": "0",
                        "margin": "0",
                        "backgroundColor": brand_colors['White'],
                        "border-radius": "0",
                        "display": "flex",
                        "alignItems": "stretch",
                        "justifyContent": "stretch",
                        "box-sizing": "border-box",
                        "position": "relative"
                    }) # End of table panel container
    ], style={
        "display": "flex",
        "width": "90vw",
        "height": "100vh"
    })

def affordability_tab_layout():
    return html.Div([html.H1("Dietary Mapping & Affordability - Coming Soon")])

# ------------------------- Main app layout ------------------------- #

app.layout = html.Div([
    #Parent container
                html.Div([
        # Vertical tabs on the left
                    html.Div([
                                html.Img(src="/assets/logos/temp_efs_logo.png", 
                                            style={"height": "auto", 
                                                "width":"90%", 
                                                "padding": "0", 
                                                "justifyContent": "flex-start",
                                                "margin-bottom": "10px",}),

                                dcc.Tabs(id="tabs", value='tab-2-mpi', vertical=True, children=[
                                    dcc.Tab(label=tabs_brief[0], value='tab-1-stakeholders', style=tab_style, selected_style=tab_selected_style),
                                    dcc.Tab(label=tabs_brief[1], value='tab-2-mpi', style=tab_style, selected_style=tab_selected_style),
                                    dcc.Tab(label=tabs_brief[2], value='tab-3-affordability', style=tab_style, selected_style=tab_selected_style),
                                    dcc.Tab(label=tabs_brief[3], value='tab-4-nutrition', style=tab_style, selected_style=tab_selected_style),
                                    dcc.Tab(label=tabs_brief[4], value='tab-5-supply', style=tab_style, selected_style=tab_selected_style),
                                    dcc.Tab(label=tabs_brief[5], value='tab-6-shocks', style=tab_style, selected_style=tab_selected_style)
                                    ],style = {
                                                'width' : '90%',
                                                'height' : '100%',
                                                'display' : 'flex',
                                                "vertical-align":'top',
                                                "flexDirection": "column",
                                                'flex-wrap' : 'wrap',}), # End of tabs 
                                                
                                    ], style={
                                        "display": "flex",
                                        "vertical-align":'top',
                                        "flexDirection": "column",
                                        "justifyContent": "flex-start",
                                        "width": "10vw",
                                        "height": "100vh"}), # End of header div

                    # Preload Poverty tab content
                    html.Div(id="tab-content", children=poverty_tab_layout(), style={"width": "90vw"})
                ], style={
                        "display": "flex",
                        'width':"100vw",
                        'height':"100vh"}),
            
                # Footer
                html.Footer([
                    #html.P("Websites, maybe Logos, Links?"),
                    html.Div([
                            html.Img(src="/assets/logos/DeSIRA.png", style={'height': '60px', 'margin': '0 10px'}),
                            html.Img(src="/assets/logos/IFAD.png", style={'height': '50px', 'margin': '0 10px'}),
                            html.Img(src="/assets/logos/RyanInstitute.png", style={'height': '100px', 'margin': '0 10px'})
                        ], style={"display": "flex", "align-items": "center"})

                ], style={
                    "width": "100%",
                    "height": "80px",
                    "backgroundColor": brand_colors['Dark khaki'],
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between",
                    "margin-top": "20px",
                    "border-radius": "10px 10px 0 0"
                })
            ])

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
        labels={'Dist_Name': 'District',
                'Value':"Percentage of Deprived Households"},
        color_discrete_sequence=[brand_colors['Dark khaki']]
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'},
                      height=25 * len(sorted_df),
                      hoverlabel=dict(
                        bgcolor="white",      # Tooltip background color
                        font_color="black",   # Tooltip text color
                        #font_family="Calibri"
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
    zoom = 8

    MPI_display = MPI.copy()
    MPI_display['opacity'] = 0.7
    MPI_display['line_width'] = 0.8

    # If a bar is clicked, zoom to that district
    if clickData and 'points' in clickData:
        selected_dist = clickData['points'][0]['y']  # y is Dist_Name for horizontal bar
        match = MPI[MPI['Dist_Name'] == selected_dist]
        if not match.empty:
            centroid = match.geometry.centroid
            center = {
                "lat": match.geometry.centroid.y.values[0],
                "lon": match.geometry.centroid.x.values[0]
            }
            area = match.geometry.area.values[0]
            zoom = max(8, min(12, 12 - area * 150))  # Zoom in closer
            # Highlight: set opacity and line_width for the selected district
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
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
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

# Update Piechart 1 UI on click while filtering table
@app.callback(
    Output('piechart', 'figure'),
    Output('selected_slice', 'data'),
    Input('pie-filter-dropdown', 'value'),
    Input('piechart', 'clickData'),
    State('selected_slice', 'data'),
    prevent_initial_call=False
)
def update_pie(filter_by, clickData, current_selected):
    if filter_by == 'Area':
        df_count = df_sh['Area of Activity in the food system'].value_counts().reset_index()
        df_count.columns = ['name', 'count']
    else:
        df_count = df_sh['Stakeholder catagorization '].value_counts().reset_index()
        df_count.columns = ['name', 'count']

    # Handle click to select/unselect slice
    new_selected = current_selected
    pull = [0]*len(df_count)
    if clickData:
        clicked = clickData['points'][0]['label']
        new_selected = None if clicked == current_selected else clicked
        pull = [0.2 if name==new_selected else 0 for name in df_count['name']]

    fig = px.pie(df_count, values='count', names='name', hole=0,
                 color_discrete_sequence=px.colors.sequential.Reds)
    fig.update_traces(pull=pull, hoverinfo='percent', textinfo='label', textposition='inside', insidetextorientation='radial')
    fig.update_layout(margin=dict(t=0.25, l=0.25, r=0.25, b=0.25), showlegend=False)

    return fig, new_selected


# Table filtering based on both selections made in piecharts
@app.callback(
    Output('sh_table', 'data'),
    Input('pie-filter-dropdown', 'value'),
    Input('selected_slice', 'data')
)
def filter_table(filter_by, selected):
    if selected:
        if filter_by == 'Area':
            df_filtered = df_sh[df_sh['Area of Activity in the food system'] == selected]
        else:
            df_filtered = df_sh[df_sh['Stakeholder catagorization '] == selected]
        return df_filtered.to_dict('records')
    else:
        return df_sh.to_dict('records')


# Linking the tabs to page content loading 
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "value")
)
def render_tab_content(active_tab):
    if active_tab == 'tab-2-mpi':
        return poverty_tab_layout()
    elif active_tab == 'tab-1-stakeholders':
        return stakeholders_tab_layout()
    elif active_tab == 'tab-3-affordability':
        return affordability_tab_layout()
    else:
        return html.Div([html.H2("Tab not found")])


if __name__ == '__main__':
    app.run(debug=True)
