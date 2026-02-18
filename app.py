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
import dash
from dash import Dash, html, dcc, Output, Input, State, callback, dash_table
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash_extensions.javascript import assign
import random
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
import plotly.graph_objects as go
from lorem_text import lorem

import warnings
warnings.filterwarnings("ignore")

from dashboard_components import create_nutrition_kpi_card
import addis_config
import hanoi_config
from shared_components import sidebar, footer, city_selector
from addis_layouts import (
    stakeholders_tab_layout, supply_tab_layout, poverty_tab_layout,
    affordability_tab_layout, sustainability_tab_layout, policies_tab_layout,
    health_nutrition_tab_layout, footprints_tab_layout
)
from hanoi_layouts import (
    hanoi_stakeholders_tab_layout, hanoi_supply_tab_layout,
    hanoi_poverty_tab_layout, hanoi_affordability_tab_layout,
    hanoi_health_nutrition_tab_layout
)

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
MPI = gpd.read_file(path+"/addis_adm3_mpi.geojson")#.set_index('Dist_Name')
MPI['MPI'] = MPI['MPI'].astype(float)
MPI['Dist_Name'] = MPI['Dist_Name'].astype(str)
geojson = json.loads(MPI.to_json())

# Loading and Formatting MPI CSV Data=
df_mpi = pd.read_csv(path+"addis_mpi_long.csv")
variables = df_mpi['Variable'].unique()

# Loading and Formatting Food Systems Stakeholders Data
df_sh = pd.read_csv(path+"/addis_stakeholders_cleaned.csv").dropna(how='any').astype(str)
df_sh.rename(columns={'Area of Activity (Food Systems Value Chain)': 'Area of Activity'}, inplace=True)

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

# Loading GeoJSON files for Food Outlets
outlets_path = os.path.join(homepath, "assets", "data", "jsons_addis_foodoutlets")
outlets_geojson_files_addis = sorted(os.listdir(outlets_path))

# Loading and Formatting Food Environment Choropleth Data
food_env_path = path + "addis_diet_env_mapping.geojson"
gdf_food_env = gpd.read_file(food_env_path).to_crs('EPSG:4326')

# Define food environment metrics and their labels
cols_food_env = ['density_healthyout', 'density_unhealthyout', 'density_mixoutlets',
                 'ratio_obesogenic', 'pct_access_healthy', 'ptc_access_unhealthy']

data_labels_food_env = ['Healthy Outlet Density', 'Unhealthy Outlet Density', 'Mixed Outlet Density',
                        'Obesogenic Ratio', 'Percent Access to Healthy Food', 'Percent Access to Unhealthy Food']

# Define which metrics are "good" when higher (True) or "bad" when higher (False)
metric_direction = {
    'Count_healthy': True,
    'Count_UnhealthyOutlets': False,
    'Count_MixOutlets': None,
    'density_healthyout': True,
    'density_unhealthyout': False,
    'density_mixoutlets': None,
    'ratio_obesogenic': False,
    'pop_sum': None,
    'density_pop_healthy': True,
    'density_pop_unhealthy': False,
    'total_density_pop': None,
    'acc_healthyaccess_pop_healthysum': True,
    'acc_unhealthyaccess_unhealthy_popsum': False,
    'pct_access_healthy': True,
    'ptc_access_unhealthy': False
}

# Color schemes for choropleth
green_scale = ['#e3f6d5', '#c1d88e', '#a5be91', '#6f946d', '#3a6649']
red_scale = ['#fee5d9', '#fcbba1', '#fc9272', '#fb6a4a', '#de2d26']
grey_scale = ['#f7f7f7', '#d9d9d9', '#bdbdbd', '#969696', '#636363']

# Loading supply flow data for Sankey Diagram
df_sankey = pd.read_csv(path+'/hanoi_supply.csv')

df_policies = pd.read_csv(path+'/addis_policy_database.csv').drop('Unnamed: 0',axis=1)

df_indicators = pd.read_csv(path+'/addis_policy_database_expanded_sdg.csv')

# Create SDG logos as list of numbers for rendering
def get_sdg_numbers(row):
    sdg_cols = ['SDG_1', 'SDG_2', 'SDG_3', 'SDG_4', 'SDG_5']
    sdg_numbers = []
    for col in sdg_cols:
        if pd.notna(row[col]) and str(row[col]).strip():
            # Extract just the number (e.g., "1.3.1" -> "1", "2.1" -> "2")
            sdg_num = str(row[col]).split('.')[0]
            if sdg_num.isdigit() and sdg_num not in sdg_numbers:
                sdg_numbers.append(sdg_num)
    return ', '.join(sdg_numbers) if sdg_numbers else '--'

df_indicators['SDG Numbers'] = df_indicators.apply(get_sdg_numbers, axis=1)

df_env = pd.read_csv(path+'/addis_lca_pivot.csv')
df_lca = df_env  # Alias for compatibility

# -------------------------- Loading Hanoi Data ------------------------- #

# Hanoi MPI Data
MPI_hanoi = gpd.read_file(path+"Hanoi_districts_MPI.geojson")
MPI_hanoi['Normalized'] = MPI_hanoi['Normalized'].astype(float)
MPI_hanoi['Dist_Name'] = MPI_hanoi['Dist_Name'].astype(str)
geojson_hanoi = json.loads(MPI_hanoi.to_json())

