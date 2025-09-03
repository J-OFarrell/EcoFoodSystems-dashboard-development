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

from dash import Dash, html, dcc, Output, Input

import warnings
warnings.filterwarnings("ignore")

app = Dash()

colors = {
  'eco_green': '#AFC912',
  'forest_green': '#4C7A2E',
  'earth_brown': '#7B5E34',
  'harvest_yellow': '#F2D16B',
  'neutral_light': '#F5F5F5',
  'dark_text': '#333333',
  'accent_warm': '#E07A5F'
}

# Loading and Formatting MPI Data
path = "/Users/jemim/app_dev_EFS/"
MPI = gpd.read_file(path+"Hanoi_districts_MPI.geojson")#.set_index('Dist_Name')
MPI['Normalized'] = MPI['Normalized'].astype(float)
MPI['Dist_Name'] = MPI['Dist_Name'].astype(str)
geojson = json.loads(MPI.to_json())

# Adding MPI Choropleth to the map
fig_ch = px.choropleth_mapbox(MPI, geojson=geojson, 
                    locations="Dist_Name", 
                    featureidkey="properties.Dist_Name",
                    color='Normalized',
                    color_continuous_scale="RdYlGn_r",
                    opacity=0.8,
                    range_color=(0, 1),
                    labels={'Normalized':'MPI',
                            'Dist_Name':'District Name'},

                    mapbox_style="carto-positron",
                    zoom=7.5,
                    center={"lat": MPI.geometry.centroid.y.mean(), 
                            "lon": MPI.geometry.centroid.x.mean()}
                    )

fig_ch.update_layout(coloraxis_colorbar=dict(
    title=None,
    orientation='h',  # 'v' for vertical (default), 'h' for horizontal
    thickness=20,
    len=1,
    x=0.5,  # position on x-axis (for horizontal orientation)
    y=-0.2,   # position on y-axis
    tickvals=[0, 0.5, 1],
    ticktext=["Low", "Medium", "High"]
))

# Adding grouped bar chart of MDI variables per dist
df = pd.read_csv(path+"Hanoi_districts_MPI_long.csv")
variables = df['Variable'].unique()

app.layout = html.Div([

    # Header
    html.Header(
        style={
            "width": "50%",
            "display": "inline-block",
            "align-items": "center",
            "justify-content": "center",
            "backgroundColor": colors['eco_green'],
            #"padding": "10px"
        },
        children=[
            html.H1(
                style={
                    'textAlign': 'center',
                    'color': colors['dark_text'],
                    'font-family': 'Calibri',
                    'font-weight': 'bold',
                    'font-size': '32px',
                    'padding': '2px',
                    "border-radius": "0 0 5px 0"
                    },
                children='EcoFoodSystems Dash Demo',
            )
        ]
    ),

    # Body
    html.Div(
        style={
            "display": "flex",
            "width": "100%",
            "justify-content": "space-between",
            'font-family': 'Calibri'
        },
        children=[
    # Adding text and drop down menu for chart
            html.Div(
                style={
                    "width": "50%",
                    "padding": "10px",
                    "height": "400px",
                    "overflowY": "scroll",  # Enable vertical scrolling
                    "border": "1px solid #ccc", 
                },
                children=[
                    html.P('Some text about the data from Yared \n'),
                    html.P('Please select a variable from the dropdown menu:'),
                    dcc.Dropdown(
                        id='variable-dropdown',
                        options=[{'label': v, 'value': v} for v in variables],
                        value=variables[0]) 
            ]),
    # Adding bar chart for selected variable
            html.Div(
                style={
                "width": "45%",
                "padding": "20px",
                "backgroundColor": "#f9f9f9",
                "border-radius": "10px",
                "box-shadow": "0 2px 8px rgba(0,0,0,0.05)"
                },
                children=[dcc.Graph(id='bar-plot')
            ]),

            html.Div(
                style={
                    "width": "50%",
                    "padding": "0",
                    "height": "90vh",
                    "border-radius": "10px",
                    "box-shadow": "0 2px 8px rgba(0,0,0,0.05)",
                    "backgroundColor": colors['light_background'],
                },
                children=[
                    dcc.Graph(
                        id='map',
                        figure=fig_ch,
                        style={"height": "90vh"})
            ])
    ]),


    # Footer
    html.Footer(
        style={
            "width": "100%",
            "height": "80px",
            "backgroundColor": colors['eco_green'],
            "border": "0px",
            "display": "flex",
            "align-items": "center",
            "justify-content": "flex",
            "padding": "0px",
            "margin-top": "20px"
        },
        children=[
            html.Img(src="/assets/DeSIRA.png", style={'width': 'auto', 
                                                    'height': '60px', 
                                                    "vertical-align": "center",
                                                    "horizontal-align": "left",
                                                    "padding":"20px"}),
            html.Img(src="/assets/IFAD.png", style={'width': 'auto', 
                                                    'height': '50px', 
                                                    "vertical-align": "center",
                                                    "horizontal-align": "left",
                                                    "padding":"20px"}),
            html.Img(src="/assets/RyanInstitute.png", style={'width': 'auto', 
                                                    'height': '100px', 
                                                    "vertical-align": "center",
                                                    "horizontal-align": "right",
                                                    "padding":"10px"})
        ]
    )

])


@app.callback(
    Output('bar-plot', 'figure'),
    Input('variable-dropdown', 'value')
)

def update_bar(selected_variable):
    # Sort by selected variable, descending
    filtered_df = df[df["Variable"]==selected_variable]
    sorted_df = filtered_df.sort_values('Value', ascending=False)
    fig = px.bar(
        sorted_df,
        x='Value',
        y='Dist_Name',
        orientation='h',
        hover_data=['Dist_Name'],
        labels={'Dist_Name': 'District',
                'Value':"Percentage of Deprived Households"},
        color_discrete_sequence=[colors['accent_warm']]
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'},
                      height=25 * len(sorted_df))
    return fig

if __name__ == '__main__':
    app.run(debug=True)


                    #    [
                    #        'Food Systems Stakeholders',
                    #        'Multidimensional Poverty',
                    #        'Dietry Mapping & Affordability',
                    #        'Health & Nutrition',
                    #        'Food Flows, Supply & Value Chain',
                    #        'Climate Shocks and Resilience'
                    #    ]