# Hanoi MPI CSV Data
df_mpi_hanoi = pd.read_csv(path+"Hanoi_districts_MPI_long.csv")
variables_hanoi = df_mpi_hanoi['Variable'].unique()

# Hanoi Stakeholders Data
df_sh_hanoi = pd.read_csv(path+"/hanoi_stakeholders.csv").dropna(how='any').astype(str)

if 'Website' in df_sh_hanoi.columns:
    df_sh_hanoi['Website'] = df_sh_hanoi['Website'].apply(
        lambda x: f'[Link Available]({x})' if x and x.startswith('http') else '--'
    )

# Loading GeoJSON files for Food Outlets
outlets_path_hanoi = os.path.join(homepath, "assets", "data", "jsons_hanoi_foodoutlets")
outlets_geojson_files_hanoi = sorted(os.listdir(outlets_path_hanoi))

# Hanoi affordability data
df_affordability_hanoi = pd.read_csv(path+'/hanoi_affordability_cleaned.csv')

# Hanoi dietary data
df_diet_hanoi = pd.read_csv(path+'/hanoi_health_nutrition_cleaned.csv')
df_diet_2_hanoi = pd.read_csv(path+'hanoi_health_nutrition_cleaned_2.csv')

# -------------------------- Defining Custom Styles ------------------------- #

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
# sidebar and footer are now imported from shared_components.py

# ------------------------- Main app layout ------------------------- #

def landing_page_layout(background_image=None, tab_backgrounds=None, selected_city='addis'):
    """
    Generate landing page layout for a city.
    
    Args:
        background_image: URL to background image (default: Addis)
        tab_backgrounds: Dict mapping tab_id to background color (default: Addis)
        selected_city: Currently selected city ('addis' or 'hanoi')
    """
    if background_image is None:
        background_image = addis_config.BACKGROUND_IMAGE
    if tab_backgrounds is None:
        tab_backgrounds = addis_config.TAB_BACKGROUNDS
    
    tab_labels = [
        "Food Systems Stakeholders", "Food Flows, Supply & Value Chains", "Sustainability Metrics / Indicators", "Multidimensional Poverty",
        "Labour, skills & green jobs", "Resilience to Food System Shocks", "Dietary Mapping & Affordability", "Food Losses & Waste",
        "Food System Policies", "Health & Nutrition", "Environmental Footprints of Food & Diets", "Behaviour Change Tool (AI Chatbot & Game)"
    ]

    tab_ids = [
        "stakeholders", "supply", "sustainability", "poverty",
        "labour", "resilience", "affordability", "losses",
        "policies", "nutrition", "footprints", "behaviour"]
    
    # Use passed-in background_colours
    background_colours = tab_backgrounds
    
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
        # Store selected city
        dcc.Store(id='selected-city', data='addis'),
        
        # Header with Title and City Selector
        html.Div([
            # Title centered
            html.Div([
                html.H1("EcoFoodSystems Dashboard", style={
                    "color": brand_colors['Brown'],
                    "fontWeight": "bold",
                    "fontSize": "2.75em",
                    "marginBottom": "0",
                    "textAlign": "center"
                }),
            ], style={
                "width": "100%",
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center"
            }),
            
            # City Selector positioned on the right
            city_selector(selected_city=selected_city, visible=True),
        ], style={
            "position": "relative",
            "width": "100%",
            "paddingTop": "30px",
            "paddingBottom": "20px"
        }),

        # Subtitle text
        html.Div([
            html.P("EcoFoodSystems takes a food systems research approach to enable transitions towards diets that are more sustainable, healthier and affordable for consumers in city regions",
                style={
                    "color": brand_colors['Brown'],
                    "fontSize": "1em",
                    "textAlign": "center",
                    "maxWidth": "800px",
                    "margin": "0 auto 30px auto",
                }
            ),
        ], style={
            "width": "100%",
            "display": "flex",
            "justifyContent": "center"
        }),

        # Tab Grid
        html.Div([grid_layout], style={ "width": "100%", 
                                        "height":"auto",
                                        "display": "block",
                                        "marginTop": "auto",
                                        "backgroundImage": f"url('{background_image}')",  
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


# ------------------------- Tab Layouts ------------------------- #
# Tab layout functions are now in separate files:
# - addis_layouts.py: All Addis Ababa tab layouts
# - hanoi_layouts.py: All Hà Nội tab layouts



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

# ------------------------- Callbacks ------------------------- #

# Callback to store selected city
@app.callback(
    Output('selected-city', 'data'),
    Input('city-selector', 'value')
)
def store_selected_city(city):
    return city

# Linking the dropdown to the bar chart for the MPI page    
@app.callback(
    Output('bar-plot', 'figure'),
    Input('variable-dropdown', 'value'),
    prevent_initial_call=False
    
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
        labels={'Dist_Name': " ",
                'Value':"Percentage of Deprived Households"},
        color_discrete_sequence=[brand_colors['Red']]
    )
    fig.update_layout(
        yaxis={'categoryorder':'total ascending'},
        autosize=True,  # Allow figure to fill container
        #height=25 * len(sorted_df),
        margin=dict(l=0.15, r=0.1, t=0.15, b=1),
        hoverlabel=dict(
            bgcolor="white",      # Tooltip background color
            font_color="black",   # Tooltip text color
        )
    )

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
    zoom = 10

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
        color='MPI',
        color_continuous_scale="Reds",
        opacity=0.7,
        range_color=(0, 50),
        labels={'MPI':'MPI','Dist_Name':'District Name'},
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



@app.callback(
    Output('map_foodoutlets', 'figure'),
    Input('variable-dropdown', 'value')
)
def add_outlets_map(selected_variable):
    center = {
        "lat": MPI.geometry.centroid.y.mean(),
        "lon": MPI.geometry.centroid.x.mean()
    }
    zoom = 10

    fig = px.choropleth_mapbox(
        MPI,
        geojson=geojson,
        locations="Dist_Name",
        featureidkey="properties.Dist_Name",
        color='MPI',
        color_continuous_scale="Reds",
        opacity=0.7,
        range_color=(0, 50),
        labels={'MPI':'MPI','Dist_Name':'District Name'},
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

    return fig


# Update Piechart 1 UI on click while filtering table
@app.callback(
    Output('piechart', 'figure'),
    Output('selected_slice', 'data'),
    Input('pie-filter-dropdown', 'value'),
    Input('piechart', 'clickData'),
    State('selected_slice', 'data')
)
def update_pie(filter_by, clickData, current_selected):
    if filter_by == 'Area':
        df_count = df_sh['Area of Activity (Food Systems Value Chain)'].value_counts().reset_index()
        df_count.columns = ['name', 'count']
    elif filter_by == 'Scale':
        df_count = df_sh['Scale of Activity'].value_counts().reset_index()
        df_count.columns = ['name', 'count']
    elif filter_by == 'Sector':
        df_count = df_sh['Primary sector '].value_counts().reset_index()
        df_count.columns = ['name', 'count']

    # Handle click to select/unselect slice
    new_selected = current_selected
    pull = [0]*len(df_count)
    if clickData:
        clicked = clickData['points'][0]['label']
        new_selected = None if clicked == current_selected else clicked
        pull = [0.2 if name==new_selected else 0 for name in df_count['name']]

    slice_colors = plotting_palette_cat  # or greens_pie_palette
    text_colors = []
    for color in slice_colors:
        # Simple luminance check for hex color
        rgb = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        luminance = 0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]
        text_colors.append('white' if luminance < 180 else brand_colors['Brown'])


    fig = px.pie(df_count, values='count', names='name', hole=0,
                 color_discrete_sequence=slice_colors)
    fig.update_traces(textfont_color=text_colors, pull=pull, hoverinfo='percent', textinfo='label', textposition='inside', insidetextorientation='radial')
    fig.update_layout(margin=dict(t=0.1, l=0.1, r=0.1, b=0.1), showlegend=False)

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
            df_filtered = df_sh[df_sh['Area of Activity (Food Systems Value Chain)'] == selected]
        elif filter_by == 'Scale':
            df_filtered = df_sh[df_sh['Scale of Activity'] == selected] 
        elif filter_by == 'Sector':
            df_filtered = df_sh[df_sh['Primary sector '] == selected]
        return df_filtered.to_dict('records')
    else:
        return df_sh.to_dict('records')
    

@app.callback(
    Output('affordability-map', 'figure'),
    [Input("choropleth-select", "value"),
     Input("outlets-layer-select", "value")],
    [State('affordability-map', 'relayoutData')]
)
def update_affordability_map(selected_metric, selected_outlets, relayout_data):
    # Preserve current zoom and center if available
    if relayout_data and 'mapbox.center' in relayout_data:
        center = relayout_data['mapbox.center']
        zoom = relayout_data.get('mapbox.zoom', 11)
    else:
        center = {"lat": 9.0192, "lon":  38.752}
        zoom = 11
    
    fig = go.Figure()
    
    # Add choropleth layer if metric selected
    if selected_metric:
        gdf = gdf_food_env.copy()
        
        if selected_metric in gdf.columns:
            gdf[selected_metric] = pd.to_numeric(gdf[selected_metric], errors='coerce')
            
            # Get human-readable label for the metric
            metric_label = data_labels_food_env[cols_food_env.index(selected_metric)] if selected_metric in cols_food_env else selected_metric
            
            # Choose color scale based on metric direction
            direction = metric_direction.get(selected_metric, None)
            if direction is True:
                colorscale = [[0, green_scale[0]], [0.25, green_scale[1]], [0.5, green_scale[2]], 
                             [0.75, green_scale[3]], [1, green_scale[4]]]
            elif direction is False:
                colorscale = [[0, red_scale[0]], [0.25, red_scale[1]], [0.5, red_scale[2]], 
                             [0.75, red_scale[3]], [1, red_scale[4]]]
            else:
                colorscale = [[0, grey_scale[0]], [0.25, grey_scale[1]], [0.5, grey_scale[2]], 
                             [0.75, grey_scale[3]], [1, grey_scale[4]]]
            
            geojson_data = json.loads(gdf.to_json())
            
            fig.add_trace(go.Choroplethmapbox(
                geojson=geojson_data,
                locations=gdf.index,
                z=gdf[selected_metric],
                colorscale=colorscale,
                marker=dict(opacity=0.7, line=dict(color='#222', width=1)),
                hovertemplate='<b>' + metric_label + '</b>: %{z:.2f}<extra></extra>',
                text=gdf.get('Dist_Name', gdf.index),
                showscale=False
            ))
    
    # Add outlet markers if selected
    if selected_outlets:
        # Diverse color palette for outlet markers - high contrast against light backgrounds and each other
        marker_palette = [
            "#ff7f0e",  # Vibrant orange
            "#9467bd",  # Purple
            "#8c564b",  # Brown
            "#e377c2",  # Pink
            "#e8e826",  # Olive
            "#17becf"   # Cyan
        ]
        
        for i, filename in enumerate(selected_outlets):
            outlet_gdf = gpd.read_file(os.path.join(outlets_path, filename)).to_crs('EPSG:4326')
            
            # Cycle through diverse color palette
            marker_color = marker_palette[i % len(marker_palette)]
            
            fig.add_trace(go.Scattermapbox(
                lat=outlet_gdf.geometry.y,
                lon=outlet_gdf.geometry.x,
                mode='markers',
                marker=dict(size=6, color=marker_color, opacity=0.8),
                name=filename.split('_')[1] if len(filename.split('_')) < 4 else f"{filename.split('_')[1]} {filename.split('_')[2]}",
                hoverinfo='skip'
            ))
    
    # Update layout
    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=center,
            zoom=zoom
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=brand_colors['White'],
        showlegend=True if selected_outlets else False,
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)'),
        uirevision='constant'  # Preserve zoom/pan state
    )
    
    return fig


@app.callback(
    [Output("kpi-total-flow", "children"),
     Output("urban-indicator", "figure"),
     Output("sankey-graph", "figure")],
    Input("slider", "value"))

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

# Populate food items grid based on selected food group
@app.callback(
    Output('food-items-container', 'children'),
    [Input('food-group-select', 'value')]
)
def update_food_items_grid(selected_group):
    # Filter items by selected group
    filtered_df = df_lca[df_lca['Food Group'] == selected_group].sort_values('Item Cd')
    
    # Calculate percentile thresholds for traffic light system across all foods
    # Lower values are better for environmental impact
    thresholds = {
        'Total GHG Emissions': {
            'green': df_lca['Total GHG Emissions'].quantile(0.33),
            'yellow': df_lca['Total GHG Emissions'].quantile(0.67)
        },
        'Freshwater Comsumption (l)': {
            'green': df_lca['Freshwater Comsumption (l)'].quantile(0.33),
            'yellow': df_lca['Freshwater Comsumption (l)'].quantile(0.67)
        },
        'Acidification (kg SO2eq)': {
            'green': df_lca['Acidification (kg SO2eq)'].quantile(0.33),
            'yellow': df_lca['Acidification (kg SO2eq)'].quantile(0.67)
        },
        'Eutrophication (kg PO43-eq)': {
            'green': df_lca['Eutrophication (kg PO43-eq)'].quantile(0.33),
            'yellow': df_lca['Eutrophication (kg PO43-eq)'].quantile(0.67)
        }
    }
    
    def get_traffic_light_colors(value, indicator):
        """Return border and shadow colors based on traffic light system (green=good, yellow=medium, red=bad)"""
        if value <= thresholds[indicator]['green']:
            return {"border": "#2e7d32", "shadow": "#a5d6a7"}  # Dark green border, light green shadow
        elif value <= thresholds[indicator]['yellow']:
            return {"border": "#f57f17", "shadow": "#fff59d"}  # Dark yellow border, light yellow shadow
        else:
            return {"border": "#c62828", "shadow": "#ef9a9a"}  # Dark red border, light red shadow
    
    # Create a card for each food item
    food_cards = []
    for _, row in filtered_df.iterrows():
        # Create 2x2 grid of mini KPI cards with traffic light colors
        mini_kpis = html.Div([
            # Row 1: GHG and Water
            html.Div([
                # GHG mini card
                html.Div([
                    html.Div("GHG", style={"fontSize": "0.7em", "color": brand_colors['Brown'], "marginBottom": "2px"}),
                    html.Div(f"{row['Total GHG Emissions']:.4f}", style={"fontSize": "1em", "fontWeight": "bold", "color": brand_colors['Brown']}),
                    html.Div("kg CO₂-eq", style={"fontSize": "0.6em", "color": brand_colors['Brown']})
                ], style={"flex": "1", "textAlign": "center", "padding": "8px", 
                         "backgroundColor": brand_colors['White'], 
                         "border": f"2px solid {get_traffic_light_colors(row['Total GHG Emissions'], 'Total GHG Emissions')['border']}",
                         "boxShadow": f"0 2px 8px {get_traffic_light_colors(row['Total GHG Emissions'], 'Total GHG Emissions')['shadow']}",
                         "borderRadius": "5px", "margin": "3px"}),
                
                # Water mini card
                html.Div([
                    html.Div("Water", style={"fontSize": "0.7em", "color": brand_colors['Brown'], "marginBottom": "2px"}),
                    html.Div(f"{row['Freshwater Comsumption (l)']:.2f}", style={"fontSize": "1em", "fontWeight": "bold", "color": brand_colors['Brown']}),
                    html.Div("liters", style={"fontSize": "0.6em", "color": brand_colors['Brown']})
                ], style={"flex": "1", "textAlign": "center", "padding": "8px", 
                         "backgroundColor": brand_colors['White'], 
                         "border": f"2px solid {get_traffic_light_colors(row['Freshwater Comsumption (l)'], 'Freshwater Comsumption (l)')['border']}",
                         "boxShadow": f"0 2px 8px {get_traffic_light_colors(row['Freshwater Comsumption (l)'], 'Freshwater Comsumption (l)')['shadow']}",
                         "borderRadius": "5px", "margin": "3px"})
            ], style={"display": "flex", "marginBottom": "5px"}),
            
            # Row 2: Acidification and Eutrophication
            html.Div([
                # Acidification mini card
                html.Div([
                    html.Div("Acidification", style={"fontSize": "0.7em", "color": brand_colors['Brown'], "marginBottom": "2px"}),
                    html.Div(f"{row['Acidification (kg SO2eq)']:.6f}", style={"fontSize": "1em", "fontWeight": "bold", "color": brand_colors['Brown']}),
                    html.Div("kg SO₂-eq", style={"fontSize": "0.6em", "color": brand_colors['Brown']})
                ], style={"flex": "1", "textAlign": "center", "padding": "8px", 
                         "backgroundColor": brand_colors['White'], 
                         "border": f"2px solid {get_traffic_light_colors(row['Acidification (kg SO2eq)'], 'Acidification (kg SO2eq)')['border']}",
                         "boxShadow": f"0 2px 8px {get_traffic_light_colors(row['Acidification (kg SO2eq)'], 'Acidification (kg SO2eq)')['shadow']}",
                         "borderRadius": "5px", "margin": "3px"}),
                
                # Eutrophication mini card
                html.Div([
                    html.Div("Eutrophication", style={"fontSize": "0.7em", "color": brand_colors['Brown'], "marginBottom": "2px"}),
                    html.Div(f"{row['Eutrophication (kg PO43-eq)']:.6f}", style={"fontSize": "1em", "fontWeight": "bold", "color": brand_colors['Brown']}),
                    html.Div("kg PO₄³⁻-eq", style={"fontSize": "0.6em", "color": brand_colors['Brown']})
                ], style={"flex": "1", "textAlign": "center", "padding": "8px", 
                         "backgroundColor": brand_colors['White'], 
                         "border": f"2px solid {get_traffic_light_colors(row['Eutrophication (kg PO43-eq)'], 'Eutrophication (kg PO43-eq)')['border']}",
                         "boxShadow": f"0 2px 8px {get_traffic_light_colors(row['Eutrophication (kg PO43-eq)'], 'Eutrophication (kg PO43-eq)')['shadow']}",
                         "borderRadius": "5px", "margin": "3px"})
            ], style={"display": "flex"})
        ])
        
        # Main card for this food item
        food_card = dbc.Card([
            dbc.CardBody([
                html.H5(row['Item Cd'], style={
                    "color": brand_colors['Brown'],
                    "fontWeight": "bold",
                    "marginBottom": "10px",
                    "textAlign": "center",
                    "fontSize": "clamp(0.9em, 1em, 1.1em)"
                }),
                mini_kpis
            ])
        ], style={
            "backgroundColor": brand_colors['White'],
            "borderRadius": "10px",
            "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
            "padding": "10px",
            "height": "100%"
        })
        
        food_cards.append(food_card)
    
    return food_cards

# Callback for SDG filter buttons
@app.callback(
    [Output('indicators_table', 'data'),
     Output('sdg-filter-status', 'children'),
     Output('sdg-filter-1', 'style'),
     Output('sdg-filter-2', 'style'),
     Output('sdg-filter-3', 'style'),
     Output('sdg-filter-4', 'style'),
     Output('sdg-filter-5', 'style'),
     Output('sdg-filter-6', 'style'),
     Output('sdg-filter-7', 'style'),
     Output('sdg-filter-8', 'style'),
     Output('sdg-filter-9', 'style'),
     Output('sdg-filter-10', 'style'),
     Output('sdg-filter-11', 'style'),
     Output('sdg-filter-12', 'style'),
     Output('sdg-filter-13', 'style'),
     Output('sdg-filter-14', 'style'),
     Output('sdg-filter-15', 'style'),
     Output('sdg-filter-16', 'style'),
     Output('sdg-filter-17', 'style')],
    [Input('sdg-filter-1', 'n_clicks'),
     Input('sdg-filter-2', 'n_clicks'),
     Input('sdg-filter-3', 'n_clicks'),
     Input('sdg-filter-4', 'n_clicks'),
     Input('sdg-filter-5', 'n_clicks'),
     Input('sdg-filter-6', 'n_clicks'),
     Input('sdg-filter-7', 'n_clicks'),
     Input('sdg-filter-8', 'n_clicks'),
     Input('sdg-filter-9', 'n_clicks'),
     Input('sdg-filter-10', 'n_clicks'),
     Input('sdg-filter-11', 'n_clicks'),
     Input('sdg-filter-12', 'n_clicks'),
     Input('sdg-filter-13', 'n_clicks'),
     Input('sdg-filter-14', 'n_clicks'),
     Input('sdg-filter-15', 'n_clicks'),
     Input('sdg-filter-16', 'n_clicks'),
     Input('sdg-filter-17', 'n_clicks'),
     Input('sdg-clear-filter', 'n_clicks')]
)
def filter_by_sdg(*args):
    ctx = dash.callback_context
    
    # Default style for buttons
    default_style = {
        "border": "3px solid transparent",
        "borderRadius": "8px",
        "padding": "5px",
        "margin": "5px",
        "cursor": "pointer",
        "backgroundColor": "transparent",
        "transition": "all 0.2s"
    }
    
    # Selected style
    selected_style = {
        "border": f"3px solid {brand_colors['Red']}",
        "borderRadius": "8px",
        "padding": "5px",
        "margin": "5px",
        "cursor": "pointer",
        "backgroundColor": brand_colors['Light green'],
        "transition": "all 0.2s",
        "boxShadow": "0 2px 8px rgba(168, 0, 80, 0.3)"
    }
    
    # All buttons default style
    button_styles = [default_style.copy() for _ in range(17)]
    
    # Get all columns including SDG Numbers
    display_cols = ['Dimensions', 'Components', 'Indicators', 'SDG impact area/target', 'SDG Numbers']
    
    if not ctx.triggered:
        return df_indicators[display_cols].to_dict('records'), "Click an SDG icon to filter indicators", *button_styles
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Clear filter
    if button_id == 'sdg-clear-filter':
        return df_indicators[display_cols].to_dict('records'), "Showing all indicators", *button_styles
    
    # Extract SDG number from button id
    if button_id.startswith('sdg-filter-'):
        sdg_num = button_id.split('-')[-1]
        
        # Filter dataframe to rows containing this SDG number
        filtered_df = df_indicators[df_indicators['SDG Numbers'].str.contains(sdg_num, na=False)]
        
        # Update button style for selected SDG
        sdg_index = int(sdg_num) - 1
        button_styles[sdg_index] = selected_style
        
        status = f"Showing {len(filtered_df)} indicators for SDG {sdg_num}"
        
        return filtered_df[display_cols].to_dict('records'), status, *button_styles
    
    return df_indicators[display_cols].to_dict('records'), "Click an SDG icon to filter indicators", *button_styles

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
        Input("city-selector", "value"),
    ],
    [State("selected-city", "data")]
)
def render_tab_content(n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, city_value, selected_city):
    ctx = dash.callback_context
    if not ctx.triggered:
        return landing_page_layout()
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # If city selector changed, reload landing page with new city config
    if trigger_id == 'city-selector':
        if city_value == 'hanoi':
            return landing_page_layout(
                background_image=hanoi_config.BACKGROUND_IMAGE,
                tab_backgrounds=hanoi_config.TAB_BACKGROUNDS,
                selected_city='hanoi'
            )
        else:  # addis
            return landing_page_layout(
                background_image=addis_config.BACKGROUND_IMAGE,
                tab_backgrounds=addis_config.TAB_BACKGROUNDS,
                selected_city='addis'
            )
    
    tab_id = trigger_id
    
    # Route to city-specific dashboards
    if selected_city == 'hanoi':
        # Hanoi-specific tabs
        if tab_id == "tab-1-stakeholders":
            return hanoi_stakeholders_tab_layout()
        elif tab_id == "tab-2-supply":
            return hanoi_supply_tab_layout()
        elif tab_id == "tab-4-poverty":
            return hanoi_poverty_tab_layout()
        elif tab_id == "tab-7-affordability":
            return hanoi_affordability_tab_layout()
        elif tab_id == "tab-10-nutrition":
            return hanoi_health_nutrition_tab_layout()
        else:
            return landing_page_layout(
                background_image=hanoi_config.BACKGROUND_IMAGE,
                tab_backgrounds=hanoi_config.TAB_BACKGROUNDS,
                selected_city='hanoi'
            )
    
    # Addis Ababa tabs
    if tab_id == "tab-1-stakeholders":
        return stakeholders_tab_layout()
        
    elif tab_id == "tab-2-supply":
        return supply_tab_layout()
    
    elif tab_id == "tab-3-sustainability":
        return sustainability_tab_layout()
    
    elif tab_id == "tab-4-poverty":
        return poverty_tab_layout()
    
    elif tab_id == "tab-7-affordability":
        return affordability_tab_layout()
    
    elif tab_id == "tab-9-policies":
        return policies_tab_layout()

    elif tab_id == "tab-10-nutrition":
        return health_nutrition_tab_layout()
    
    elif tab_id == "tab-11-footprints":
        return footprints_tab_layout()

    else:
        return landing_page_layout()


# ------------------------- Hanoi Callbacks ------------------------- #

# Hanoi MPI bar chart
@app.callback(
    Output('bar-plot-hanoi', 'figure'),
    Input('variable-dropdown-hanoi', 'value'),
    prevent_initial_call=False
)
def update_bar_hanoi(selected_variable):
    filtered_df = df_mpi_hanoi[df_mpi_hanoi["Variable"]==selected_variable]
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
                        bgcolor="white",
                        font_color="black",
    ))
    return fig


# Hanoi MPI map
@app.callback(
    Output('map-hanoi', 'figure'),
    Input('bar-plot-hanoi', 'clickData'),
    Input('variable-dropdown-hanoi', 'value')
)
def update_map_on_bar_click_hanoi(clickData, selected_variable):
    center = {
        "lat": MPI_hanoi.geometry.centroid.y.mean(),
        "lon": MPI_hanoi.geometry.centroid.x.mean()
    }
    zoom = 7.75

    MPI_display = MPI_hanoi.copy()
    MPI_display['opacity'] = 0.7
    MPI_display['line_width'] = 0.8

    if clickData and 'points' in clickData:
        selected_dist = clickData['points'][0]['y']
        match = MPI_hanoi[MPI_hanoi['Dist_Name'] == selected_dist]
        if not match.empty:
            center = {
                "lat": match.geometry.centroid.y.values[0],
                "lon": match.geometry.centroid.x.values[0]
            }
            zoom = 10
            MPI_display.loc[MPI_display['Dist_Name'] == selected_dist, 'opacity'] = 1
            MPI_display.loc[MPI_display['Dist_Name'] == selected_dist, 'line_width'] = 2

    fig = px.choropleth_mapbox(
        MPI_hanoi,
        geojson=geojson_hanoi,
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

    fig.update_traces(
        marker=dict(
            opacity=MPI_display['opacity'],
            line=dict(width=MPI_display['line_width'], color='black')
        )
    )
    return fig

# Hanoi affordability map with outlet layers
@app.callback(
    Output('affordability-map-hanoi', 'figure'),
     Input("outlets-layer-select-hanoi", "value"),
    [State('affordability-map-hanoi', 'relayoutData')]
)
def update_affordability_map_hanoi(selected_outlets, relayout_data):
    # Calculate center from Hanoi districts
    hanoi_center = {
        "lat": MPI_hanoi.geometry.centroid.y.mean(),
        "lon": MPI_hanoi.geometry.centroid.x.mean()
    }
    
    # Preserve current zoom and center if available
    if relayout_data and 'mapbox.center' in relayout_data:
        center = relayout_data['mapbox.center']
        zoom = relayout_data.get('mapbox.zoom', 10)
    else:
        center = hanoi_center
        zoom = 10
    
    fig = go.Figure()
    
    # Add Hanoi district boundaries (outline only, no fill)
    fig.add_trace(go.Choroplethmapbox(
        geojson=geojson_hanoi,
        locations=MPI_hanoi.index,
        z=[0] * len(MPI_hanoi),  # Dummy values since we don't want color fill
        colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],  # Transparent fill
        marker=dict(
            opacity=0.5,  # No fill
            line=dict(color=brand_colors['Brown'], width=2)  # Brown boundaries
        ),
        hovertemplate='<b>%{text}</b><extra></extra>',
        text=MPI_hanoi['Dist_Name'],
        showscale=False,
        name="Districts"
    ))

    # Add outlet markers if selected
    if selected_outlets:
        # Diverse color palette for outlet markers - high contrast against light backgrounds and each other
        marker_palette = [
            "#ff7f0e",  # Vibrant orange
            "#9467bd",  # Purple
            "#8c564b",  # Brown
            "#e377c2",  # Pink
            "#e8e826",  # Olive
            "#17becf"   # Cyan
        ]
        
        for i, filename in enumerate(selected_outlets):
            outlet_gdf = gpd.read_file(os.path.join(outlets_path_hanoi, filename)).to_crs('EPSG:4326')
            
            # Cycle through diverse color palette
            marker_color = marker_palette[i % len(marker_palette)]
            
            fig.add_trace(go.Scattermapbox(
                lat=outlet_gdf.geometry.y,
                lon=outlet_gdf.geometry.x,
                mode='markers',
                marker=dict(size=6, color=marker_color, opacity=0.8),
                name=filename.split('_')[1] if len(filename.split('_')) < 4 else f"{filename.split('_')[1]} {filename.split('_')[2]}",
                hoverinfo='skip'
            ))
    
    # Update layout
    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=center,
            zoom=zoom
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=brand_colors['White'],
        showlegend=True if selected_outlets else False,
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)'),
        uirevision='constant'  # Preserve zoom/pan state
    )
    
    return fig

# Hanoi Sankey diagram
@app.callback(
    [Output("kpi-total-flow-hanoi", "children"),
     Output("urban-indicator-hanoi", "figure"),
     Output("sankey-graph-hanoi", "figure")],
    Input("slider-hanoi", "value"),
    prevent_initial_call=False
)
def update_sankey_hanoi(value):
    df_sankey_filt = df_sankey[df_sankey['Year']==int(value)]
    flow1 = df_sankey_filt[['province', 'Target', 'Supply to Hanoi']].rename(
        columns={'province':'source', 'Target':'target', 'Supply to Hanoi':'supply'})

    flow2 = df_sankey_filt[['Target', 'Target_1', 'Rice supply']].rename(
        columns={'Target':'source', 'Target_1':'target', 'Rice supply':'supply'})

    df_sankey_final = pd.concat([flow1.drop_duplicates(), flow2.groupby(['source','target']).sum().reset_index()], ignore_index=True)
    labels = list(pd.unique(df_sankey_final[['source','target']].values.ravel('K')))

    source_indices = df_sankey_final['source'].apply(lambda x: labels.index(x))
    target_indices = df_sankey_final['target'].apply(lambda x: labels.index(x))
    weights = df_sankey_final['supply']

    node_colors = [brand_colors['Red'] for l in labels]
    link_colors = ["rgba(209, 231, 168, 0.5)" for link in df_sankey_final['source']]

    # KPIs
    total_flow = flow1.drop_duplicates()["supply"].sum()
    total_flow_text = f"{total_flow:,.0f}"

    total = flow2.groupby(['source','target']).sum().reset_index()['supply'].sum()
    urban_only = flow2.groupby(['source','target']).sum().reset_index().set_index('target').loc['Hanoi urban'].values[1]
    urban_share = urban_only/total *100

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
        width=None
    )

    urban_fig = go.Figure(go.Pie(
        values=[urban_share, 100-urban_share],
        hole=0.6,
        marker=dict(colors=[brand_colors['Red'], brand_colors['Light green']]),
        textinfo="none",
        labels=["Urban", "Rural"],
        hoverinfo="label+percent",
        hovertext=[f"Urban: {urban_share:.1f}%", f"Rural: {100-urban_share:.1f}%"]
    ))
    
    urban_fig.update_layout(
        showlegend=False, 
        margin=dict(l=0,r=0,t=0,b=0.1),
        paper_bgcolor="rgba(0,0,0,0)",  
        plot_bgcolor="rgba(0,0,0,0)"
    )

    return total_flow_text, urban_fig, fig


# Hanoi affordability trend
@app.callback(
    Output('affordability-trend-hanoi','figure'),
    Input('affordability-filter-dropdown-hanoi','value')
)
def update_affordability_trend_hanoi(selected_variable):
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

    df_filt = df_affordability_hanoi[df_affordability_hanoi['Cat']==selected_variable]

    fig = px.line(df_filt, 
                  x='Year', 
                  y='value', 
                  color='Reg', 
                  markers=True,
                  color_discrete_sequence=[brand_colors['Red'], brand_colors['Dark green']]
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
    fig.update_yaxes(title_text=y_labels[selected_variable])
    return fig


# Hanoi health trend
@app.callback(
    Output('health-trend-hanoi','figure'),
    Input('health-filter-dropdown-hanoi','value')
)
def update_health_trend_hanoi(selected_variable):
    df_filt = df_diet_2_hanoi[df_diet_2_hanoi['Cat']==selected_variable]

    fig = px.line(df_filt, 
                  x='Year', 
                  y='value', 
                  color='Reg', 
                  markers=True,
                  color_discrete_sequence=[brand_colors['Red'], brand_colors['Dark green']]
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
    fig.update_yaxes(title_text=selected_variable)
    return fig


# Hanoi diet dumbbell
@app.callback(
    Output('diet-dumbbell-hanoi', 'figure'),
    Input('dumbbell-slider-hanoi', 'value')
)
def update_diet_dumbbell_hanoi(year_start):
    categories = df_diet_hanoi['Cat'].unique()
  
    line_x, line_y, x_start, x_2023, y_labels = [], [], [], [], []

    for cat in categories:
        val_start = df_diet_hanoi.loc[(df_diet_hanoi.Year == year_start) & (df_diet_hanoi.Cat == cat), "value"].values[0]
        val_2023 = df_diet_hanoi.loc[(df_diet_hanoi.Year == 2023) & (df_diet_hanoi.Cat == cat), "value"].values[0]
        line_x.extend([val_start, val_2023, None])
        line_y.extend([cat, cat, None])
        x_start.append(val_start)
        x_2023.append(val_2023)
        y_labels.append(cat)

    fig = go.Figure()

    # Line connecting start year and 2023
    fig.add_trace(go.Scatter(
        x=line_x,
        y=line_y,
        mode="lines",
        line=dict(color="grey"),
        showlegend=False
    ))

    # Start year markers
    fig.add_trace(go.Scatter(
        x=x_start,
        y=y_labels,
        mode="markers",
        name=str(year_start),
        marker=dict(
            color=brand_colors['Red'],
            size=8,
            symbol="circle",
            line=dict(color=brand_colors['Brown'], width=2)
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
            line=dict(color=brand_colors['Brown'], width=2)
        )
    ))

    # Add arrows
    for x0, x1, y in zip(x_start, x_2023, y_labels):
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
            showgrid=True,
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
        plot_bgcolor=brand_colors['White']
    )

    return fig


# Expose the Flask server for production deployment
server = app.server

if __name__ == '__main__':
    # For production, Render will set PORT environment variable
    port = int(os.environ.get('PORT', 8051))
    # Debug True by default for local dev, False in production (when PORT is set by Render)
    debug = os.environ.get('PORT') is None
    app.run(debug=debug, host='0.0.0.0', port=port)
