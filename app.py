import os
import csv
from functools import lru_cache
import numpy as np
import xarray as xr
import rioxarray as rxr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd
import geopandas as gpd
from shapely.ops import unary_union
import seaborn as sns
import plotly.express as px
import json
import dash
from dash import Dash, html, dcc, Output, Input, State, callback, dash_table, ALL, ctx
import dash_bootstrap_components as dbc
import dash_auth  
import dash_leaflet as dl
from dash_extensions.javascript import assign
import random
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
import plotly.graph_objects as go
import plotly.colors as pc
import plotly.io as pio
from plotly.subplots import make_subplots
from lorem_text import lorem
from io import StringIO

import warnings
warnings.filterwarnings("ignore")

# Esri World Imagery (satellite) tiles — used for Vietnam maps while a
# compliant labelled basemap is sourced from Vietnamese partners.
# Hoang Sa (Paracel) and Truong Sa (Spratly) islands are rendered explicitly
# as GeoJSON overlays on the resilience tab to satisfy Vietnamese law.
#_ESRI_TILE = {
#    "below": "traces",
#    "sourcetype": "raster",
#    "source": ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
#}

_BASEMAP_TILE = [
{
    "below":"traces",
    "sourcetype":"raster",
    "source":[
        "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
    ]
}
]


from dashboard_components import create_nutrition_kpi_card
import addis_config
import hanoi_config
from shared_components import sidebar, footer, city_selector
from addis_layouts import (
    governance_stakeholders_tab_layout as addis_governance_stakeholders_tab_layout,
    storage_distribution_tab_layout as addis_storage_distribution_tab_layout,
    livelihoods_poverty_equity_tab_layout as addis_livelihoods_poverty_equity_tab_layout,
    sdg_indicator_atlas_tab_layout as addis_fcd_indicator_atlas_tab_layout,
    governance_policies_tab_layout as addis_governance_policies_tab_layout,
    diets_nutrition_health_tab_layout as addis_diets_nutrition_health_tab_layout,
    environment_footprints_tab_layout as addis_environment_footprints_tab_layout,
    #resilience_tab_layout as addis_resilience_tab_layout,
    environment_climate_change_tab as addis_environment_climate_change_tab,
    income_growth_distribution_tab as addis_income_growth_distribution_tab,
    policies_leadership_tab as addis_policies_leadership_tab,
    population_growth_migration_tab as addis_population_growth_migration_tab,
    socio_cultural_context_tab as addis_socio_cultural_context_tab,
    food_availability_tab as addis_food_availability_tab,
    food_affordability_tab as addis_food_affordability_tab,
    food_accessibility_vendor_properties_tab_layout as addis_vendor_properties_tab,
    processing_packing_tab as addis_processing_packing_tab,
    production_systems_input_supply_tab as addis_production_systems_input_supply_tab,
    retail_markerting_tab as addis_retail_markerting_tab,
    storage_distrbution_tab as addis_storage_distrbution_tab,
    economic_tab as addis_economic_tab,
    governance_tab as addis_governance_tab,
    resilience_tab as addis_resilience_tab,
    food_security_tab as addis_food_security_tab,
    livelihoods_poverty_equity_tab as addis_livelihoods_poverty_equity_tab,
    noncommunicable_diseases_tab as addis_noncommunicable_diseases_tab,
    nutrional_status_tab as addis_nutrional_status_tab,
    governance_policies_tab_layout as addis_governance_policies_tab_layout,
)
from hanoi_layouts import (
    governance_stakeholders_tab_layout as hanoi_governance_stakeholders_tab_layout,
    storage_distribution_tab_layout as hanoi_storage_distribution_tab_layout,
    livelihoods_poverty_equity_tab_layout as hanoi_livelihoods_poverty_equity_tab_layout,
    food_affordability_tab_layout as hanoi_food_affordability_tab_layout,
    diets_nutrition_health_tab_layout as hanoi_diets_nutrition_health_tab_layout,
    #governance_policies_tab_layout as hanoi_policies_leadership_tab,
    policies_leadership_tab as hanoi_policies_leadership_tab,
    sdg_indicator_atlas_tab_layout as hanoi_fcd_indicator_atlas_tab_layout,
    climate_resilience_tab_layout as hanoi_climate_resilience_tab,
    environment_climate_change_tab as hanoi_environment_climate_change_tab,
    income_growth_distribution_tab as hanoi_income_growth_distribution_tab,
    policies_leadership_tab as hanoi_policies_leadership_tab,
    population_growth_migration_tab as hanoi_population_growth_migration_tab,
    socio_cultural_context_tab as hanoi_socio_cultural_context_tab,
    food_availability_tab as hanoi_food_availability_tab,
    food_affordability_tab as hanoi_food_affordability_tab,
    vendor_properties_tab as hanoi_vendor_properties_tab,
    processing_packing_tab as hanoi_processing_packing_tab,
    production_systems_input_supply_tab as hanoi_production_systems_input_supply_tab,
    retail_markerting_tab as hanoi_retail_markerting_tab,
    storage_distrbution_tab as hanoi_storage_distrbution_tab,
    economic_tab as hanoi_economic_tab,
    governance_tab as hanoi_governance_tab,
    temporal_resilience_tab as hanoi_temporal_resilience_tab,
    food_security_tab as hanoi_food_security_tab,
    livelihoods_poverty_equity_tab as hanoi_livelihoods_poverty_equity_tab,
    noncommunicable_diseases_tab as hanoi_noncommunicable_diseases_tab,
    nutrional_status_tab as hanoi_nutrional_status_tab,
    render_spatial_climate_resilience_layout,
    render_temporal_resilience_layout,
    render_lulc_resilience_layout,
)

app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.server.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

VALID_USERNAME = os.environ.get('DASH_USERNAME', 'ecofoodsystems')
VALID_PASSWORD = os.environ.get('DASH_PASSWORD', 'data4decisions!')

auth = dash_auth.BasicAuth(
    app,
    {VALID_USERNAME: VALID_PASSWORD}
)


def _path_mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def _figure_from_json(fig_json):
    return pio.from_json(fig_json) if fig_json else go.Figure()


@lru_cache(maxsize=96)
def _read_geojson_cached(path):
    return gpd.read_file(path).to_crs("EPSG:4326")


def _load_food_env_layer(geojson_path, values_csv_path=None, join_key_candidates=None):
    if not os.path.exists(geojson_path):
        return None

    gdf = gpd.read_file(geojson_path).to_crs("EPSG:4326")

    if values_csv_path and os.path.exists(values_csv_path):
        try:
            candidate_keys = list(join_key_candidates or [])
            dtype_map = {col: "string" for col in candidate_keys}
            df_values = pd.read_csv(values_csv_path, dtype=dtype_map, keep_default_na=False)
            join_key = next(
                (col for col in candidate_keys if col in gdf.columns and col in df_values.columns),
                None,
            )
            if join_key:
                gdf[join_key] = gdf[join_key].astype("string").str.strip()
                df_values[join_key] = df_values[join_key].astype("string").str.strip()

                df_values = df_values[df_values[join_key].notna() & (df_values[join_key] != "")].copy()
                df_values = df_values.drop_duplicates(subset=[join_key])

                gdf = gdf.merge(df_values, on=join_key, how="left")
                gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs="EPSG:4326")
            else:
                print(f"[WARN] No common join key found for food environment layer: {geojson_path}")
        except Exception as exc:
            print(f"[WARN] Could not merge food environment values from CSV: {exc}")

    return gdf


@lru_cache(maxsize=4)
def _get_food_env_geojson(city_key):
    gdf = gdf_summary_stats_addis if city_key == "addis" else gdf_food_env_hanoi if city_key == "hanoi" else None
    if gdf is None:
        return None

    keep_cols = [c for c in ["Dist_Name", "Dist_name", "shapeName", "commune", "name", "ma_xa"] if c in gdf.columns]
    slim_gdf = gdf[keep_cols + ["geometry"]].copy() if keep_cols else gdf[["geometry"]].copy()
    return slim_gdf.to_json()


@lru_cache(maxsize=48)
def _build_isochrone_union_geojson(isochrones_path_local, selected_isochrones_key, selected_time_seconds, selected_transport_mode):
    """
    Union selected isochrone files and filter by travel time threshold.
    
    Args:
        isochrones_path_local: Path to isochrones directory
        selected_isochrones_key: Tuple of outlet category names (e.g., ('shop_bakery', 'shop_alcohol'))
        selected_time_seconds: Time threshold in seconds (e.g., 900 for 15 minutes)
        selected_transport_mode: Mode of transportation (e.g., 'walk', 'multimodal', 'driving')
    Returns:
        GeoJSON string of unioned isochrones, or None if no geometries found
    """

    if not selected_isochrones_key:
        print(f"DEBUG: No isochrones selected, returning None")
        return None

    geoms = []
    for outlet_category in selected_isochrones_key:
        # Map outlet category to isochrone filename
        # E.g., 'shop_bakery' -> 'isochrone_shop_bakery_multimodal.geojson'
        iso_filename = f"isochrone_{outlet_category}_{selected_transport_mode}.geojson"
        iso_path = os.path.join(isochrones_path_local, iso_filename)

        #print(f"DEBUG: Processing isochrone file: {iso_path} for category '{outlet_category}' with time threshold {selected_time_seconds}")
      
        if os.path.exists(iso_path):
            try:
                gdf = _read_geojson_cached(iso_path)
                #print(f"DEBUG: Loaded GeoDataFrame shape: {gdf.shape}")
                
                # Filter by selected travel time label (time_seconds column)
                if 'threshold_s' in gdf.columns:
                    gdf["threshold_s"] = pd.to_numeric(gdf["threshold_s"], errors='coerce')
                    filtered_gdf = gdf[gdf['threshold_s'].astype(int) == int(selected_time_seconds)]
                    #print(f"DEBUG: Filtered GeoDataFrame shape: {filtered_gdf.shape}")
                    geoms.extend([geom for geom in filtered_gdf.geometry if geom is not None and not geom.is_empty])
                else:
                    #print(f"DEBUG: No time_seconds or time_label column, including all {len(gdf)} geometries")
                    geoms.extend([geom for geom in gdf.geometry if geom is not None and not geom.is_empty])
            except Exception as e:
                #print(f"Error loading isochrone {iso_filename}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"DEBUG: Isochrone file not found: {iso_path}")

    try:
        unioned = unary_union(geoms)
        # Create GeoDataFrame in EPSG:4326 (isochrones already in this CRS)
        union_gdf = gpd.GeoDataFrame({"geometry": [unioned]}, crs="EPSG:4326")
        # Convert to GeoJSON 
        result = union_gdf.to_json()
        #print(f"DEBUG: Successfully created GeoJSON, length={len(result)}")
        return result
    except Exception as e:
        #print(f"Error unioning isochrone geometries: {e}")
        import traceback
        traceback.print_exc()
        return None

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
    'Black': '#333333',
    "Brown": "#313715",
    "Red": "#A80050",
    "Orange": "#D9A85C",
    "Teal": "#1d574f",
    "Light Teal": "#4e998c",
    "Dark green": "#939f5c",
    "Mid green": "#bbce8a",
    "Light green": "#E8F0DA",
    "White": "#ffffff"
}

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

_cmap_full = plt.get_cmap('RdYlBu_r')
_cmap = mcolors.LinearSegmentedColormap.from_list(
    'RdYlGn_r_clipped',
    _cmap_full(np.linspace(0.25, 1.0, 256))
)

drought_colorscale = [[round(i/9, 2), mcolors.to_hex(_cmap(i/9))] for i in range(10)]


tabs = [
    'Food Systems Stakeholders',                 
    'Food Flows & Supply Chains',         
    'Sustainability Metrics',       
    'Multidimensional Poverty',                  
    'Resilience Indicators',          
    'Food Environments',           
    'Food Losses & Waste',                      
    'Policies & Regulation',                     
    'Nutrition & Health',                       
    'Environmental Footprints',  
    'Behaviour Change Tool (AI Chatbot & Game)'  
]

# -------------------------- Loading and Formatting All Data ------------------------- #

homepath = os.path.dirname(os.path.abspath(__file__))
data_root = os.path.join(homepath, "assets", "data")

addis_root = os.path.join(data_root, "addis")
addis_mpi_dir = os.path.join(addis_root, "mpi")
addis_stakeholders_dir = os.path.join(addis_root, "stakeholders")
addis_food_env_dir = os.path.join(addis_root, "food_environment")
addis_policy_dir = os.path.join(addis_root, "policy")
addis_environment_dir = os.path.join(addis_root, "environment")
addis_adm3_dir = os.path.join(addis_root, "aa_adm3_updated")

hanoi_root = os.path.join(data_root, "hanoi")
hanoi_mpi_dir = os.path.join(hanoi_root, "mpi")
hanoi_stakeholders_dir = os.path.join(hanoi_root, "stakeholders")
hanoi_policy_dir = os.path.join(hanoi_root, "policy")
hanoi_supply_dir = os.path.join(hanoi_root, "supply_chain")
hanoi_affordability_dir = os.path.join(hanoi_root, "affordability")
hanoi_nutrition_dir = os.path.join(hanoi_root, "nutrition")
hanoi_food_env_dir = os.path.join(hanoi_root, "food_environment")
hanoi_resilience_dir = os.path.join(hanoi_root, "resilience")
hanoi_climate_dir = os.path.join(hanoi_resilience_dir, "precomputed_hanoi_climate_vars")
hanoi_infrastructure_dir = os.path.join(hanoi_resilience_dir, "osm_infrastructure")
#atlas_csv_path = os.path.join(homepath, "EcoFoodSystems_indicator_architecture - 260326 - Hanoi_rewritten_descriptions_final.csv")
atlas_csv_path = os.path.join(homepath, "EcoFoodSystems_FCD_aligned.csv")

# Loading and Formatting MPI Data
MPI = gpd.read_file(os.path.join(addis_mpi_dir, "addis_districts_MPI.geojson"))#.set_index('Dist_Name')
MPI['Multidimensional Poverty Index'] = MPI['Multidimensional Poverty Index'].astype(float)
MPI['Dist_Name'] = MPI['Dist_Name'].astype(str)
geojson = json.loads(MPI.to_json())

adm3_eth_gdf = gpd.read_file(os.path.join(addis_adm3_dir, "aa_adm3_updated.geojson")).to_crs("EPSG:4326")
adm3_eth_gdf = adm3_eth_gdf.reset_index(drop=True)
adm3_eth_gdf["adm3_id"] = adm3_eth_gdf.index.astype(str)
adm3_eth_geojson = json.loads(adm3_eth_gdf[["adm3_id", "ADM3_EN", "geometry"]].to_json())

# Loading and Formatting MPI CSV Data=
# Detect numeric columns in the GeoJSON and coerce to numeric where possible
geo_vars = []
for _col in MPI.columns:
    if _col in ['geometry', 'Dist_Name']:
        continue
    coerced = pd.to_numeric(MPI[_col], errors='coerce')
    if coerced.notna().any():
        MPI[_col] = coerced
        geo_vars.append(_col)

# Loading and Formatting MPI CSV Data (fallback)
df_mpi = pd.read_csv(os.path.join(addis_mpi_dir, "addis_mpi_long.csv"))
vars_csv = list(df_mpi['Variable'].unique())
# Universal list of MPI variables (source of truth for dropdown ordering)
mpi_vars = [
    'Multidimensional Poverty Index',
    'Cooking fuel',
    'Housing',
    'Assets',
    'Drinking water',
    'Sanitation',
    'Electricity'
]

# For Addis, use the universal list but only include variables present in the GeoDataFrame
variables = [v for v in mpi_vars if v in MPI.columns]

# Loading and Formatting Food Systems Stakeholders Data
df_sh = pd.read_csv(os.path.join(addis_stakeholders_dir, "addis_stakeholders_cleaned.csv")).dropna(how='any').astype(str)
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
outlets_path = os.path.join(addis_food_env_dir, "jsons_addis_foodoutlets")
outlets_geojson_files_addis = sorted(os.listdir(outlets_path))


def _humanize_outlet_label(filename):
    base = os.path.splitext(os.path.basename(filename))[0]
    if base.endswith("_addis"):
        base = base[:-6]
    if base.startswith("shop_"):
        base = base[len("shop_"):]
    elif base.startswith("amenity_"):
        base = base[len("amenity_"):]
    if base in {"healthy", "healthy_offers"}:
        return "All Healthy Offers"
    if base in {"unhealthy", "unhealthy_offers"}:
        return "All Unhealthy Offers"
    if base in {"mixed", "mixed_offers"}:
        return "All Mixed Offers"
    return base.replace("_", " ").title()


def _build_accessibility_outlet_options_addis(outlet_files):
    healthy_files = {
        "healthy_offers_addis.geojson",
        "shop_butcher_addis.geojson",
        "shop_dairy_addis.geojson",
        "shop_farm_addis.geojson",
        "shop_greengrocer_addis.geojson",
        "shop_health_food_addis.geojson",
        "shop_seafood_addis.geojson",
        "amenity_marketplace_addis.geojson",
        "amenity_drinking_water_addis.geojson",
    }
    unhealthy_files = {
        "unhealthy_offers_addis.geojson",
        "shop_bakery_addis.geojson",
        "shop_beverages_addis.geojson",
        "shop_confectionery_addis.geojson",
        "shop_convenience_addis.geojson",
        "shop_pastry_addis.geojson",
        "shop_kiosk_addis.geojson",
        "amenity_fast_food_addis.geojson",
        "amenity_cafe_addis.geojson",
        "amenity_ice_cream_addis.geojson",
        "amenity_vending_machine_addis.geojson",
    }
    mixed_files = {
        "mixed_offers_addis.geojson",
        "shop_supermarket_addis.geojson",
        "amenity_restaurant_addis.geojson",
        "amenity_pub_addis.geojson",
        "shop_deli_addis.geojson",
    }

    groups = [
        ("All Healthy Offers", healthy_files),
        ("All Unhealthy Offers", unhealthy_files),
        ("All Mixed Offers", mixed_files),
    ]

    remaining = []
    grouped = []
    used = set()

    for header, known_files in groups:
        section_items = [f for f in outlet_files if f in known_files]
        if section_items:
            grouped.append({"label": f"── {header} ──", "value": f"__{header.lower().replace(' ', '_')}__", "disabled": True})
            for file_name in sorted(section_items, key=_humanize_outlet_label):
                grouped.append({"label": _humanize_outlet_label(file_name), "value": file_name})
                used.add(file_name)

    for file_name in outlet_files:
        if file_name not in used:
            remaining.append(file_name)

    if remaining:
        grouped.append({"label": "── Other Outlet Layers ──", "value": "__other_outlets__", "disabled": True})
        for file_name in sorted(remaining, key=_humanize_outlet_label):
            grouped.append({"label": _humanize_outlet_label(file_name), "value": file_name})

    return grouped


accessibility_outlet_options_addis = _build_accessibility_outlet_options_addis(outlets_geojson_files_addis)

# Loading GeoJSON files for Isochrones (30-minute accessibility polygons)
isochrones_path = os.path.join(addis_food_env_dir, "isochrones_addis_all")
#isochrones_geojson_files_addis = sorted(os.listdir(isochrones_path)) if os.path.exists(isochrones_path) else []
summary_stats_path_addis = os.path.join(addis_food_env_dir, "addis_HRSL_diet_env_subcities.geojson")
gdf_summary_stats_addis = gpd.read_file(summary_stats_path_addis).to_crs('EPSG:4326')
#walking_segments_addis = gpd.read_file(os.path.join(addis_food_env_dir, "addis_walking_segments_lst_canopy.geojson")).to_crs('EPSG:4326')
hex_vars_addis = gpd.read_file(os.path.join(addis_food_env_dir, "population_othervars_hexgrid.geojson")).to_crs('EPSG:4326')
hex_vars_addis_geojson = json.loads(hex_vars_addis.to_crs("EPSG:4326").to_json())

accessibility_zonal_stats_path_addis = os.path.join(addis_food_env_dir, "accessibility_zonal_stats_percentage.csv")


def _load_accessibility_zonal_stats(path):
    if not os.path.exists(path):
        return pd.DataFrame(), [], [], []

    df = pd.read_csv(path).drop(columns=["Unnamed: 0"], errors="ignore")
    for col in ["index", "time"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["pop_cat", "offer_cat", "mode"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    subcity_cols = [
        col for col in df.columns
        if col not in {"index", "pop_cat", "offer_cat", "mode", "time"}
    ]

    population_labels = {
        "total": "Total",
        "men": "Men",
        "women": "Women",
        "youth": "Youth",
        "children_u5": "Children (0-5 years)",
        "women_rep": "Women of Reproductive Age (15-49 years)",
        "elderly": "Elderly (60+ years)",
    }
    population_options = [
        {"label": population_labels.get(pop, pop.replace("_", " ").title()), "value": pop}
        for pop in sorted(df["pop_cat"].dropna().astype(str).unique())
    ]
    offer_options = [
        {"label": offer.replace("_", " ").title(), "value": offer}
        for offer in sorted(df["offer_cat"].dropna().astype(str).unique())
    ]

    return df, subcity_cols, population_options, offer_options


accessibility_zonal_stats_addis, accessibility_subcity_columns_addis, accessibility_population_options_addis, accessibility_offer_options_addis = _load_accessibility_zonal_stats(accessibility_zonal_stats_path_addis)

# Define food environment metrics and their labels

sub_city_level_metrics = {
                        'density_he': 'Healthy Outlet Density',
                        'density_un': 'Unhealthy Outlet Density',
                        'density_mi': 'Mixed Outlet Density',
                        'ratio_obes': 'Obesogenic Ratio',
                        'children_u5': 'Children (0-5 years)', 
                        'elderly': 'Elderly (60+ years)', 
                        'women_rep': 'Women of Reproductive Age (15-49 years)', 
                        'youth': 'Youth (15-24 years)', 
                        'men': 'Men', 
                        'women': 'Women', 
                        'total': 'Total'} 

cols_labels_hex_vars = {'children_u5': 'Children (0-5 years)', 
                        'elderly': 'Elderly (60+ years)', 
                        'women_rep': 'Women of Reproductive Age (15-49 years)', 
                        'youth': 'Youth (15-24 years)', 
                        'men': 'Men', 
                        'women': 'Women', 
                        'total': 'Total', 
                        'canopy_cover_pixels': 'Canopy Cover (m²)', 
                        'mean_lst': 'Average Land Surface Temperature (°C)'}

REGION_COLOURS = {
    "Red River Delta":    "#e63946",
    "Northeast":          "#457b9d",
    "Northwest":          "#2a9d8f",
    "North Central Coast":"#e9c46a",
    "South Central Coast":"#f4a261",
    "Central Highlands":  "#264653",
    "Southeast":          "#a8dadc",
    "Mekong Delta":       "#06d6a0",
}

# Color schemes for choropleth
green_scale = ['#e3f6d5', '#c1d88e', '#a5be91', '#6f946d', '#3a6649']
red_scale = ['#fee5d9', '#fcbba1', '#fc9272', '#fb6a4a', '#de2d26']
grey_scale = ['#f7f7f7', '#d9d9d9', '#bdbdbd', '#969696', '#636363']


# Food-environment choropleth palettes
# Plotly equivalents for requested styles: RdOrYl_r and GnYl_r
FOOD_ENV_NEG_SCALE = "YlOrRd"
FOOD_ENV_POS_SCALE = "YlGn"
FOOD_ENV_NEUTRAL_BONE_SCALE = [
    [0.00, "#fffdf8"],
    [0.25, "#f7f1e3"],
    [0.50, "#eadfc8"],
    [0.75, "#d8c9ab"],
    [1.00, "#c5b395"],
]
VIRIDIS_SCALE = "Viridis"
BLUES_SCALE = "Blues"
YLORBR_SCALE = "YlOrBr"
HOT_SCALE = "Hot"


metric_direction =      {'density_he': FOOD_ENV_POS_SCALE,
                        'density_un': FOOD_ENV_NEG_SCALE,
                        'density_mi': FOOD_ENV_NEUTRAL_BONE_SCALE,
                        'ratio_obes': FOOD_ENV_NEG_SCALE,
                        'children_u5': YLORBR_SCALE, 
                        'elderly': YLORBR_SCALE, 
                        'women_rep': YLORBR_SCALE, 
                        'youth': YLORBR_SCALE, 
                        'men': YLORBR_SCALE, 
                        'women': YLORBR_SCALE, 
                        'total': YLORBR_SCALE,
                        'canopy_cover_pixels': FOOD_ENV_POS_SCALE,
                        'mean_lst': HOT_SCALE}

# Loading supply flow data for Sankey Diagram
df_sankey = pd.read_csv(os.path.join(hanoi_supply_dir, 'hanoi_supply.csv'))

df_policies_addis = pd.read_csv(os.path.join(addis_policy_dir, 'addis_policy_database_faolex.csv'))#.drop('Unnamed: 0',axis=1)
# Ensure link columns render as markdown links in the DataTable
if 'Document URL' in df_policies_addis.columns:
    df_policies_addis['Document URL'] = df_policies_addis['Document URL'].apply(
        lambda x: f'[Link Available]({x})' if x and str(x).startswith('http') else '--'
    )

if 'Record URL' in df_policies_addis.columns:
    df_policies_addis['Record URL'] = df_policies_addis['Record URL'].apply(
        lambda x: f'[Link Available]({x})' if x and str(x).startswith('http') else '--'
    )

if 'Available website' in df_policies_addis.columns:
    df_policies_addis['Available website'] = df_policies_addis['Available website'].apply(
        lambda x: f'[Link Available]({x})' if x and str(x).startswith('http') else '--'
    )

df_indicators = pd.read_csv(os.path.join(addis_policy_dir, 'addis_policy_database_expanded_sdg.csv'))

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

df_env = pd.read_csv(os.path.join(addis_environment_dir, 'addis_lca_pivot.csv'))
df_lca = df_env  # Alias for compatibility

# -------------------------- Loading Hanoi Data ------------------------- #

# Hanoi MPI Data (commune level)
MPI_hanoi = gpd.read_file(os.path.join(hanoi_mpi_dir, "hanoi_communes.geojson"))
MPI_hanoi['Name'] = MPI_hanoi['Name'].astype(str)
MPI_hanoi['ma_xa'] = MPI_hanoi['ma_xa'].astype(str)

# Load long-format MPI CSV and pivot to wide, then merge into GeoDataFrame
df_mpi_hanoi = pd.read_csv(os.path.join(hanoi_mpi_dir, "hanoi_communes_MPI_long.csv"))
df_mpi_wide = df_mpi_hanoi.pivot_table(index='Name', columns='Variable', values='Value').reset_index()
df_mpi_wide.columns.name = None
MPI_hanoi = MPI_hanoi.merge(df_mpi_wide, on='Name', how='left')

# Detect numeric MPI columns (all columns added from the pivot)
geo_vars = []
for _col in MPI_hanoi.columns:
    if _col in ['geometry', 'Name', 'ma_xa']:
        continue
    coerced = pd.to_numeric(MPI_hanoi[_col], errors='coerce')
    if coerced.notna().any():
        MPI_hanoi[_col] = coerced
        geo_vars.append(_col)

geojson_hanoi = json.loads(MPI_hanoi.to_json())

# Hanoi Stakeholders Data
df_sh_hanoi = pd.read_csv(os.path.join(hanoi_stakeholders_dir, "hanoi_stakeholders.csv")).dropna(how='any').astype(str)

if 'Website' in df_sh_hanoi.columns:
    df_sh_hanoi['Website'] = df_sh_hanoi['Website'].apply(
        lambda x: f'[Link Available]({x})' if x and x.startswith('http') else '--'
    )

# Hanoi policy database
df_policies_hanoi = pd.read_csv(os.path.join(hanoi_policy_dir, 'hanoi_policy_database_cleaned.csv'))#.drop('Unnamed: 0',axis=1)

if 'Document Link' in df_policies_hanoi.columns:
    df_policies_hanoi['Document Link'] = df_policies_hanoi['Document Link'].apply(
        lambda x: f'[Link Available]({x})' if x and str(x).startswith('http') else '--'
    )

    df_policies_hanoi['Available website'] = df_policies_hanoi['Available website'].apply(
        lambda x: f'[Link Available]({x})' if x and str(x).startswith('http') else '--'
    )

# Loading GeoJSON files for Food Outlets
outlets_path_hanoi = os.path.join(hanoi_food_env_dir, "jsons_hanoi_foodoutlets")
outlets_geojson_files_hanoi = sorted(os.listdir(outlets_path_hanoi))

# Hanoi food-environment choropleth (minified base geometry + values CSV when available)
food_env_path_hanoi = os.path.join(hanoi_food_env_dir, "hanoi_diet_env_mapping.geojson")
food_env_values_path_hanoi = os.path.join(hanoi_food_env_dir, "hanoi_diet_env_mapping_values.csv")
gdf_food_env_hanoi = None
try:
    gdf_food_env_hanoi = _load_food_env_layer(
        food_env_path_hanoi,
        food_env_values_path_hanoi,
        join_key_candidates=["ma_xa", "shapeID", "Dist_Name", "Dist_name"],
    )
except Exception as e:
    print(f"Error loading Hanoi food environment layer: {e}")

# Loading GeoJSON files for Isochrones (30-minute accessibility polygons)
isochrones_path_hanoi = os.path.join(hanoi_food_env_dir, "isochrones_hanoi")
isochrones_geojson_files_hanoi = sorted(os.listdir(isochrones_path_hanoi)) if os.path.exists(isochrones_path_hanoi) else []

# Hanoi affordability data
df_affordability_hanoi = pd.read_csv(os.path.join(hanoi_affordability_dir, 'hanoi_affordability_cleaned.csv'))

# Hanoi dietary data
df_diet_2_hanoi = pd.read_csv(os.path.join(hanoi_nutrition_dir, 'hanoi_health_nutrition_cleaned.csv'))


def _load_indicator_atlas_records(csv_path):
    if not os.path.exists(csv_path):
        return []

    rows = None
    for enc in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
        try:
            with open(csv_path, newline='', encoding=enc) as f:
                rows = list(csv.reader(f))
            break
        except UnicodeDecodeError:
            continue

    # Last-resort fallback: preserve row structure while replacing undecodable bytes.
    if rows is None:
        with open(csv_path, 'rb') as f:
            text = f.read().decode('utf-8', errors='replace')
        rows = list(csv.reader(StringIO(text)))

    if len(rows) < 2:
        return []

    # Find the real header row dynamically (some files include a title/metadata row first).
    header_idx = None
    for idx, row in enumerate(rows):
        normalized = [str(c).strip() for c in row]
        if 'Domain / Sub-theme' in normalized and 'Indicator name' in normalized:
            header_idx = idx
            break

    if header_idx is None:
        return []

    header = [str(c).strip() for c in rows[header_idx]]
    records = []
    for row in rows[header_idx + 1:]:
        if not any((c or '').strip() for c in row):
            continue
        if len(row) < len(header):
            row = row + [''] * (len(header) - len(row))
        rec = dict(zip(header, row[:len(header)]))
        indicator_name = (rec.get('Indicator name') or '').strip()
        if not indicator_name:
            continue
        records.append(rec)
    return records


atlas_records = _load_indicator_atlas_records(atlas_csv_path)
#print(f"DEBUG: Loaded {len(atlas_records)} records from indicator atlas CSV, Example: {atlas_records[:1]}")


# ── commune climate indicators ───────────────────────────────────────────────
_climate_csv  = os.path.join(hanoi_climate_dir, "vietnam_climate_resilience_quarterly_v1.csv")
_communes_path = os.path.join(hanoi_climate_dir, "resilience_communes_base_2025.geojson")
_islands_path = os.path.join(hanoi_resilience_dir, "vnm_islands.geojson")

_lulc_stats_csv = os.path.join(hanoi_resilience_dir, "lulc_stats.csv")
_communes_geojson_path = os.path.join(hanoi_mpi_dir, "hanoi_communes.geojson")
_region_quarterly_path = os.path.join(hanoi_climate_dir, "regional_quarterly_climate.csv")
_slopes_path = os.path.join(hanoi_climate_dir, "regional_indicator_slopes.csv")


@lru_cache(maxsize=1)
def _get_resilience_context():
    commune_climate_df = pd.read_csv(_climate_csv).reset_index()
    commune_climate_df["quarter"] = commune_climate_df["quarter"].astype(str)
    if "shapeID" in commune_climate_df.columns:
        commune_climate_df["shapeID"] = commune_climate_df["shapeID"].astype(str)

    resilience_gdf = _read_geojson_cached(_communes_path).copy()

    # Prefer shapeID for commune joins when available; shapeName can be ambiguous.
    if ("shapeID" in resilience_gdf.columns) and ("shapeID" in commune_climate_df.columns):
        join_key = "shapeID"
        featureidkey = "properties.shapeID"
        communes_unique = (
            resilience_gdf[["shapeID", "shapeName", "geometry"]]
            .dissolve(by="shapeID", as_index=False)
            .reset_index(drop=True)
        )
    else:
        join_key = "shapeName"
        featureidkey = "properties.shapeName"
        communes_unique = (
            resilience_gdf[["shapeName", "geometry"]]
            .dissolve(by="shapeName", as_index=False)
            .reset_index(drop=True)
        )

    return {
        "commune_climate_df": commune_climate_df,
        "communes_unique": communes_unique,
        "resilience_base_geojson": json.loads(communes_unique.to_json()),
        "join_key": join_key,
        "featureidkey": featureidkey,
        "all_quarters": tuple(sorted(commune_climate_df["quarter"].unique())),
    }


@lru_cache(maxsize=1)
def _get_lulc_context():
    lulc_stats_gdf = None
    indicator_options = []
    map_center = {"lat": 21.03, "lon": 105.85}

    if os.path.exists(_lulc_stats_csv) and os.path.exists(_communes_geojson_path):
        try:
            communes_gdf = _read_geojson_cached(_communes_geojson_path).copy()
            lulc_df = pd.read_csv(_lulc_stats_csv)
            lulc_stats_gdf = gpd.GeoDataFrame(
                pd.concat(
                    [communes_gdf.set_index("Name"), lulc_df.set_index("Name").drop(columns=["ma_xa"], errors="ignore")],
                    axis=1,
                    join="inner",
                ).reset_index(),
                geometry="geometry",
                crs="EPSG:4326",
            )
            lulc_stats_gdf["geometry"] = lulc_stats_gdf["geometry"].buffer(0)
            lulc_stats_gdf = lulc_stats_gdf[lulc_stats_gdf["geometry"].is_valid & ~lulc_stats_gdf["geometry"].is_empty].copy()
            lulc_stats_gdf["__rid"] = lulc_stats_gdf["ma_xa"].astype(str)

            if not lulc_stats_gdf.empty:
                minx, miny, maxx, maxy = lulc_stats_gdf.total_bounds
                map_center = {
                    "lat": float((miny + maxy) / 2.0),
                    "lon": float((minx + maxx) / 2.0),
                }

            excluded_lulc_cols = {"Name", "ma_xa", "geometry", "__rid"}
            lulc_columns = []
            for c in lulc_stats_gdf.columns:
                if c in excluded_lulc_cols:
                    continue
                numeric_vals = pd.to_numeric(lulc_stats_gdf[c], errors="coerce")
                if numeric_vals.notna().any():
                    lulc_columns.append(c)

            indicator_options = [{"label": c, "value": c} for c in lulc_columns]
        except Exception as exc:
            print(f"[WARN] Could not load LULC stats: {exc}")

    return {
        "gdf": lulc_stats_gdf,
        "indicator_options": indicator_options,
        "map_center": map_center,
    }


@lru_cache(maxsize=1)
def _get_region_quarterly_context():
    return {
        "region_quarterly": pd.read_csv(_region_quarterly_path),
        "slopes_df": pd.read_csv(_slopes_path),
    }

# Paths for cached EMDAT parquet files (resilience)
EMDAT_COUNTS_PQ = os.path.join(hanoi_resilience_dir, "emdat_counts.parquet")
EMDAT_TOTALS_PQ = os.path.join(hanoi_resilience_dir, "emdat_totals.parquet")
EMDAT_COUNTS_CSV = os.path.join(hanoi_resilience_dir, "emdat_counts.csv")
EMDAT_TOTALS_CSV = os.path.join(hanoi_resilience_dir, "emdat_totals.csv")

def _load_emdat_cached():
    if os.path.exists(EMDAT_COUNTS_PQ) and os.path.exists(EMDAT_TOTALS_PQ):
        try:
            df_counts = pd.read_parquet(EMDAT_COUNTS_PQ)
            df_totals = pd.read_parquet(EMDAT_TOTALS_PQ)
            return df_counts, df_totals
        except Exception as exc:
            print(f"[WARN] Could not read EMDAT parquet cache: {exc}")

    # Fallback for environments where parquet engine is unavailable (e.g., hosted deploys)
    if os.path.exists(EMDAT_COUNTS_CSV) and os.path.exists(EMDAT_TOTALS_CSV):
        try:
            df_counts = pd.read_csv(EMDAT_COUNTS_CSV)
            df_totals = pd.read_csv(EMDAT_TOTALS_CSV)
            return df_counts, df_totals
        except Exception as exc:
            print(f"[WARN] Could not read EMDAT CSV cache: {exc}")
            return None, None

    return None, None

@lru_cache(maxsize=8)
def _build_resilience_figure_cached(size_max, counts_pq_mtime, totals_pq_mtime, counts_csv_mtime, totals_csv_mtime):
    df_counts, df_totals = _load_emdat_cached()
    fig = build_resilience_figure_from_cache(df_counts=df_counts, df_totals=df_totals, size_max=size_max)
    return fig.to_json()


def build_resilience_figure_from_cache(df_counts=None, df_totals=None, size_max=40):
    if df_counts is None and df_totals is None:
        return _figure_from_json(
            _build_resilience_figure_cached(
                size_max,
                _path_mtime(EMDAT_COUNTS_PQ),
                _path_mtime(EMDAT_TOTALS_PQ),
                _path_mtime(EMDAT_COUNTS_CSV),
                _path_mtime(EMDAT_TOTALS_CSV),
            )
        )

    if df_counts is None or df_totals is None:
        df_counts, df_totals = _load_emdat_cached()
        if df_counts is None or df_totals is None:
            empty = go.Figure()
            empty.add_annotation(text="EMDAT cache not found", showarrow=False, xref='paper', yref='paper', x=0.5, y=0.5, font=dict(size=12))
            empty.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=420)
            return empty

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.9, 0.4], vertical_spacing=0.06)

    counts = df_counts.copy()
    counts["Year"] = pd.to_numeric(counts["Year"], errors="coerce")
    counts["Count"] = pd.to_numeric(counts["Count"], errors="coerce")
    counts = counts.dropna(subset=["Year", "Disaster Subtype", "Count"])

    if not counts.empty:
        max_count = float(max(counts["Count"].max(), 1.0))
        size_ref = 2.0 * max_count / (max(size_max, 1) ** 2)

        for subgroup, sub in counts.groupby("Disaster Subgroup", dropna=False):
            subgroup_label = "Unknown" if pd.isna(subgroup) else str(subgroup)
            fig.add_trace(
                go.Scatter(
                    x=sub["Year"],
                    y=sub["Disaster Subtype"],
                    mode="markers",
                    marker=dict(
                        size=sub["Count"].clip(lower=1),
                        sizemode="area",
                        sizeref=size_ref,
                        sizemin=4,
                    ),
                    name=subgroup_label,
                    showlegend=False,
                    customdata=np.column_stack([
                        sub["Count"].to_numpy(),
                        np.full(len(sub), subgroup_label),
                    ]),
                    hovertemplate=(
                        "Year: %{x}<br>"
                        "Subtype: %{y}<br>"
                        "Subgroup: %{customdata[1]}<br>"
                        "Count: %{customdata[0]}<extra></extra>"
                    ),
                ),
                row=1,
                col=1,
            )

    totals = df_totals.copy()
    totals["Year"] = pd.to_numeric(totals["Year"], errors="coerce")
    totals["TotalAffected"] = pd.to_numeric(totals["TotalAffected"], errors="coerce")
    totals = totals.dropna(subset=["Year", "TotalAffected"])

    if not totals.empty:
        fig.add_trace(
            go.Bar(
                x=totals["Year"],
                y=totals["TotalAffected"],
                marker_color="orangered",
                hovertemplate="Year: %{x}<br>Total Affected: %{y:,}<extra></extra>",
                showlegend=False,
            ),
            row=2,
            col=1,
        )

    fig.update_yaxes(title_text=None, row=1, col=1, automargin=True)
    fig.update_yaxes(title_text="Total Affected", row=2, col=1, automargin=True)
    fig.update_yaxes(tickfont=dict(size=11))
    fig.update_xaxes(dtick=1, tickangle=90)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=550, template='plotly_white', showlegend=False)
    fig.update_yaxes(row=2, col=1, tickformat=",", separatethousands=True)
    return fig


def _build_emdat_events_figure(size_max=20):
    df_counts, _ = _load_emdat_cached()
    if df_counts is None:
        empty = go.Figure()
        empty.add_annotation(text="EMDAT cache not found", showarrow=False, xref='paper', yref='paper', x=0.5, y=0.5, font=dict(size=12))
        empty.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=350)
        return empty
    fig = go.Figure()
    counts = df_counts.copy()
    counts["Year"] = pd.to_numeric(counts["Year"], errors="coerce")
    counts["Count"] = pd.to_numeric(counts["Count"], errors="coerce")
    counts = counts.dropna(subset=["Year", "Disaster Subtype", "Count"])
    if not counts.empty:
        max_count = float(max(counts["Count"].max(), 1.0))
        size_ref = 2.0 * max_count / (max(size_max, 1) ** 2)
        for subgroup, sub in counts.groupby("Disaster Subgroup", dropna=False):
            subgroup_label = "Unknown" if pd.isna(subgroup) else str(subgroup)
            fig.add_trace(go.Scatter(
                x=sub["Year"],
                y=sub["Disaster Subtype"],
                mode="markers",
                marker=dict(size=sub["Count"].clip(lower=1), sizemode="area", sizeref=size_ref, sizemin=4),
                name=subgroup_label,
                showlegend=False,
                customdata=np.column_stack([sub["Count"].to_numpy(), np.full(len(sub), subgroup_label)]),
                hovertemplate="Year: %{x}<br>Subtype: %{y}<br>Subgroup: %{customdata[1]}<br>Count: %{customdata[0]}<extra></extra>",
            ))
    fig.update_yaxes(title_text=None, automargin=True, tickfont=dict(size=11))
    fig.update_xaxes(dtick=1, tickangle=90)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=350, template='plotly_white', showlegend=False)
    return fig


def _build_emdat_affected_figure():
    _, df_totals = _load_emdat_cached()
    if df_totals is None:
        empty = go.Figure()
        empty.add_annotation(text="EMDAT cache not found", showarrow=False, xref='paper', yref='paper', x=0.5, y=0.5, font=dict(size=12))
        empty.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=350)
        return empty
    fig = go.Figure()
    totals = df_totals.copy()
    totals["Year"] = pd.to_numeric(totals["Year"], errors="coerce")
    totals["TotalAffected"] = pd.to_numeric(totals["TotalAffected"], errors="coerce")
    totals = totals.dropna(subset=["Year", "TotalAffected"])
    if not totals.empty:
        fig.add_trace(go.Bar(
            x=totals["Year"],
            y=totals["TotalAffected"],
            marker_color="orangered",
            hovertemplate="Year: %{x}<br>Total Affected: %{y:,}<extra></extra>",
            showlegend=False,
        ))
    fig.update_yaxes(title_text="Total Affected", automargin=True, tickformat=",", separatethousands=True, tickfont=dict(size=11))
    fig.update_xaxes(dtick=1, tickangle=90)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=350, template='plotly_white', showlegend=False)
    return fig


@app.callback(
    Output('resilience-emdat-events-graph', 'figure'),
    Output('resilience-emdat-affected-graph', 'figure'),
    Input('selected-city', 'data')
)
def update_resilience_emdat(selected_city):
    return _build_emdat_events_figure(size_max=20), _build_emdat_affected_figure()


@app.callback(
    Output('emdat-events-container', 'style'),
    Output('emdat-affected-container', 'style'),
    Output('emdat-tab-events', 'className'),
    Output('emdat-tab-affected', 'className'),
    Input('emdat-tab-events', 'n_clicks'),
    Input('emdat-tab-affected', 'n_clicks'),
    prevent_initial_call=True,
)
def toggle_emdat_tab(n_events, n_affected):
    trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'emdat-tab-events'
    active = 'affected' if trigger == 'emdat-tab-affected' else 'events'
    show = {"display": "block"}
    hide = {"display": "none"}
    if active == 'events':
        return show, hide, "emdat-tab-active", "emdat-tab-inactive"
    return hide, show, "emdat-tab-inactive", "emdat-tab-active"


@app.callback(
    Output("resilience-indicator-pillar-collapse-1", "is_open"),
    Output("resilience-indicator-pillar-collapse-2", "is_open"),
    Output("resilience-indicator-pillar-collapse-3", "is_open"),
    Input("resilience-indicator-pillar-toggle-1", "n_clicks"),
    Input("resilience-indicator-pillar-toggle-2", "n_clicks"),
    Input("resilience-indicator-pillar-toggle-3", "n_clicks"),
    State("resilience-indicator-pillar-collapse-1", "is_open"),
    State("resilience-indicator-pillar-collapse-2", "is_open"),
    State("resilience-indicator-pillar-collapse-3", "is_open"),
    prevent_initial_call=True,
)
def toggle_resilience_indicator_pillars(n1, n2, n3, open1, open2, open3):
    ctx = dash.callback_context
    if not ctx.triggered:
        return open1, open2, open3

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    state_map = {
        "resilience-indicator-pillar-toggle-1": open1,
        "resilience-indicator-pillar-toggle-2": open2,
        "resilience-indicator-pillar-toggle-3": open3,
    }

    if trigger_id not in state_map:
        return open1, open2, open3

    if trigger_id == "resilience-indicator-pillar-toggle-1":
        return (not bool(open1)), open2, open3
    if trigger_id == "resilience-indicator-pillar-toggle-2":
        return open1, (not bool(open2)), open3
    return open1, open2, (not bool(open3))


commune_indicator_cfg = {
    "ag_area_ha":                    {"col": "ag_area_ha",                  "label": "Agricultural Area (ha)",                  "colorscale": "YlGn",     "diverging": False, "vmin": "0", "vmax": "10000" },   
    "grace_trend":                   {"col": "grace_trend",                 "label": "Terrestrial Water Storage Anomaly (mm)",  "colorscale": "RdYlBu",   "diverging": True, "vmin": "-30", "vmax": "30" },
    "vci_severe_pct":                {"col": "vci_severe_pct",              "label": "Cropland Area Under Severe Drought (%)",  "colorscale": "RdYlGn_r", "diverging": False, "vmin": "0", "vmax": "100" },
    "drought_resistance":            {"col": "drought_resistance",          "label": "Vegetation Drought Resistance (SPEI6)",   "colorscale": "RdYlGn",   "diverging": False, "vmin": "0", "vmax": "1" },
    #"flood_resistance":              {"col": "flood_resistance",            "label": "Vegetation Flood Resistance (SPEI6)",     "colorscale": "RdYlBu",   "diverging": False, "vmin": "0", "vmax": "1" },
    "class_-3_months_SPEI3":         {"col": "class_-3_months_SPEI3",       "label": "SPEI-3 Moderate Drought Frequency",       "colorscale": "YlOrRd",   "diverging": False, "vmin": "0", "vmax": "150" },
    "class_-2_months_SPEI3":         {"col": "class_-2_months_SPEI3",       "label": "SPEI-3 Severe Drought Frequency",         "colorscale": "YlOrRd",   "diverging": False, "vmin": "0", "vmax": "100" },
    "class_-1_months_SPEI3":         {"col": "class_-1_months_SPEI3",       "label": "SPEI-3 Extreme Drought Frequency",        "colorscale": "YlOrRd",   "diverging": False, "vmin": "0", "vmax": "50" },
    "class_-3_months_SPEI6":         {"col": "class_-3_months_SPEI6",       "label": "SPEI-6 Moderate Drought Frequency",       "colorscale": "YlOrRd",   "diverging": False, "vmin": "0", "vmax": "150" },
    "class_-2_months_SPEI6":         {"col": "class_-2_months_SPEI6",       "label": "SPEI-6 Severe Drought Frequency",         "colorscale": "YlOrRd",   "diverging": False, "vmin": "0", "vmax": "100" },
    "class_-1_months_SPEI6":         {"col": "class_-1_months_SPEI6",       "label": "SPEI-6 Extreme Drought Frequency",        "colorscale": "YlOrRd",   "diverging": False, "vmin": "0", "vmax": "50" },
    "class_-3_months_SPEI12":        {"col": "class_-3_months_SPEI12",      "label": "SPEI-12 Moderate Drought Frequency",      "colorscale": "YlOrRd",   "diverging": False, "vmin": "0", "vmax": "150"},
    "class_-2_months_SPEI12":        {"col": "class_-2_months_SPEI12",      "label": "SPEI-12 Severe Drought Frequency",        "colorscale": "YlOrRd",   "diverging": False, "vmin": "0", "vmax": "100"},
    "class_-1_months_SPEI12":        {"col": "class_-1_months_SPEI12",      "label": "SPEI-12 Extreme Drought Frequency",       "colorscale": "YlOrRd",   "diverging": False, "vmin": "0", "vmax": "50"},
}


# -------------------------- Defining Custom Styles ------------------------- #

tabs_style = {
                "backgroundColor": brand_colors['Light green'],
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


ATLAS_SECTIONS = [
    ("Diets, Nutrition & Health", "tab-10-nutrition"),
    ("Environment, Natural Resources & Production", "tab-3-sustainability"),
    ("Livelihoods, Poverty & Equity", "tab-4-poverty"),
    ("Governance", "tab-9-policies"),
    ("Resilience", "tab-6-resilience"),
    ("Uncategorized", "tab-home"),
]

ATLAS_CITY_TABS = {
    "hanoi": {
        "tab-1-stakeholders", "tab-2-supply", "tab-3-sustainability", "tab-4-poverty",
        "tab-6-resilience", "tab-7-food-environments", "tab-9-policies", "tab-10-nutrition",
        "tab-home",
    },
    "addis": {
        "tab-1-stakeholders", "tab-2-supply", "tab-3-sustainability", "tab-4-poverty",
        "tab-6-resilience", "tab-7-food-environments", "tab-9-policies", "tab-10-nutrition", "tab-11-footprints",
        "tab-home",
    },
}


def _normalize_indicator_name(name):
    normalized = (name or '').strip().lower().replace('&', ' and ')
    return ' '.join(normalized.split())


ATLAS_UNAVAILABLE_BOTH_INDICATORS = {
    _normalize_indicator_name('Active Urban Mobility'),
    _normalize_indicator_name('Percent access to Cost of affordable diets'),
    _normalize_indicator_name('Cost and affordability of healthy diets'),
    _normalize_indicator_name('Water & Air Quality'),
    _normalize_indicator_name('Food poisoning'),
    _normalize_indicator_name('Prevalence of adult hypertension'),
    _normalize_indicator_name('Prevalence of adult diabetes'),
    _normalize_indicator_name('Cost of affordable diets')
}

ATLAS_UNAVAILABLE_HANOI_INDICATORS = {
    _normalize_indicator_name('Prevalence of obesity and overweight for women'),
    _normalize_indicator_name('Percent access to unhealthy food'),
    _normalize_indicator_name('Percent access to healthy food'),
    _normalize_indicator_name('Food price resilience indicator'),
}

ATLAS_UNAVAILABLE_ADDIS_INDICATORS = {
    _normalize_indicator_name('Food Expenditure as a portion of Total Expenditure'),
    _normalize_indicator_name('Food Expenditure as a portion of Household Income'),
}


def _is_indicator_available_for_city(indicator_name, city, target_tab):
    if target_tab not in ATLAS_CITY_TABS.get(city, set()):
        return False

    normalized_name = _normalize_indicator_name(indicator_name)
    if normalized_name in ATLAS_UNAVAILABLE_BOTH_INDICATORS:
        return False

    if city == 'hanoi' and normalized_name in ATLAS_UNAVAILABLE_HANOI_INDICATORS:
        return False

    if city == 'addis' and normalized_name in ATLAS_UNAVAILABLE_ADDIS_INDICATORS:
        return False

    return True


def _atlas_target_for_record(rec):
    domain = (rec.get('Domain / Sub-theme') or '').lower()
    theme = (rec.get('Theme') or '').lower()
    name = (rec.get('Indicator name') or '').lower()
    pillars = (rec.get('Pillars') or '').lower()

    pillar_text = f"{pillars} {domain} {theme} {name}"

    # First map to the new high-level pillar groups for atlas display.
    if ('resilience' in pillar_text) or ('resilience' in domain) or ('resilience' in theme):
        if any(k in pillar_text for k in ['land-use & land-cover distribution']):
            return "Resilience", "tab-6-resilience", "Land-use & Land-cover"
        if any(k in pillar_text for k in ['agricultural climate resilience indicator', 'water storage anomalies', 'natural disasters database']):
            return "Resilience", "tab-6-resilience", "Biophysical shocks"
        if any(k in pillar_text for k in ['food price resilience indicator']):
            return "Resilience", "tab-6-resilience", "Socio-Economic Shocks"
        return "Resilience", "tab-6-resilience", "Resilience Indicator Trends"

    if any(k in pillar_text for k in ['diets', 'nutrition', 'health', 'food safety', 'food environments', 'affordability', 'afford']):
        # Route atlas cards to the most relevant existing data view.
        if any(k in pillar_text for k in ['food environments', 'affordability', 'afford']):
            return "Diets, Nutrition & Health", "tab-7-food-environments", None
        return "Diets, Nutrition & Health", "tab-10-nutrition", None

    if any(k in pillar_text for k in ['environment', 'natural resources', 'production', 'sustainability', 'footprint', 'life cycle', 'loss', 'waste']):
        if any(k in pillar_text for k in ['footprint', 'life cycle']):
            return "Environment, Natural Resources & Production", "tab-11-footprints", None
        if any(k in pillar_text for k in ['loss', 'waste']):
            return "Environment, Natural Resources & Production", "tab-8-losses", None
        return "Environment, Natural Resources & Production", "tab-3-sustainability", None

    if any(k in pillar_text for k in ['livelihoods', 'poverty', 'equity', 'labour', 'skills', 'green jobs']):
        if any(k in pillar_text for k in ['labour', 'skills', 'green jobs']):
            return "Livelihoods, Poverty & Equity", "tab-5-labour", None
        return "Livelihoods, Poverty & Equity", "tab-4-poverty", None

    if any(k in pillar_text for k in ['governance', 'policy', 'stakeholder', 'flow', 'supply chain', 'value chain', 'behaviour', 'behavior', 'chatbot', 'game']):
        if any(k in pillar_text for k in ['stakeholder']):
            return "Governance", "tab-1-stakeholders", None
        if any(k in pillar_text for k in ['flow', 'supply chain', 'value chain']):
            return "Governance", "tab-2-supply", None
        if any(k in pillar_text for k in ['behaviour', 'behavior', 'chatbot', 'game']):
            return "Governance", "tab-12-behaviour", None
        return "Governance", "tab-9-policies", None

    return "Uncategorized", "tab-home", None


_ALL_TAB_IDS = [
    "tab-home", "tab-1-stakeholders", "tab-2-supply", "tab-3-sustainability",
    "tab-4-poverty", "tab-5-labour", "tab-6-resilience", "tab-7-food-environments",
    "tab-8-losses", "tab-9-policies", "tab-10-nutrition", "tab-11-footprints",
    "tab-12-behaviour",
]

def _hidden_tab_stubs():
    """Hidden zero-click buttons for every tab id so Dash callbacks never see missing inputs."""
    return html.Div(
        [html.Button(id=tid, n_clicks=0, style={"display": "none"}) for tid in _ALL_TAB_IDS],
        style={"display": "none"},
    )


def indicator_atlas_layout_hanoi(records, initial_section=None):
    section_map = {title: [] for title, _ in ATLAS_SECTIONS}

    for idx, rec in enumerate(records):
        section_title, target_tab, target_subview = _atlas_target_for_record(rec)
        indicator_name = (rec.get('Indicator name') or '').strip()
        definition = (rec.get('Definition (what the indicator measures)') or '').strip()
        relevance = (rec.get('Relevance (why it matters for the project)') or '').strip()
        source = (rec.get('Data source') or '').strip()
        hanoi_available = str(rec.get('Available Hanoi', '1')).strip() == '1'
        addis_available = str(rec.get('Available Addis', '1')).strip() == '1'

        section_map.setdefault(section_title, []).append(
            dbc.Card(
                dbc.CardBody([
                    html.H6(indicator_name, style={"fontWeight": "bold", "marginBottom": "6px", "color": brand_colors['Brown']}),
                    html.P(definition or "No definition available.", style={"fontSize": "0.88em", "marginBottom": "6px", "color": "#333"}),
                    html.P(relevance or "No relevance note available.", style={"fontSize": "0.85em", "marginBottom": "6px", "color": "#555"}),
                    html.Div([
                        html.Span("Source: ", style={"fontWeight": "bold"}),
                        html.Span(source or "Not specified")
                    ], style={"fontSize": "0.8em", "color": "#777", "marginBottom": "12px"}),
                    html.Div([
                        dbc.Button(
                            "View Data - Hanoi",
                            id={
                                "type": "atlas-view-btn",
                                "target": target_tab,
                                "subview": target_subview or "",
                                "city": "hanoi",
                                "index": idx,
                            },
                            size="sm",
                            disabled=not hanoi_available,
                            title=None if hanoi_available else "Not available for Hanoi",
                            style={
                                "borderRadius": "6px",
                                "fontWeight": "bold",
                                "backgroundColor": "#ebebeb" if not hanoi_available else brand_colors['Red'],
                                "borderColor": "#ebebeb" if not hanoi_available else brand_colors['Red'],
                                "color": "#bbb" if not hanoi_available else "#ffffff",
                                "cursor": "not-allowed" if not hanoi_available else "pointer",
                            }
                        ),
                        dbc.Button(
                            "View Data - Addis Ababa",
                            id={
                                "type": "atlas-view-btn",
                                "target": target_tab,
                                "subview": target_subview or "",
                                "city": "addis",
                                "index": idx,
                            },
                            size="sm",
                            disabled=not addis_available,
                            title=None if addis_available else "Not available for Addis Ababa",
                            style={
                                "borderRadius": "6px",
                                "fontWeight": "bold",
                                "backgroundColor": "#ebebeb" if not addis_available else brand_colors['Red'],
                                "borderColor": "#ebebeb" if not addis_available else brand_colors['Red'],
                                "color": "#bbb" if not addis_available else "#ffffff",
                                "cursor": "not-allowed" if not addis_available else "pointer",
                            }
                        ),
                    ], style={"display": "flex", "gap": "8px", "flexWrap": "wrap", "marginTop": "auto"}),
                ], style={"display": "flex", "flexDirection": "column", "height": "100%"}),
                style={
                    "borderRadius": "10px",
                    "boxShadow": "0 1px 4px rgba(0,0,0,0.07)",
                    "marginBottom": "0",
                    "backgroundColor": "#ffffff",
                    "border": "1px solid #eee",
                    "height": "100%",
                }
            )
        )

    section_order = [title for title, _ in ATLAS_SECTIONS]
    if initial_section in section_map:
        section_order = [initial_section] + [s for s in section_order if s != initial_section]

    section_blocks = []
    for title in section_order:
        cards = section_map.get(title, [])
        if not cards:
            continue
        # Fixed 2-column grid — all cards same width regardless of count
        card_cols = [
            dbc.Col(card, xs=12, md=6, style={"marginBottom": "16px", "display": "flex"})
            for card in cards
        ]
        section_blocks.append(
            html.Div([
                html.Div([
                    html.H4(title, style={
                        "margin": 0,
                        "fontWeight": "bold",
                        "color": brand_colors['Brown'],
                        "fontSize": "1.15em",
                    }),
                ], style={
                    "borderLeft": f"4px solid {brand_colors['Dark green']}",
                    "paddingLeft": "12px",
                    "marginBottom": "14px",
                    "marginTop": "6px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between",
                }),
                dbc.Row(card_cols, className="g-3"),
            ], style={"marginBottom": "32px"})
        )

    if not section_blocks:
        section_blocks = [
            dbc.Alert(
                [
                    html.Strong("No indicator records loaded."),
                    html.Div("Check that the atlas CSV contains 'Domain / Sub-theme' and 'Indicator name' columns and at least one populated indicator row."),
                ],
                color="warning",
                style={"margin": "8px"},
            )
        ]

    return html.Div([
        city_selector(selected_city='hanoi', visible=False),
        html.Div([
            html.Div([
                html.Button(
                    [
                        html.Img(
                            src="/assets/logos/home_button.svg",
                            alt="Home",
                            style={"height": "18px", "width": "18px", "marginRight": "8px"}
                        ),
                        html.Span("Home")
                    ],
                    id={"type": "atlas-home-btn", "index": 0},
                    n_clicks=0,
                    className="dash-atlas-home-btn",
                )
            ], style={
                "marginBottom": "12px",
                "display": "flex",
                "justifyContent": "flex-end",
            }),
            html.Div(section_blocks),
        ], style={
            "padding": "28px 8%",
            "overflowY": "auto",
            "backgroundColor": brand_colors['Light green'],
            "width": "100%",
        })
    ], style={"display": "flex", "flexDirection": "column", "width": "100%", "height": "100%"})


# ----------------------- App Layout Components -------------------------- #
# sidebar and footer are now imported from shared_components.py

def _atlas_row_is_available_for_city(rec, city_key):
    field = 'Available Hanoi' if city_key == 'hanoi' else 'Available Addis'
    val = str(rec.get(field, '')).strip().lower()
    return val in {'1', 'true', 'yes', 'y'}


def _count_available_indicators_by_pillar(city_key):
    counts = {
        'drivers': 0,
        'cross-cutting-issues': 0,
        'food-environments': 0,
        'food-supply-chains': 0,
        'individual-factors': 0,
        'outcomes': 0,
    }
    seen = set()

    for rec in atlas_records:
        name = str(rec.get('Indicator name', '')).strip()
        if not name:
            continue
        if not _atlas_row_is_available_for_city(rec, city_key):
            continue

        pill = str(rec.get('FCD Primary Pillar', '')).strip().lower()

        if pill == 'drivers':
            counts['drivers'] += 1
        elif pill == 'cross-cutting issues':
            counts['cross-cutting-issues'] += 1
        elif pill == 'food environments':
            counts['food-environments'] += 1        
        elif pill == 'food supply chains':
            counts['food-supply-chains'] += 1
        elif pill == 'individual factors':
            counts['individual-factors'] += 1
        elif pill == 'outcomes':
            counts['outcomes'] += 1

    return counts


_TAB_BG_KEY_BY_TAB_ID = {
    'tab-1-stakeholders': 'stakeholders',
    'tab-2-supply': 'supply',
    'tab-3-sustainability': 'sustainability',
    'tab-4-poverty': 'poverty',
    'tab-5-labour': 'labour',
    'tab-6-resilience': 'resilience',
    'tab-7-food-environments': 'food-environments',
    'tab-8-losses': 'losses',
    'tab-9-policies': 'policies',
    'tab-10-nutrition': 'nutrition',
    'tab-11-footprints': 'footprints',
    'tab-12-behaviour': 'behaviour',
}


def _record_pillar_key(rec):
    pill = str(rec.get('Pillars', '')).strip().lower()
    dom = str(rec.get('Domain / Sub-theme', '')).strip().lower()
    text = f"{pill} {dom}"

    if 'diets' in text or 'nutrition' in text or 'health' in text:
        return 'diets'
    if 'environment' in text or 'natural resources' in text or 'production' in text:
        return 'environment'
    if 'livelihoods' in text or 'poverty' in text or 'equity' in text:
        return 'livelihoods'
    if 'governance' in text:
        return 'governance'
    if 'resilience' in text:
        return 'resilience'
    return None


def _build_home_indicator_buttons(selected_city, tab_backgrounds, pillar_key):
    buttons_payload = []
    seen_names = set()

    for idx, rec in enumerate(atlas_records):
        if _record_pillar_key(rec) != pillar_key:
            continue

        name = str(rec.get('Indicator name', '')).strip()
        if not name:
            continue
        norm_name = name.lower()
        if norm_name in seen_names:
            continue
        seen_names.add(norm_name)

        _, target_tab, target_subview = _atlas_target_for_record(rec)
        available = _atlas_row_is_available_for_city(rec, selected_city)
        bg_key = _TAB_BG_KEY_BY_TAB_ID.get(target_tab)
        tab_is_coming_soon = tab_backgrounds.get(bg_key or '', '#ffffff') == '#f4f4f4'
        disabled = (not available) or tab_is_coming_soon

        buttons_payload.append((
            name.lower(),
            html.Button(
                [
                    html.Span(name),
                    html.Span('Coming soon', className='dash-landing-btn-coming-soon') if disabled else None,
                ],
                id={
                    'type': 'home-indicator-btn',
                    'target': target_tab,
                    'subview': target_subview or '',
                    'city': selected_city,
                    'index': idx,
                },
                n_clicks=0,
                className='dash-home-indicator-btn',
                disabled=disabled,
                style={
                    'opacity': 0.45 if disabled else 1,
                    'cursor': 'not-allowed' if disabled else 'pointer',
                },
            )
        ))

    if not buttons_payload:
        return [html.Div('No indicators available for this city yet.', className='dash-home-empty-indicators')]

    return [btn for _, btn in sorted(buttons_payload, key=lambda x: x[0])]


_SUBDOMAIN_GROUPS = {
    'Drivers': [
        ('environment-climate-change', 'Environment, Climate Change'),
        ('income-growth-distribution', 'Income Growth & Distribution'),
        ('policies-leadership', 'Policies & Leadership'),
        ('population-growth-migration', 'Population Growth & Migration'),
        ('socio-cultural-context', 'Socio-Cultural Context'),
    ],
    'Food Environments': [
        ('food-availability', 'Food Availability'),
        ('food-affordability', 'Food Affordability'),
        ('vendor-properties', 'Vendor Properties'),
    ],
    'Food Supply Chains': [
        ('processing-packing', 'Processing & Packing'),
        ('production-systems-input-supply', 'Production Systems & Input Supply'),
        ('retail-markerting', 'Retail & Marketing'),
        ('storage-distrbution', 'Storage & Distribution'),
    ],
    'Individual Factors': [
        ('economic', 'Economic'),
    ],
    'Cross-Cutting Issues': [
        ('governance', 'Governance'),
        ('resilience', 'Resilience'),
    ],
    'Outcomes': [
        ('food-security', 'Food Security'),
        ('livelihoods-poverty-equity', 'Livelihoods, Poverty & Equity'),
        ('noncommunicable-diseases', 'Noncommunicable Diseases'),
        ('nutrional-status', 'Nutritional Status'),
    ],
}


_COMING_SOON_SUBDOMAINS_BY_CITY = {
    'addis': {
        'environment-climate-change',
        'population-growth-migration',
        'socio-cultural-context',
        'food-availability',
        'food-affordability',
        'production-systems-input-supply',
        'retail-markerting',
        'storage-distrbution',
        'economic',
        'food-security',
        'noncommunicable-diseases',
    },
    'hanoi': {
        'population-growth-migration',
        'socio-cultural-context',
        'food-availability',
        'food-affordability',
        'vendor-properties',
        'processing-packing',
        #'production-systems-input-supply',
        'retail-markerting',
        'economic',
        'food-security',
        'noncommunicable-diseases',
    },
}


def _is_subdomain_coming_soon(selected_city, subdomain_key):
    city_key = selected_city if selected_city in ('addis', 'hanoi') else 'hanoi'
    return subdomain_key in _COMING_SOON_SUBDOMAINS_BY_CITY.get(city_key, set())


def _render_subdomain_hub_layout(selected_city, section_title):
    subdomains = _SUBDOMAIN_GROUPS.get(section_title, [])
    if not subdomains:
        return html.Div([
            html.H3(section_title or 'Sub-domain', style={'marginBottom': '10px'}),
            html.P('No sub-domains configured for this pillar yet.'),
        ], style={'padding': '20px'})

    return html.Div([
        city_selector(selected_city=selected_city, visible=False),
        html.Div([
            html.H3(section_title, style={
                'color': brand_colors['Brown'],
                'fontWeight': 'bold',
                'marginBottom': '8px',
            }),
            html.Div([
                html.Button(
                    [
                        html.Span(label, style={'display': 'block', 'fontWeight': 'bold'}),
                        html.Span('Coming soon', style={'display': 'block', 'fontSize': '0.78em', 'marginTop': '2px'})
                        if _is_subdomain_coming_soon(selected_city, subdomain_key) else None,
                    ],
                    id={
                        'type': 'home-subdomain-btn',
                        'subdomain': subdomain_key,
                        'city': selected_city,
                        'index': idx,
                    },
                    n_clicks=0,
                    disabled=_is_subdomain_coming_soon(selected_city, subdomain_key),
                    style={
                        'width': '90%',
                        'textAlign': 'left',
                        'padding': '12px 14px',
                        #'marginBottom': '10px',
                        'borderRadius': '10px',
                        'margin': '10px',
                        'border': 'none',
                        'fontWeight': 'bold',
                        'color': brand_colors['Brown'],
                        'backgroundColor': brand_colors['White'],
                        'boxShadow': '0 2px 6px rgba(0,0,0,0.08)',
                        'opacity': 0.55 if _is_subdomain_coming_soon(selected_city, subdomain_key) else 1,
                        'cursor': 'not-allowed' if _is_subdomain_coming_soon(selected_city, subdomain_key) else 'pointer',
                    },
                )
                for idx, (subdomain_key, label) in enumerate(subdomains)
            ]),
        ], style={
            'maxWidth': '820px',
            'margin': '20px auto',
            'padding': '16px',
            'backgroundColor': brand_colors['Light green'],
            'borderRadius': '12px',
            'margin': '10px',
        })
    ], style={'width': '100%', 'height': '100%', 'overflowY': 'auto'})


def _resolve_subdomain_layout(route_city, subdomain_key):
    if route_city == 'hanoi':
        if subdomain_key == 'environment-climate-change':
            resilience_ctx = _get_resilience_context()
            return hanoi_climate_resilience_tab(list(resilience_ctx['all_quarters']), default_view='Biophysical shocks')
        if subdomain_key == 'income-growth-distribution':
            return hanoi_income_growth_distribution_tab()
        if subdomain_key == 'policies-leadership':
            return hanoi_policies_leadership_tab()
        if subdomain_key == 'population-growth-migration':
            return hanoi_population_growth_migration_tab()
        if subdomain_key == 'socio-cultural-context':
            return hanoi_socio_cultural_context_tab()
        if subdomain_key == 'food-availability':
            return hanoi_food_availability_tab()
        if subdomain_key == 'food-affordability':
            return hanoi_food_affordability_tab()
        if subdomain_key == 'vendor-properties':
            return hanoi_vendor_properties_tab()
        if subdomain_key == 'processing-packing':
            return hanoi_processing_packing_tab()
        if subdomain_key == 'production-systems-input-supply':
            return hanoi_production_systems_input_supply_tab()
        if subdomain_key == 'retail-markerting':
            return hanoi_retail_markerting_tab()
        if subdomain_key == 'storage-distrbution':
            return hanoi_storage_distrbution_tab()
        if subdomain_key == 'economic':
            return hanoi_economic_tab()
        if subdomain_key == 'governance':
            return hanoi_governance_tab()
        if subdomain_key == 'resilience':
            return hanoi_temporal_resilience_tab()
        if subdomain_key == 'food-security':
            return hanoi_food_security_tab()
        if subdomain_key == 'livelihoods-poverty-equity':
            return hanoi_livelihoods_poverty_equity_tab()
        if subdomain_key == 'noncommunicable-diseases':
            return hanoi_noncommunicable_diseases_tab()
        if subdomain_key == 'nutrional-status':
            return hanoi_diets_nutrition_health_tab_layout()
        return html.Div('Coming soon', style={'padding': '20px'})

    # Addis
    if subdomain_key == 'environment-climate-change':
        return addis_environment_climate_change_tab()
    if subdomain_key == 'income-growth-distribution':
        return addis_income_growth_distribution_tab()
    if subdomain_key == 'policies-leadership':
        return addis_policies_leadership_tab()
    if subdomain_key == 'population-growth-migration':
        return addis_population_growth_migration_tab()
    if subdomain_key == 'socio-cultural-context':
        return addis_socio_cultural_context_tab()
    if subdomain_key == 'food-availability':
        return addis_food_availability_tab()
    if subdomain_key == 'food-affordability':
        return addis_food_affordability_tab()
    if subdomain_key == 'vendor-properties':
        return addis_vendor_properties_tab()
    if subdomain_key == 'processing-packing':
        return addis_processing_packing_tab()
    if subdomain_key == 'production-systems-input-supply':
        return addis_production_systems_input_supply_tab()
    if subdomain_key == 'retail-markerting':
        return addis_retail_markerting_tab()
    if subdomain_key == 'storage-distrbution':
        return addis_storage_distrbution_tab()
    if subdomain_key == 'economic':
        return addis_economic_tab()
    if subdomain_key == 'governance':
        return addis_governance_tab()
    if subdomain_key == 'resilience':
        return addis_resilience_tab()
    if subdomain_key == 'food-security':
        return addis_food_security_tab()
    if subdomain_key == 'livelihoods-poverty-equity':
        return addis_livelihoods_poverty_equity_tab()
    if subdomain_key == 'noncommunicable-diseases':
        return addis_noncommunicable_diseases_tab()
    if subdomain_key == 'nutrional-status':
        return addis_nutrional_status_tab()
    return html.Div('Coming soon', style={'padding': '20px'})

# ------------------------- Main app layout ------------------------- #

def landing_page_layout(background_image=None, tab_backgrounds=None, selected_city='hanoi', expanded_section=None):
    if background_image is None:
        background_image = hanoi_config.BACKGROUND_IMAGE if selected_city == 'hanoi' else addis_config.BACKGROUND_IMAGE
    if tab_backgrounds is None:
        tab_backgrounds = hanoi_config.TAB_BACKGROUNDS if selected_city == 'hanoi' else addis_config.TAB_BACKGROUNDS

    # Default active tab to Drivers
    if expanded_section is None:
        expanded_section = 'Drivers'

    pillar_counts = _count_available_indicators_by_pillar(selected_city)

    _PILLAR_TABS = [
        ('Drivers', 1, 'drivers',
         'The biophysical, socio-economic, and political forces that shape how food systems function and evolve over time.'),
        ('Food Supply Chains', 2, 'food-supply-chains',
         'All activities involved in producing, processing, distributing, and retailing food from farm to consumer.'),
        ('Food Environments', 3, 'food-environments',
         'The physical, economic, political, and socio-cultural contexts that determine how people access and acquire food.'),
        ('Individual Factors', 4, 'individual-factors',
         'The personal circumstances, resources, and preferences that shape food choices and dietary behaviours.'),
        ('Cross-Cutting Issues', 5, 'cross-cutting-issues',
         'Issues that span multiple pillars and affect the overall functioning and outcomes of food systems.'),
        ('Outcomes', 6, 'outcomes',
         'The resulting impacts on food security, diets, nutrition and health, environmental sustainability, and socio-economic equity.'),
    ]

    city_label = 'HANOI' if selected_city == 'hanoi' else 'ADDIS ABABA'

    used_ids = {
        'tab-home', 'tab-1-stakeholders', 'tab-2-supply', 'tab-3-sustainability',
        'tab-4-poverty', 'tab-5-labour', 'tab-6-resilience', 'tab-7-food-environments',
        'tab-8-losses', 'tab-9-policies', 'tab-10-nutrition', 'tab-11-footprints', 'tab-12-behaviour'
    }
    hidden_stub_buttons = [
        html.Button(id=tab_id, n_clicks=0, style={'display': 'none'})
        for tab_id in sorted(used_ids)
    ]

    # Hero tab buttons — clicking triggers existing home-pillar-atlas-btn callback
    tab_buttons = []
    for title, num, _ck, _d in _PILLAR_TABS:
        is_active = (expanded_section == title)
        tab_buttons.append(
            html.Button(
                title,
                id={
                    'type': 'home-pillar-atlas-btn',
                    'section': title,
                    'city': selected_city,
                    'index': num,
                },
                n_clicks=0,
                className='dash-hero-tab-btn dash-hero-tab-btn--active' if is_active else 'dash-hero-tab-btn',
            )
        )

    # Active pillar metadata
    active_info = next(
        ((t, n, ck, d) for t, n, ck, d in _PILLAR_TABS if t == expanded_section),
        _PILLAR_TABS[0]
    )
    active_title, active_index, active_count_key, active_description = active_info

    _DOT_COLORS = {
        'environment-climate-change': '#22c55e',
        'income-growth-distribution': '#f59e0b',
        'policies-leadership': '#60a5fa',
        'population-growth-migration': '#a855f7',
        'socio-cultural-context': '#7A9A3A',
        'food-availability': '#22c55e',
        'food-affordability': '#f59e0b',
        'vendor-properties': '#7A9A3A',
        'processing-packing': '#22c55e',
        'production-systems-input-supply': '#7A9A3A',
        'retail-markerting': '#f59e0b',
        'storage-distrbution': '#22c55e',
        'economic': '#f59e0b',
        'governance': '#60a5fa',
        'resilience': '#a855f7',
        'food-security': '#22c55e',
        'livelihoods-poverty-equity': '#7A9A3A',
        'noncommunicable-diseases': '#ef4444',
        'nutrional-status': '#22c55e',
    }

    _SUBDOMAIN_DESCRIPTIONS = {
        'environment-climate-change': 'Climate patterns, land use, and environmental conditions shaping food production and availability.',
        'income-growth-distribution': 'Economic growth, income distribution, and their effects on food system actors and consumers.',
        'policies-leadership': 'Government policies, regulatory frameworks, and leadership enabling sustainable food systems.',
        'population-growth-migration': 'Demographic shifts driving changes in food demand patterns and urban food systems.',
        'socio-cultural-context': 'Cultural norms, traditions, and social structures influencing food preferences and practices.',
        'food-availability': 'Supply of diverse, nutritious food through markets and distribution channels.',
        'food-affordability': 'Ability of different population groups to access adequate nutritious food within their budgets.',
        'vendor-properties': 'Physical characteristics and practices of food vendors including hygiene and quality.',
        'processing-packing': 'Value-addition activities transforming raw agricultural produce into food products.',
        'production-systems-input-supply': 'Agricultural production methods and supply of inputs for food growing.',
        'retail-markerting': 'Marketing, branding, and retail practices shaping consumer food choices.',
        'storage-distrbution': 'Post-harvest storage infrastructure and distribution networks moving food from farms to markets.',
        'economic': 'Individual economic resources, livelihoods, and financial capacity affecting food access.',
        'governance': 'Institutions, policies, and multi-stakeholder processes governing the food system.',
        'resilience': 'Capacity of food systems to absorb shocks and adapt to climate and economic disruptions.',
        'food-security': 'Access to sufficient, safe, and nutritious food for active and healthy lives.',
        'livelihoods-poverty-equity': 'Income, wellbeing, and equity outcomes for people working in and depending on food systems.',
        'noncommunicable-diseases': 'Chronic diseases linked to diet quality including diabetes, hypertension, and obesity.',
        'nutrional-status': 'Nutritional outcomes including stunting, wasting, micronutrient deficiencies, and overweight.',
    }

    subdomains = _SUBDOMAIN_GROUPS.get(active_title, [])

    # Build indicator rows — coming-soon state preserved exactly from _COMING_SOON_SUBDOMAINS_BY_CITY
    indicator_rows = []
    for idx, (subdomain_key, label) in enumerate(subdomains):
        is_coming_soon = _is_subdomain_coming_soon(selected_city, subdomain_key)
        dot_color = _DOT_COLORS.get(subdomain_key, '#7A9A3A')
        description = _SUBDOMAIN_DESCRIPTIONS.get(subdomain_key, '')

        row_inner = [
            html.Div([
                html.Div(style={
                    'width': '8px',
                    'height': '8px',
                    'borderRadius': '50%',
                    'backgroundColor': dot_color if not is_coming_soon else '#d1d5db',
                    'marginTop': '5px',
                    'flexShrink': '0',
                }),
                html.Div([
                    html.Span(label, style={
                        'fontWeight': 'bold',
                        'fontSize': '15px',
                        'color': '#374151',
                    }),
                    html.P(description, style={
                        'color': '#6B7280',
                        'fontSize': '13px',
                        'margin': '3px 0 0 0',
                        'lineHeight': '1.4',
                    }) if description else None,
                    html.Span('Coming soon', style={
                        'display': 'block',
                        'fontSize': '11px',
                        'color': '#9ca3af',
                        'fontStyle': 'italic',
                        'marginTop': '3px',
                    }) if is_coming_soon else None,
                ], style={'flex': '1', 'minWidth': '0', 'textAlign': 'left'}),
            ], style={
                'display': 'flex',
                'gap': '12px',
                'alignItems': 'flex-start',
                'flex': '1',
                'minWidth': '0',
            }),
            html.Span('EXPLORE →', className='dash-hero-explore-inline') if not is_coming_soon else None,
        ]

        if not is_coming_soon:
            indicator_rows.append(html.Button(
                row_inner,
                id={
                    'type': 'home-subdomain-btn',
                    'subdomain': subdomain_key,
                    'city': selected_city,
                    'index': idx,
                },
                n_clicks=0,
                className='dash-indicator-card',
            ))
        else:
            indicator_rows.append(html.Div(
                row_inner,
                className='dash-indicator-card-disabled',
            ))

    legend = html.Div([
        html.Span([html.Span('●', style={'color': '#22c55e'}), ' Environmental'],
                  style={'fontSize': '12px', 'color': '#6B7280', 'marginRight': '14px'}),
        html.Span([html.Span('●', style={'color': '#7A9A3A'}), ' Social'],
                  style={'fontSize': '12px', 'color': '#6B7280', 'marginRight': '14px'}),
        html.Span([html.Span('●', style={'color': '#f59e0b'}), ' Economic'],
                  style={'fontSize': '12px', 'color': '#6B7280', 'marginRight': '14px'}),
        html.Span([html.Span('●', style={'color': '#60a5fa'}), ' Governance'],
                  style={'fontSize': '12px', 'color': '#6B7280', 'marginRight': '14px'}),
        html.Span([html.Span('●', style={'color': '#a855f7'}), ' Resilience'],
                  style={'fontSize': '12px', 'color': '#6B7280', 'marginRight': '14px'}),
        html.Span([html.Span('●', style={'color': '#ef4444'}), ' Health'],
                  style={'fontSize': '12px', 'color': '#6B7280'}),
    ], style={
        'display': 'flex',
        'flexWrap': 'wrap',
        'gap': '4px',
        'paddingTop': '14px',
        'borderTop': '1px solid #f3f4f6',
        'marginTop': '4px',
    })

    content_panel = html.Div([
        html.Div([
            html.Div([
                html.Span(
                    f"PILLAR {active_index} OF 6  ·  {pillar_counts.get(active_count_key, 0)} INDICATORS",
                    style={
                        'color': '#7A9A3A',
                        'fontSize': '12px',
                        'fontWeight': '600',
                        'letterSpacing': '0.05em',
                        'textTransform': 'uppercase',
                        'display': 'block',
                        'marginBottom': '6px',
                    }
                ),
                html.H2(active_title, style={
                    'fontSize': '28px',
                    'fontWeight': '700',
                    'color': '#111827',
                    'margin': '0 0 8px 0',
                }),
                html.P(active_description, style={
                    'color': '#6B7280',
                    'fontSize': '14px',
                    'lineHeight': '1.5',
                    'margin': '0',
                    'maxWidth': '580px',
                }),
            ], style={'flex': '1', 'minWidth': '0'}),
            html.Div([
                html.Span(
                    f'CITY: {city_label}',
                    style={
                        'color': '#9ca3af',
                        'fontSize': '11px',
                        'fontWeight': '600',
                        'letterSpacing': '0.1em',
                        'textTransform': 'uppercase',
                        'display': 'block',
                        'textAlign': 'right',
                        'whiteSpace': 'nowrap',
                    }
                ),
            ], style={'paddingLeft': '24px', 'flexShrink': '0'}),
        ], style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'flex-start',
            'marginBottom': '16px',
            'gap': '16px',
        }),
        html.Hr(style={'border': 'none', 'borderTop': '1px solid #e5e7eb', 'margin': '0 0 4px 0'}),
        html.Div(indicator_rows if indicator_rows else [
            html.P('No sub-domains available yet.', style={'color': '#9ca3af', 'padding': '20px 0'})
        ]),
        legend,
    ], style={
        'backgroundColor': 'white',
        'borderRadius': '12px',
        'boxShadow': '0 4px 20px rgba(0,0,0,0.1)',
        'padding': '28px 32px',
    })

    hero = html.Div([
        # Top bar: city selector floats via absolute positioning within this 60px container
        html.Div([
            city_selector(selected_city=selected_city, visible=True),
        ], style={
            'position': 'relative',
            'height': '60px',
            'width': '100%',
        }),
        # Title + subtitle
        html.Div([
            html.H1('ECOFOODSYSTEMS DASHBOARD', style={
                'color': 'white',
                'fontWeight': '800',
                'fontSize': 'clamp(24px, 4vw, 44px)',
                'letterSpacing': '0.04em',
                'textTransform': 'uppercase',
                'margin': '0 0 14px 0',
                'textAlign': 'center',
            }),
            html.P(
                'Explore the EcoFoodSystems dashboard through six concise pillars adapted from the Food Systems Countdown framing.',
                style={
                    'color': 'rgba(255,255,255,0.85)',
                    'fontSize': '15px',
                    'maxWidth': '600px',
                    'textAlign': 'center',
                    'margin': '0 auto 32px auto',
                    'lineHeight': '1.6',
                }
            ),
        ], style={'padding': '16px 24px 0', 'textAlign': 'center'}),
        # Tab bar — sits at the bottom edge of the hero
        html.Div(tab_buttons, className='dash-hero-tab-bar'),
    ], style={
        'background': 'linear-gradient(135deg, #0F2E2A 0%, #2A7A6F 50%, #5FA89A 100%)',
        'paddingBottom': '0',
        'position': 'relative',
        'zIndex': '20',
    })

    return html.Div([
        *hidden_stub_buttons,
        hero,
        html.Div([content_panel], style={
            'margin': '-20px 24px 0 24px',
            'position': 'relative',
            'zIndex': '10',
        }),
        footer,
    ], style={
        'backgroundColor': '#ffffff',
        'minHeight': '100vh',
        'width': '100%',
        'overflowY': 'auto',
        'boxSizing': 'border-box',
    })


# ------------------------- Tab Layouts ------------------------- #
# Tab layout functions are now in separate files:
# - addis_layouts.py: All Addis Ababa tab layouts
# - hanoi_layouts.py: All Hà Nội tab layouts

# ------------------------- Other App Functions ------------------------- #

def make_region_kpi_card(region_name, quarter_value, all_values, all_quarters, slope, indicator_label, cfg=None):
    border_default = brand_colors["Dark green"]   # #939f5c
    border_color = border_default
    border_width = "2px"

    # Derive value badge colour from the choropleth colorscale
    badge_bg = "#f0f0f0"
    badge_fg = brand_colors["Black"]
    if cfg is not None and quarter_value is not None and not np.isnan(quarter_value):
        valid_vals = [v for v in all_values if v is not None and not np.isnan(v)]
        if valid_vals:
            if cfg["diverging"]:
                lim = max(abs(min(valid_vals)), abs(max(valid_vals)))
                vmin, vmax = -lim, lim
            else:
                vmin, vmax = min(valid_vals), max(valid_vals)
            t = (quarter_value - vmin) / (vmax - vmin) if vmax != vmin else 0.5
            t = max(0.0, min(1.0, t))
            sampled = pc.sample_colorscale(cfg["colorscale"], [t])[0]
            # sampled is 'rgb(r,g,b)' — convert to hex and pick text contrast
            rgb = pc.unlabel_rgb(sampled)
            badge_bg = "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
            luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
            badge_fg = "#ffffff" if luminance < 0.5 else brand_colors["Black"]

    # Polyfit overlay
    x_idx = np.arange(len(all_values))
    valid = [(i, v) for i, v in zip(x_idx, all_values) if v is not None and not np.isnan(v)]
    if len(valid) >= 2:
        xi, yi = zip(*valid)
        coeffs = np.polyfit(xi, yi, 1)
        trend_y = np.polyval(coeffs, x_idx).tolist()
    else:
        trend_y = [None] * len(all_values)

    sparkline = go.Figure()

    # Raw series
    sparkline.add_trace(go.Scatter(
        x=all_quarters, y=all_values,
        mode="lines",
        line=dict(color=brand_colors['Mid green'], width=1.5),
        hovertemplate="%{x}: %{y:.3f}<extra></extra>",
        name=indicator_label,
    ))

    # Polyfit trend
    sparkline.add_trace(go.Scatter(
        x=all_quarters, y=trend_y,
        mode="lines",
        line=dict(color=brand_colors['Brown'], width=1, dash="dot"),
        hoverinfo="skip",
        name="Trend",
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

    val_str = f"{quarter_value:.3f}" if quarter_value is not None and not np.isnan(quarter_value) else "N/A"

    card = dbc.Card(
        [
            dbc.CardBody([
                html.Div(
                    region_name,
                    style={
                        "fontWeight": "bold",
                        "fontSize": "12px",
                        "color": border_default,
                        "whiteSpace": "nowrap",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                        "minHeight": "18px",
                    },
                ),
                html.Div(
                    val_str,
                    style={
                        "fontSize": "20px",
                        "fontWeight": "bold",
                        "lineHeight": "1.2",
                        "minHeight": "30px",
                        "backgroundColor": badge_bg,
                        "color": badge_fg,
                        "borderRadius": "6px",
                        "padding": "2px 8px",
                        "display": "inline-block",
                    },
                ),
                dcc.Graph(
                    figure=sparkline,
                    config={"displayModeBar": False},
                    style={"height": "80px", "width": "100%"},
                ),
            ], style={
                "padding": "6px",
                "height": "100%",
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "space-between",
            }),
        ],
        style={
            "backgroundColor": "#ffffff",
            "border": f"{border_width} solid {border_color}",
            "borderRadius": "8px",
            "margin": "3px",
            "height": "150px",
            "width": "100%",
            "boxShadow": "none",
        },
    )

    return card

#------------------------- App Layout ----------------------- #

app.layout = html.Div([
    dcc.Loading(
        id="global-page-loader",
        type="circle",
        fullscreen=True,
        color="#A51E22",  # optional: brand red
        children=html.Div(id="page-content")
    ),
    dcc.Store(id='selected-city', data='hanoi'),  # default city
    dcc.Store(id='atlas-open-tab', data=None),
    dcc.Store(id='sh-table-page-size-store', data=13),

    dcc.Interval(id='resize-interval', interval=1000, n_intervals=0),
    html.Div(id="tab-content", children=landing_page_layout(selected_city='hanoi'), style={"width": "100%",
                                                                       "height": "100%"})
    # Parent container for full page
], style={
    "display": "flex",
    "flexDirection": "column",
    "height": "100vh",
    "width": "100vw"
})

# ------------------------- Callbacks ------------------------- #

# Clientside callback to compute page size based on window height
app.clientside_callback(
    """
    function(n) {
        // Estimate available height for table rows (px)
        var h = window.innerHeight || 800;
        // Reserve space for headers, padding, other UI (approx)
        var reserved = 260; // tweak if needed
        var rowHeight = 44; // approximate row height including padding
        var avail = h - reserved;
        var pageSize = Math.max(5, Math.floor(avail / rowHeight));
        return pageSize;
    }
    """,
    Output('sh-table-page-size-store', 'data'),
    Input('resize-interval', 'n_intervals')
)


# Callback to store selected city
@app.callback(
    Output('selected-city', 'data'),
    Input('city-selector', 'value')
)
def store_selected_city(city):
    return city


# Linking the dropdown to the bar chart for the MPI page    
@app.callback(
    Output('bar-plot-addis', 'figure'),
    Input('variable-dropdown', 'value'),
    prevent_initial_call=False
    
)
def update_bar(selected_variable):
    # Use only the MPI GeoDataFrame for plotting (no CSV fallback)
    if selected_variable in MPI.columns:
        df_plot = MPI[['Dist_Name', selected_variable]].dropna(subset=[selected_variable]).copy()
        df_plot = df_plot.sort_values(selected_variable, ascending=False)
        fig = px.bar(
            df_plot,
            x=selected_variable,
            y='Dist_Name',
            orientation='h',
            hover_data=['Dist_Name'],
            labels={'Dist_Name': "commune", selected_variable: 'Percentage of Deprived Households'},
            #color_discrete_sequence=[brand_colors['Red']]
            #color_discrete_sequence=["#1d574f"]
            color=selected_variable,
            color_continuous_scale=["#ffffff", "#D9A85C", "#A80050"]
        )
        
        fig.update_coloraxes(showscale=False)

        # compute bounded height from number of rows for stable layout
        nrows = df_plot.shape[0]
        computed_height = int(max(320, min(800, 28 * nrows)))

        fig.update_layout(
            yaxis={'categoryorder':'total ascending'},
            height=computed_height,
            margin=dict(l=10, r=10, t=10, b=72),
            hoverlabel=dict(bgcolor="white", font_color="black"),
            uirevision='bar-uirev-addis'
        )

        return fig
    else:
        # Selected variable not found in GeoDataFrame — return an empty figure with message
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="Selected variable not found in MPI GeoDataFrame",
                                 showarrow=False,
                                 xref='paper', yref='paper', x=0.5, y=0.5,
                                 font=dict(size=14))
        empty_fig.update_layout(margin=dict(l=10, r=10, t=10, b=72), height=360)
        return empty_fig

# Adding MPI map and linking it to the bar chart via click
@app.callback(
    Output('addis-mpi-map', 'figure'),
    Input('bar-plot-addis', 'clickData'),
    Input('variable-dropdown', 'value')
)
def update_map_on_bar_click(clickData, selected_variable):
    center = {
        "lat": MPI.geometry.centroid.y.mean(),
        "lon": MPI.geometry.centroid.x.mean()
    }
    zoom = 11

    MPI_display = MPI.copy()
    MPI_display['opacity'] = 0.7
    MPI_display['line_width'] = 0.8
    MPI_display['line_color'] = '#ffffff'

    # If a bar is clicked, zoom to that commune
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
            # Highlight: set opacity and line_width for the selected commune

            zoom = 11.5
            MPI_display.loc[MPI_display['Dist_Name'] == selected_dist, 'opacity'] = 0.2
            MPI_display.loc[MPI_display['Dist_Name'] == selected_dist, 'line_width'] = 2
            MPI_display.loc[MPI_display['Dist_Name'] == selected_dist, 'line_color'] = "#000000"

    # Choose choropleth column: prefer selected variable if present in GeoJSON, else fall back to 'Multidimensional Poverty Index'
    choropleth_col = selected_variable if selected_variable in MPI.columns else ('Multidimensional Poverty Index' if 'Multidimensional Poverty Index' in MPI.columns else None)

    if choropleth_col is None:
        empty_fig = go.Figure()
        empty_fig.update_layout(paper_bgcolor=brand_colors['White'], plot_bgcolor=brand_colors['White'], margin=dict(l=0, r=0, t=0, b=0))
        return empty_fig

    labels = {choropleth_col: choropleth_col, 'Dist_Name': 'commune Name'}

    fig = px.choropleth_mapbox(
        MPI,
        geojson=geojson,
        locations="Dist_Name",
        featureidkey="properties.Dist_Name",
        color=choropleth_col,
        color_continuous_scale=["#ffffff", "#D9A85C", "#A80050"],
        opacity=0.9,
        labels=labels,
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
            line=dict(width=MPI_display['line_width'], color=MPI_display['line_color'])
        )
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
    
@callback(
    Output("transport-mode", "data"),
    Output("btn-walk", "active"),
    Output("btn-transit", "active"),
    Output("btn-drive", "active"),
    Input("btn-walk", "n_clicks"),
    Input("btn-transit", "n_clicks"),
    Input("btn-drive", "n_clicks"),
    prevent_initial_call=True
)
def select_transport(*_):

    button = ctx.triggered_id

    mode = {
        "btn-walk": "walk",
        "btn-transit": "multimodal",
        "btn-drive": "drive"
    }[button]

    return (
        mode,
        button == "btn-walk",
        button == "btn-transit",
        button == "btn-drive"
    )

dcc.Store(id="transport-mode", data="walk")

def _build_accesibility_figure(
    selected_travel_time,
    selected_outlets,
    selected_metric,
    selected_transport_mode,
    selected_other_layer,
    selected_adm3_id,
    relayout_data,
    outlets_geojson_files_local,
    outlets_path_local,
    isochrones_path_local,
    gdf_food_env_local=None,
    sub_city_level_metrics=None,
    #cols_food_env_local=None,
    #data_labels_food_env_local=None,
    metric_direction_local=None,
    center_default=None,
    zoom_default=11,
    city_key=None,
): 
    # Map slider value to time_seconds label
    # Slider returns 0, 1, or 2 -> convert to time label
    slider_to_time_seconds = {
        0: 300,
        1: 600,
        2: 900
    }
    selected_time_seconds = slider_to_time_seconds.get(selected_travel_time, 900)
    #print(f"DEBUG: Converting slider value {selected_travel_time} to time_seconds={selected_time_seconds}")
    
    # Normalize selection
    if selected_outlets and "SELECT_ALL" in selected_outlets:
        selected_outlets = outlets_geojson_files_local.copy()
    elif not selected_outlets:
        selected_outlets = []
    else:
        selected_outlets = [item for item in selected_outlets if item != "SELECT_ALL"]

    # Derive isochrone categories from outlet filenames
    # E.g., 'amenity_cafe_addis.geojson' -> 'amenity_cafe'
    selected_isochrones = []
    if selected_outlets:
        for outlet_file in selected_outlets:
            print(outlet_file)
            # Outlet files are named '{category}_{city_key}.geojson'; strip the city suffix only
            category = outlet_file.replace(f'_{city_key}.geojson', '')
            selected_isochrones.append(category)  # Store category name, not filename

    # Preserve zoom/center
    if relayout_data and 'mapbox.center' in relayout_data:
        center = relayout_data['mapbox.center']
        zoom = relayout_data.get('mapbox.zoom', zoom_default)
    else:
        center = center_default or {"lat": 0, "lon": 0}
        zoom = zoom_default

    fig = go.Figure()

    # Temporarily disabled: food-environment choropleth layer.
    # Keep selected_metric in signature so callback wiring remains stable.
    # if selected_metric and gdf_food_env_local is not None and sub_city_level_metrics is not None:
    #     ...

    # Contextual hex layers containing population data etc. 
    if selected_other_layer:
        #print(f"DEBUG: Attempting to load other layer {selected_other_layer}")
        try:
            other_gdf = hex_vars_addis.copy()
            #print(f"DEBUG: hex_vars_addis columns: {other_gdf.columns}")
            #print(f"DEBUG: selected_other_layer.shape={other_gdf[selected_other_layer].shape}")
            fig.add_trace(go.Choroplethmapbox(
                geojson=hex_vars_addis_geojson,
                locations=other_gdf.h3_id,
                featureidkey="properties.h3_id",
                z=other_gdf[selected_other_layer],
                colorscale=metric_direction_local.get(selected_other_layer),
                marker=dict(opacity=0.9),
                name=cols_labels_hex_vars[selected_other_layer],
                showscale=False,
                hovertemplate='Approximate Population Count: %{z:.2f}<extra></extra>',
            ))
        except Exception as e:
            print(f"Error loading other layer {selected_other_layer}: {e}")

    # Isochrones: union selected isochrone polygons into a single layer with fixed opacity
    if selected_isochrones and selected_travel_time is not None:
        try:
            # Isochrone subdirectory structure: isochrones_path/isochrones_{city_key}_{transport_mode}/
            iso_dir = os.path.join(isochrones_path_local, f"isochrones_{city_key}_{selected_transport_mode}")
            
            #print(f"DEBUG: iso_dir={iso_dir}")
            #print(f"DEBUG: selected_isochrones={tuple(sorted(selected_isochrones))}")

            union_geojson = _build_isochrone_union_geojson(
                iso_dir,
                tuple(sorted(selected_isochrones)),
                selected_time_seconds,
                selected_transport_mode
            )
            if union_geojson:
                geojson_data = json.loads(union_geojson)
                # single uniform color (light cyan) with requested alpha (0.6)
                iso_color = '#83dfe9'
                fig.add_trace(go.Choroplethmapbox(
                    geojson=geojson_data,
                    locations=[0],
                    z=[1],
                    colorscale=[[0, iso_color], [1, iso_color]],
                    marker=dict(opacity=0.6, line=dict(width=0.5, color='black')),
                    showscale=False,
                    hoverinfo='skip',
                ))
                
            else:
                print(f"DEBUG: union_geojson is None")
        except Exception as e:
            print(f"Error unioning isochrones: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"DEBUG: Skipping isochrones - selected_isochrones={bool(selected_isochrones)}, selected_travel_time={selected_travel_time}")

    # Outlets
    if selected_outlets:
        num_outlets = len(selected_outlets)
        marker_palette = pc.sample_colorscale("Spectral", [n / max(num_outlets - 1, 1) for n in range(num_outlets)])
        for i, filename in enumerate(selected_outlets):
            try:
                outlet_gdf = _read_geojson_cached(os.path.join(outlets_path_local, filename)).copy()
                marker_color = marker_palette[i]
                fig.add_trace(go.Scattermapbox(
                    lat=outlet_gdf.geometry.y,
                    lon=outlet_gdf.geometry.x,
                    mode='markers',
                    marker=dict(size=4, color=marker_color, opacity=0.8),
                    name=filename.split('_')[1] if len(filename.split('_')) < 4 else f"{filename.split('_')[1]} {filename.split('_')[2]}",
                    hoverinfo='skip'
                ))
            except Exception as e:
                print(f"Error loading outlet {filename}: {e}")

    # Ensure basemap renders even when no traces were added: add an invisible Scattermapbox
    # This prevents Plotly from switching to a Cartesian empty plot when no layers are selected.
    if len(fig.data) == 0:
        try:
            fig.add_trace(go.Scattermapbox(
                lat=[center.get('lat', 0)],
                lon=[center.get('lon', 0)],
                mode='markers',
                marker=dict(size=0, opacity=0),
                hoverinfo='skip',
                showlegend=False
            ))
        except Exception:
            # fallback: ensure layout still defines mapbox
            pass

    #print(f"DEBUG: adm3_eth_gdf.columns={adm3_eth_gdf.columns}")
    #print(f"DEBUG: adm3_eth_geojson.keys()={adm3_eth_geojson.keys()}")

    if city_key == "addis":
        fig.add_trace(go.Choroplethmapbox(
                    geojson=adm3_eth_geojson,
                    locations=adm3_eth_gdf["adm3_id"],
                    featureidkey="properties.adm3_id",
                    z=np.ones(len(adm3_eth_gdf), dtype=float),
                    colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                    showscale=False,
                    marker=dict(
                        opacity=1.0,
                        line=dict(color=brand_colors["Brown"], width=1.5)
                    ),
                    text=adm3_eth_gdf["ADM3_EN"],
                    hoverinfo='text',
                ))

        # Add click to highlight functionality 
        if selected_adm3_id is not None:
            selected_adm3_id = str(selected_adm3_id)
            selected_adm3_gdf = adm3_eth_gdf[adm3_eth_gdf["adm3_id"].astype(str) == selected_adm3_id]
            if not selected_adm3_gdf.empty:
                fig.add_trace(go.Choroplethmapbox(
                    geojson=json.loads(selected_adm3_gdf[["adm3_id", "ADM3_EN", "geometry"]].to_json()),
                    locations=selected_adm3_gdf["adm3_id"],
                    featureidkey="properties.adm3_id",
                    z=np.ones(len(selected_adm3_gdf), dtype=float),
                    colorscale=[[0, "rgba(171, 224, 149, 0.18)"], [1, "rgba(171, 224, 149, 0.18)"]],
                    showscale=False,
                    marker=dict(
                        opacity=0.95,
                        line=dict(color=brand_colors["Teal"], width=3)
                    ),
                    hoverinfo='skip',
                ))

    fig.update_layout(
        mapbox=dict(style="carto-positron", center=center, zoom=zoom),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=brand_colors['White'],
        showlegend=True if (selected_outlets or selected_isochrones) else False,
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)'),
        uirevision='constant'
    )

    return fig


@app.callback(
    Output('accessibility-map-addis', 'figure'),
    [Input('outlet-travel-time', 'value'), Input("food-outlets-isochrones", "value"), #Input("choropleth-select", "value"), 
     Input("transport-mode", "data"), Input("contextual-layer-select", "value"), Input("accessibility-map-addis", "clickData")],
    [State('accessibility-map-addis', 'relayoutData')]
)
def update_accesibility_map(selected_travel_time, selected_outlets, selected_transport_mode, selected_other_layer, click_data, relayout_data):
    selected_adm3_id = None
    if click_data and click_data.get('points'):
        selected_adm3_id = click_data['points'][0].get('location')

    # Add defensive defaults for None values
    selected_travel_time = selected_travel_time if selected_travel_time is not None else 2
    selected_transport_mode = selected_transport_mode if selected_transport_mode else "walk"
    
    return _build_accesibility_figure(
        selected_travel_time,
        selected_outlets,
        None,
        selected_transport_mode,
        selected_other_layer,
        selected_adm3_id,
        relayout_data,
        outlets_geojson_files_addis,
        #isochrones_geojson_files_addis,
        outlets_path,
        isochrones_path,
        gdf_food_env_local=gdf_summary_stats_addis,
        sub_city_level_metrics=sub_city_level_metrics,
        #sub_city_level_metrics.keys(),
        #data_labels_food_env_local=sub_city_level_metrics.values(),
        metric_direction_local=metric_direction,
        center_default={"lat": 9.0192, "lon":  38.752},
        zoom_default=11,
        city_key="addis",
    )


def _travel_time_to_seconds(selected_travel_time):
    time_map = {0: 300, 1: 600, 2: 900}
    return time_map.get(selected_travel_time, 900)


def _format_accessibility_label(value, city_key="addis"):
    label_map = {
        "total": "Total",
        "men": "Men",
        "women": "Women",
        "youth": "Youth",
        "children_u5": "Children (0-5 years)",
        "women_rep": "Women of Reproductive Age (15-49 years)",
        "elderly": "Elderly (60+ years)",
    }
    if value is None:
        return ""
    value = str(value)
    if city_key == "addis":
        return label_map.get(value, value.replace("_", " ").title())
    return value.replace("_", " ").title()


def _selected_offer_categories(selected_outlets, city_key="addis"):
    if not selected_outlets:
        return []
    if "SELECT_ALL" in selected_outlets:
        return sorted(accessibility_zonal_stats_addis["offer_cat"].dropna().astype(str).unique())
    suffix = f"_{city_key}.geojson"
    categories = [str(item).replace(suffix, "") for item in selected_outlets]
    return sorted(set(categories))


def _build_accessibility_population_bar_figure(pop_cat, selected_outlets, selected_transport_mode, selected_travel_time, city_key="addis"):
    fig = go.Figure()

    if accessibility_zonal_stats_addis.empty or not accessibility_subcity_columns_addis:
        fig.add_annotation(
            text="Accessibility zonal stats are not available.",
            showarrow=False,
            xref='paper',
            yref='paper',
            x=0.5,
            y=0.5,
        )
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=380)
        return fig

    if not pop_cat:
        fig.add_annotation(
            text="Select a population category to view the sub-city bar chart.",
            showarrow=False,
            xref='paper',
            yref='paper',
            x=0.5,
            y=0.5,
        )
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=380)
        return fig

    selected_seconds = _travel_time_to_seconds(selected_travel_time)
    offer_categories = _selected_offer_categories(selected_outlets, city_key=city_key)

    df = accessibility_zonal_stats_addis.copy()
    df = df[df["pop_cat"].astype(str) == str(pop_cat)]
    df = df[df["mode"].astype(str) == str(selected_transport_mode)]
    df = df[pd.to_numeric(df["time"], errors="coerce") == selected_seconds]

    if offer_categories:
        df = df[df["offer_cat"].astype(str).isin(offer_categories)]

    if df.empty:
        fig.add_annotation(
            text="No rows match the selected filters.",
            showarrow=False,
            xref='paper',
            yref='paper',
            x=0.5,
            y=0.5,
        )
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=380)
        return fig

    chart_values = df[accessibility_subcity_columns_addis].apply(pd.to_numeric, errors="coerce").mean(axis=0, skipna=True)
    chart_df = chart_values.reset_index()
    chart_df.columns = ["sub_city", "percent_affected"]
    chart_df = chart_df.sort_values("percent_affected", ascending=False)

    if len(offer_categories) == 1:
        offer_text = _format_accessibility_label(offer_categories[0], city_key=city_key)
    elif offer_categories:
        offer_text = f"{len(offer_categories)} selected outlet types"
    else:
        offer_text = "all outlet types"

    title_text = (
        f"{_format_accessibility_label(pop_cat, city_key=city_key)} affected population by sub-city"
    )
    subtitle_text = f"{offer_text} | {selected_transport_mode.title()} | {selected_seconds // 60}-minute threshold"

    fig = px.bar(
        chart_df,
        x="sub_city",
        y="percent_affected",
        text="percent_affected",
        color="percent_affected",
        color_continuous_scale=["#c8e3e0", "#1d574f"],
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(
        #title=dict(text=f"{title_text}<br><sup>{subtitle_text}</sup>", x=0.5, xanchor="center"),
        title=None,
        margin=dict(l=10, r=10, t=70, b=70),
        height=380,
        paper_bgcolor=brand_colors['White'],
        plot_bgcolor=brand_colors['White'],
        coloraxis_showscale=False,
        xaxis_title=None,
        yaxis_title="Percentage population affected",
        xaxis_tickangle=-25,
    )
    fig.update_yaxes(range=[0, float(chart_df["percent_affected"].max() * 1.1)])
    return fig


@app.callback(
    Output("accessibility-population-bar-chart", "figure"),
    [
        Input("population-category-select", "value"),
        Input("food-outlets-isochrones", "value"),
        Input("transport-mode", "data"),
        Input("outlet-travel-time", "value"),
    ],
)
def update_accessibility_population_bar_chart(pop_cat, selected_outlets, selected_transport_mode, selected_travel_time):
    selected_transport_mode = selected_transport_mode or "walk"
    selected_travel_time = selected_travel_time if selected_travel_time is not None else 2
    return _build_accessibility_population_bar_figure(
        pop_cat,
        selected_outlets,
        selected_transport_mode,
        selected_travel_time,
        city_key="addis",
    )

# Hanoi callback is defined later; avoid duplicate callback registration here.


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

@app.callback(
    Output('addis-resilience-view-container', 'children'),
    Input('addis-resilience-view-select', 'value'),
    prevent_initial_call=False,
)

# Linking the tabs to page content loading 
@app.callback(
    Output("tab-content", "children"),
    [
        Input("city-selector", "value"),
        Input("atlas-open-tab", "data"),
        #Input({"type": "atlas-home-btn", "index": ALL}, "n_clicks"),
    ],
    [State("selected-city", "data")]
)
def render_tab_content(city_value, atlas_open_tab, selected_city):

    def _with_stubs(layout):
        """Wrap a non-landing layout with hidden tab stubs so all callback inputs exist."""
        return html.Div([_hidden_tab_stubs(), layout], style={"height": "100%", "width": "100%"})

    ctx = dash.callback_context
    if not ctx.triggered:
        initial_city = selected_city if selected_city in ('addis', 'hanoi') else 'hanoi'
        if initial_city == 'hanoi':
            return landing_page_layout(
                background_image=hanoi_config.BACKGROUND_IMAGE,
                tab_backgrounds=hanoi_config.TAB_BACKGROUNDS,
                selected_city='hanoi'
            )
        return landing_page_layout(
            background_image=addis_config.BACKGROUND_IMAGE,
            tab_backgrounds=addis_config.TAB_BACKGROUNDS,
            selected_city='addis'
        )
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Pattern IDs (e.g., atlas home button) arrive as JSON strings in trigger_id.
    if trigger_id.startswith('{'):
        try:
            trig_obj = json.loads(trigger_id)
        except Exception:
            trig_obj = {}
        if trig_obj.get('type') == 'atlas-home-btn':
            _city = selected_city if selected_city in ('addis', 'hanoi') else 'hanoi'
            if _city == 'hanoi':
                return landing_page_layout(
                    background_image=hanoi_config.BACKGROUND_IMAGE,
                    tab_backgrounds=hanoi_config.TAB_BACKGROUNDS,
                    selected_city='hanoi'
                )
            return landing_page_layout(
                background_image=addis_config.BACKGROUND_IMAGE,
                tab_backgrounds=addis_config.TAB_BACKGROUNDS,
                selected_city='addis'
            )
    
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

    if trigger_id == 'atlas-top-button':
        # Open the indicator atlas directly (city-specific)
        _atlas_city = selected_city if selected_city in ('hanoi', 'addis') else 'hanoi'
        if _atlas_city == 'hanoi':
            return _with_stubs(indicator_atlas_layout_hanoi(atlas_records))
        else:
            return _with_stubs(addis_fcd_indicator_atlas_tab_layout())
    else:
        atlas_section = None
        if trigger_id == 'atlas-open-tab' and atlas_open_tab:
            if isinstance(atlas_open_tab, dict):
                tab_id = atlas_open_tab.get('tab')
                atlas_subview = atlas_open_tab.get('subview')
                atlas_city = atlas_open_tab.get('city')
                atlas_section = atlas_open_tab.get('section')
                atlas_subdomain = atlas_open_tab.get('subdomain')
            else:
                tab_id = atlas_open_tab
                atlas_subview = None
                atlas_city = None
                atlas_section = None
                atlas_subdomain = None
        else:
            tab_id = trigger_id
            atlas_subview = None
            atlas_city = None
            atlas_section = None
            atlas_subdomain = None

    if tab_id == 'atlas-section':
        _atlas_city = atlas_city if atlas_city in ('hanoi', 'addis') else selected_city
        if _atlas_city == 'hanoi':
            return _with_stubs(indicator_atlas_layout_hanoi(atlas_records, initial_section=atlas_section))
        return _with_stubs(addis_fcd_indicator_atlas_tab_layout())

    route_city = atlas_city if atlas_city in ('addis', 'hanoi') else selected_city

    if tab_id == 'subdomain-hub':
        return _with_stubs(_render_subdomain_hub_layout(route_city, atlas_section))

    if tab_id == 'subdomain' and atlas_subdomain:
        return _with_stubs(_resolve_subdomain_layout(route_city, atlas_subdomain))
    
    # Route to city-specific dashboards
    if route_city == 'hanoi':
        # Hanoi-specific tabs
        if tab_id == "tab-1-stakeholders":
            return _with_stubs(hanoi_governance_stakeholders_tab_layout())
        elif tab_id == "tab-2-supply":
            return _with_stubs(hanoi_storage_distribution_tab_layout())
        elif tab_id == "tab-3-sustainability":
            return _with_stubs(hanoi_fcd_indicator_atlas_tab_layout())
        elif tab_id == "tab-4-poverty":
            return _with_stubs(hanoi_livelihoods_poverty_equity_tab_layout())
        elif tab_id == "tab-6-resilience":
            resilience_ctx = _get_resilience_context()
            return _with_stubs(hanoi_climate_resilience_tab(list(resilience_ctx["all_quarters"]), default_view=atlas_subview or 'Biophysical shocks'))
        elif tab_id == "tab-7-food-environments":
            return _with_stubs(hanoi_food_affordability_tab_layout())
        elif tab_id == "tab-9-policies":
            return _with_stubs(hanoi_policies_leadership_tab())
        elif tab_id == "tab-10-nutrition":
            return _with_stubs(hanoi_diets_nutrition_health_tab_layout())
        elif tab_id == "tab-home":
            return landing_page_layout(
                background_image=hanoi_config.BACKGROUND_IMAGE,
                tab_backgrounds=hanoi_config.TAB_BACKGROUNDS,
                selected_city='hanoi',
                expanded_section=atlas_section
            )
        else:
            return landing_page_layout(
                background_image=hanoi_config.BACKGROUND_IMAGE,
                tab_backgrounds=hanoi_config.TAB_BACKGROUNDS,
                selected_city='hanoi'
            )
    
    # Addis Ababa tabs
    if tab_id == "tab-1-stakeholders":
        return _with_stubs(addis_governance_stakeholders_tab_layout())
        
    elif tab_id == "tab-2-supply":
        return _with_stubs(addis_storage_distribution_tab_layout())
    
    elif tab_id == "tab-3-sustainability":
        return _with_stubs(addis_fcd_indicator_atlas_tab_layout())
    
    elif tab_id == "tab-4-poverty":
        return _with_stubs(addis_livelihoods_poverty_equity_tab_layout())

    elif tab_id == "tab-6-resilience":
        # Addis resilience currently uses the dedicated wrapper tab function.
        # Sidebar indicator links route here via target='tab-6-resilience'.
        return _with_stubs(addis_resilience_tab())
    
    elif tab_id == "tab-7-food-environments":
        return _with_stubs(addis_vendor_properties_tab(selected_city=route_city))
    
    elif tab_id == "tab-9-policies":
        return _with_stubs(addis_governance_policies_tab_layout())

    elif tab_id == "tab-10-nutrition":
        return _with_stubs(addis_diets_nutrition_health_tab_layout())
    
    elif tab_id == "tab-11-footprints":
        return _with_stubs(addis_environment_footprints_tab_layout())
    
    elif tab_id == "tab-home":
        return landing_page_layout(
            background_image=addis_config.BACKGROUND_IMAGE,
            tab_backgrounds=addis_config.TAB_BACKGROUNDS,
            selected_city='addis',
            expanded_section=atlas_section,
        )

    else:
        return landing_page_layout(
            background_image=addis_config.BACKGROUND_IMAGE,
            tab_backgrounds=addis_config.TAB_BACKGROUNDS,
            selected_city='addis',
        )


@app.callback(
    [
        Output("pillar-collapse-drivers", "is_open"),
        Output("pillar-collapse-food-supply-chains", "is_open"),
        Output("pillar-collapse-food-environments", "is_open"),
        Output("pillar-collapse-individual-factors", "is_open"),
        Output("pillar-collapse-cross-cutting-issues", "is_open"),
        Output("pillar-collapse-outcomes", "is_open"),
    ],
    [
        Input("pillar-toggle-drivers", "n_clicks"),
        Input("pillar-toggle-food-supply-chains", "n_clicks"),
        Input("pillar-toggle-food-environments", "n_clicks"),
        Input("pillar-toggle-individual-factors", "n_clicks"),
        Input("pillar-toggle-cross-cutting-issues", "n_clicks"),
        Input("pillar-toggle-outcomes", "n_clicks"),
    ],
    [
        State("pillar-collapse-drivers", "is_open"),
        State("pillar-collapse-food-supply-chains", "is_open"),
        State("pillar-collapse-food-environments", "is_open"),
        State("pillar-collapse-individual-factors", "is_open"),
        State("pillar-collapse-cross-cutting-issues", "is_open"),
        State("pillar-collapse-outcomes", "is_open"),
    ],
    prevent_initial_call=True,
)
def toggle_sidebar_pillars(
    n_drivers,
    n_food_supply_chains,
    n_food_environments,
    n_individual_factors,
    n_cross_cutting_issues,
    n_outcomes,
    open_drivers,
    open_food_supply_chains,
    open_food_environments,
    open_individual_factors,
    open_cross_cutting_issues,
    open_outcomes,
):
    ctx = dash.callback_context
    if not ctx.triggered:
        return (
            open_drivers,
            open_food_supply_chains,
            open_food_environments,
            open_individual_factors,
            open_cross_cutting_issues,
            open_outcomes,
        )

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    states = {
        "drivers": open_drivers,
        "food-supply-chains": open_food_supply_chains,
        "food-environments": open_food_environments,
        "individual-factors": open_individual_factors,
        "cross-cutting-issues": open_cross_cutting_issues,
        "outcomes": open_outcomes,
    }

    key_map = {
        "pillar-toggle-drivers": "drivers",
        "pillar-toggle-food-supply-chains": "food-supply-chains",
        "pillar-toggle-food-environments": "food-environments",
        "pillar-toggle-individual-factors": "individual-factors",
        "pillar-toggle-cross-cutting-issues": "cross-cutting-issues",
        "pillar-toggle-outcomes": "outcomes",
    }
    clicked_key = key_map.get(trigger_id)

    if clicked_key is None:
        return (
            open_drivers,
            open_food_supply_chains,
            open_food_environments,
            open_individual_factors,
            open_cross_cutting_issues,
            open_outcomes,
        )

    # Accordion behavior: only one pillar open at a time.
    new_states = {}
    for key, is_open in states.items():
        if key == clicked_key:
            new_states[key] = not bool(is_open)
        else:
            new_states[key] = False

    return (
        new_states["drivers"],
        new_states["food-supply-chains"],
        new_states["food-environments"],
        new_states["individual-factors"],
        new_states["cross-cutting-issues"],
        new_states["outcomes"],
    )

@app.callback(
    Output("atlas-open-tab", "data"),
    [
        Input({"type": "atlas-view-btn", "target": ALL, "subview": ALL, "city": ALL, "index": ALL}, "n_clicks"),
        Input({"type": "sidebar-indicator-btn", "target": ALL, "subview": ALL, "city": ALL, "index": ALL}, "n_clicks"),
        Input({"type": "home-indicator-btn", "target": ALL, "subview": ALL, "city": ALL, "index": ALL}, "n_clicks"),
        Input({"type": "home-pillar-atlas-btn", "section": ALL, "city": ALL, "index": ALL}, "n_clicks"),
        Input({"type": "home-subdomain-btn", "subdomain": ALL, "city": ALL, "index": ALL}, "n_clicks"),
    ],
    prevent_initial_call=True,
)
def open_atlas_target_tab(_atlas_btn_clicks, _sidebar_btn_clicks, _home_btn_clicks, _home_pillar_btn_clicks, _home_subdomain_btn_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    trig = ctx.triggered[0]["prop_id"].split(".")[0]
    try:
        trig_obj = json.loads(trig)
    except Exception:
        return dash.no_update

    if trig_obj.get("type") == "home-pillar-atlas-btn":
        section_name = trig_obj.get("section")
        if not section_name:
            return dash.no_update
        return {
            "tab": "tab-home",
            "section": section_name,
            "city": trig_obj.get("city") or None,
        }

    if trig_obj.get("type") == "home-subdomain-btn":
        subdomain_key = trig_obj.get("subdomain")
        if not subdomain_key:
            return dash.no_update
        return {
            "tab": "subdomain",
            "subdomain": subdomain_key,
            "city": trig_obj.get("city") or None,
        }

    target_tab = trig_obj.get("target")
    if not target_tab:
        return dash.no_update

    if target_tab == "subdomain":
        subdomain_key = trig_obj.get("subdomain") or trig_obj.get("subview")
        if not subdomain_key:
            return dash.no_update
        return {
            "tab": "subdomain",
            "subdomain": subdomain_key,
            "city": trig_obj.get("city") or None,
        }

    return {
        "tab": target_tab,
        "subview": trig_obj.get("subview") or None,
        "city": trig_obj.get("city") or None,
    }


# ------------------------- Hanoi Callbacks ------------------------- #

# Hanoi MPI bar chart
@app.callback(
    Output('bar-plot-hanoi', 'figure'),
    Input('variable-dropdown-hanoi', 'value'),
    prevent_initial_call=False
)
def update_bar_hanoi(selected_variable):
    # If the selected variable exists as a column in the GeoDataFrame, use it directly

    df_plot = MPI_hanoi[['Name', selected_variable]].dropna(subset=[selected_variable]).copy()
    df_plot = df_plot.sort_values(selected_variable, ascending=False)
    fig = px.bar(
        df_plot,
        x=selected_variable,
        y='Name',
        orientation='h',
        hover_data=['Name'],
        labels={'Name': "Commune", selected_variable: 'Percentage of Deprived Households'},
        color_discrete_sequence=[brand_colors['Red']]
    )

    nrows = df_plot.shape[0]

    computed_height = int(max(320, min(800, 28 * nrows)))

    fig.update_layout(yaxis={'categoryorder': 'total ascending'},
                      height=computed_height,
                      margin=dict(l=10, r=10, t=10, b=72),
                      xaxis_title_standoff=18,
                      hoverlabel=dict(bgcolor="white", font_color="black"),
                      uirevision='bar-uirev')
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
    zoom = 8.4

    MPI_display = MPI_hanoi.copy()
    MPI_display['opacity'] = 0.7
    MPI_display['line_width'] = 0.8

    if clickData and 'points' in clickData:
        selected_dist = clickData['points'][0]['y']
        match = MPI_hanoi[MPI_hanoi['Name'] == selected_dist]
        if not match.empty:
            center = {
                "lat": match.geometry.centroid.y.values[0],
                "lon": match.geometry.centroid.x.values[0]
            }
            zoom = 10
            MPI_display.loc[MPI_display['Name'] == selected_dist, 'opacity'] = 1
            MPI_display.loc[MPI_display['Name'] == selected_dist, 'line_width'] = 2

    # Choose choropleth column: prefer selected variable if present in GeoJSON, else fall back to 'Normalized'
    choropleth_col = selected_variable if selected_variable in MPI_hanoi.columns else ('Normalized' if 'Normalized' in MPI_hanoi.columns else None)

    if choropleth_col is not None:
        color_kwargs = dict(color=choropleth_col)
        labels = {choropleth_col: choropleth_col, 'Name': 'Commune Name'}
    else:
        # No choropleth column available; create empty figure
        empty_fig = go.Figure()
        empty_fig.update_layout(paper_bgcolor=brand_colors['White'], plot_bgcolor=brand_colors['White'], margin=dict(l=0, r=0, t=0, b=0))
        return empty_fig

    fig = px.choropleth_mapbox(
        MPI_hanoi,
        geojson=geojson_hanoi,
        locations="ma_xa",
        featureidkey="properties.ma_xa",
        color=choropleth_col,
        color_continuous_scale="YlOrRd",
        opacity=0.7,
        labels=labels,
        mapbox_style="carto-positron",
        zoom=zoom,
        center=center
    )

    fig.update_layout(coloraxis_colorbar=None)
    fig.update_coloraxes(showscale=False)
    fig.update_layout(
        paper_bgcolor=brand_colors['White'],
        plot_bgcolor=brand_colors['White'],
        margin=dict(l=0, r=0, t=0, b=0),
        mapbox=dict(style="carto-positron", center=center, zoom=zoom)
    )

    fig.update_traces(
        marker=dict(
            opacity=MPI_display['opacity'],
            line=dict(width=MPI_display['line_width'], color='black')
        )
    )
    return fig

# Hanoi affordability map with outlet layers and isochrones
@app.callback(
    Output('affordability-map-hanoi', 'figure'),
    [Input("outlet-travel-time-hanoi", "value"), Input("food-outlets-isochrones-hanoi", "value"), 
     Input("choropleth-select-hanoi", "value"), Input("transit-mode-hanoi", "value")],
    [State('affordability-map-hanoi', 'relayout_data')]
)
def update_affordability_map_hanoi(selected_travel_time, selected_outlets, selected_metric, selected_transit_mode, relayout_data):
    # Delegate to shared builder to avoid duplicate callbacks
    return _build_accesibility_figure(
        selected_travel_time,
        selected_outlets,
        selected_metric,
        selected_transit_mode,
        None,
        relayout_data,
        outlets_geojson_files_hanoi,
        outlets_path_hanoi,
        isochrones_path_hanoi,
        gdf_food_env_local=gdf_food_env_hanoi,
        sub_city_level_metrics=sub_city_level_metrics,
        #cols_food_env_local=sub_city_level_metrics.keys() if gdf_food_env_hanoi is not None else None,
        #data_labels_food_env_local=sub_city_level_metrics.values() if gdf_food_env_hanoi is not None else None,
        metric_direction_local=metric_direction,
        center_default={"lat": MPI_hanoi.geometry.centroid.y.mean(), "lon": MPI_hanoi.geometry.centroid.x.mean()},
        zoom_default=10,
        city_key="hanoi",
    )

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

    node_colors = [brand_colors['Dark green'] for l in labels]
    link_colors = ["rgba(209, 231, 168, 0.5)" for link in df_sankey_final['source']]

    # KPIs
    total_flow = flow1.drop_duplicates()["supply"].sum()
    total_flow_text = f"{total_flow:,.0f}"

    total = flow2.groupby(['source','target']).sum().reset_index()['supply'].sum()
    urban_only = flow2.groupby(['source','target']).sum().reset_index().set_index('target').loc['Hanoi urban'].values[1]
    urban_share = urban_only/total *100

    fig = go.Figure(go.Sankey(
        node=dict(label=labels, pad=15, thickness=20, color=node_colors),
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
        marker=dict(colors=[brand_colors['Dark green'], brand_colors['Light green']]),
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


# ── Drought Indicator callback ────────────────────────────────────────────────────────

@lru_cache(maxsize=64)
def _build_drought_map_cached(slider_idx, indicator, min_ag_area=0, infrastructure_layers=()):
    resilience_ctx = _get_resilience_context()
    commune_climate_df = resilience_ctx["commune_climate_df"]
    communes_unique = resilience_ctx["communes_unique"]
    resilience_base_geojson = resilience_ctx["resilience_base_geojson"]
    commune_join_key = resilience_ctx["join_key"]
    commune_featureidkey = resilience_ctx["featureidkey"]
    all_quarters = resilience_ctx["all_quarters"]

    region_ctx = _get_region_quarterly_context()
    region_quarterly = region_ctx["region_quarterly"]
    slopes_df = region_ctx["slopes_df"]

    if isinstance(infrastructure_layers, str):
        infrastructure_layers = (infrastructure_layers,)
    infrastructure_layers = tuple(
        str(layer).strip().lower()
        for layer in (infrastructure_layers or ())
        if str(layer).strip()
    )

    _map_layout = dict(
        mapbox=dict(style="carto-positron", center={"lat": 16.0, "lon": 106.0}, zoom=5),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        coloraxis_showscale=False,
    )

    if not all_quarters:
        empty_fig = go.Figure().update_layout(**_map_layout)
        return empty_fig.to_json(), "", [], {"display": "block"}

    safe_idx = max(0, min(int(slider_idx), len(all_quarters) - 1))
    quarter = all_quarters[safe_idx]
    cfg = commune_indicator_cfg.get(indicator)

    if cfg is None:
        empty_fig = go.Figure().update_layout(**_map_layout)
        return empty_fig.to_json(), quarter, [], {"display": "block"}

    col = cfg["col"]
    keep_cols = [commune_join_key, col]
    if col != 'ag_area_ha':
        keep_cols.append('ag_area_ha')
    if ("shapeName" in commune_climate_df.columns) and ("shapeName" != commune_join_key):
        keep_cols.append("shapeName")

    if isinstance(indicator, str) and (indicator.startswith("class_") or indicator in ("ag_area_ha", "drought_resistance")):
        spei_csv = os.path.join(hanoi_climate_dir, "static_climate_composites.csv")
        spei_df = pd.read_csv(spei_csv)
        spei_df[commune_join_key] = spei_df[commune_join_key].astype(str)
        df = spei_df[keep_cols].dropna(subset=[col])
        slider_style = {"display": "none"}
        plot_gdf = communes_unique.merge(df, on=commune_join_key, how="left")
        #print("DEBUG: plot_gdf columns:", plot_gdf.columns)
    else:
        spei_csv = os.path.join(hanoi_climate_dir, "static_climate_composites.csv")
        spei_df = pd.read_csv(spei_csv)
        spei_df[commune_join_key] = spei_df[commune_join_key].astype(str)
        commune_climate_df = commune_climate_df.merge(spei_df[[commune_join_key, 'ag_area_ha']], on=commune_join_key, how='left')
        
        df = (
            commune_climate_df[commune_climate_df["quarter"] == quarter][keep_cols]
            .dropna(subset=[col])
        )
        plot_gdf = communes_unique.merge(df, on=commune_join_key, how="left")
        #print("DEBUG: plot_gdf columns:", plot_gdf.columns)
        slider_style = {"display": "block"}

    overlay = plot_gdf[plot_gdf[col].notna()].copy()
    if 'ag_area_ha' in overlay.columns:
        if min_ag_area > 0:
            overlay = overlay[
                overlay["ag_area_ha"].astype(float) >= min_ag_area
        ]
            
    else:
        print("DEBUG: plot_gdf columns:", plot_gdf.columns)

    hover_label_col = None
    explicit_name_candidates = [
        "shapeName",
        "shapeName_x",
        "shapeName_y",
        "Dist_Name",
        "Dist_Name_x",
        "Dist_Name_y",
        "Dist_name",
        "Dist_name_x",
        "Dist_name_y",
    ]
    for candidate in explicit_name_candidates:
        if candidate in overlay.columns and overlay[candidate].notna().any():
            hover_label_col = candidate
            break

    if hover_label_col is None:
        for c in overlay.columns:
            c_norm = c.lower()
            if ("name" in c_norm) and overlay[c].notna().any():
                hover_label_col = c
                break

    if hover_label_col is None:
        hover_label_col = commune_join_key

    fig = go.Figure()
    if not overlay.empty:
        zvals = overlay[col].to_numpy(dtype=float)
        if cfg["diverging"]:
            lim = np.nanmax(np.abs(zvals))
            zmin, zmax = -lim, lim
        else:
            zmin, zmax = np.nanmin(zvals), np.nanmax(zvals)

        try:
            mid_val = float((zmin + zmax) / 2.0)
            cb_tickvals = [zmin, mid_val, zmax]
            cb_ticktext = [f"{zmin:.2f}", f"{mid_val:.2f}", f"{zmax:.2f}"]
        except Exception:
            cb_tickvals = None
            cb_ticktext = None

        colorbar_map = dict(
            thickness=12,
            len=0.50,
            x=0.995,
            y=0.995,
            xanchor='right',
            yanchor='top',
            outlinewidth=1,
            outlinecolor='#444',
            ticks='outside',
            ticklen=6,
            tickfont=dict(size=11, color='#111111'),
            bgcolor='rgba(255,255,255,0.65)'
        )
        if cb_tickvals is not None:
            colorbar_map.update(dict(tickmode='array', tickvals=cb_tickvals, ticktext=cb_ticktext))

        fig.add_trace(go.Choroplethmapbox(
            geojson=resilience_base_geojson,
            featureidkey=commune_featureidkey,
            locations=overlay[commune_join_key],
            z=overlay[col],
            text=overlay[hover_label_col].astype(str) if hover_label_col else overlay[commune_join_key].astype(str),
            colorscale=cfg["colorscale"],
            zmin=zmin, zmax=zmax,
            marker=dict(opacity=0.78, line=dict(color="white", width=0.4)),
            showscale=True,
            colorbar=colorbar_map,
            hovertemplate=(
                "<b>%{text}</b><br>"
                + f"{col}: "
                + "%{z:.3f}<extra></extra>"
            ),
        ))

    if infrastructure_layers:
        for idx, infrastructure_layer in enumerate(infrastructure_layers):
            layer_path = os.path.join(hanoi_infrastructure_dir, f"waterway_{infrastructure_layer}.geojson")
            if not os.path.exists(layer_path):
                continue

            try:
                osm_layer = gpd.read_file(layer_path).to_crs("EPSG:4326")
            except Exception:
                continue

            # Extract coordinates interleaved with None to separate line segments.
            lats = []
            lons = []
            for geom in osm_layer.geometry:
                if geom.geom_type == 'LineString':
                    coords = np.array(geom.coords)
                    lats.extend(coords[:, 1])
                    lons.extend(coords[:, 0])
                    lats.append(None)
                    lons.append(None)
                elif geom.geom_type in ['MultiLineString', 'GeometryCollection']:
                    for line in geom.geoms:
                        if line.geom_type == 'LineString':
                            coords = np.array(line.coords)
                            lats.extend(coords[:, 1])
                            lons.extend(coords[:, 0])
                            lats.append(None)
                            lons.append(None)

            if not lats:
                continue

            fig.add_trace(go.Scattermapbox(
                lat=lats,
                lon=lons,
                mode='lines',
                line=dict(width=1.5, color=brand_colors['Teal']),
                opacity=0.7,
                hoverinfo='skip',
                name=f"{infrastructure_layer} infrastructure",
            ))

    cards_payload = []
    if col in region_quarterly.columns:
        for region in sorted(region_quarterly["region"].unique()):
            sub = region_quarterly[region_quarterly["region"] == region].sort_values("quarter")
            all_vals = tuple(None if pd.isna(v) else float(v) for v in sub[col].tolist())
            all_qtrs = tuple(sub["quarter"].tolist())
            q_row = sub[sub["quarter"] == quarter]
            q_val = float(q_row[col].iloc[0]) if not q_row.empty else None
            slope_row = slopes_df[(slopes_df["region"] == region) & (slopes_df["indicator"] == col)]
            slope = float(slope_row["slope"].iloc[0]) if not slope_row.empty else 0.0
            cards_payload.append({
                "region": region,
                "quarter_value": q_val,
                "all_values": all_vals,
                "all_quarters": all_qtrs,
                "slope": slope,
                "indicator_label": col,
            })

    # ── Island overlay (Hoàng Sa / Trường Sa) ─────────────────────────────────
    # Shown in grey with a 'coming soon' tooltip to satisfy Vietnamese law
    # requiring both island groups to be displayed on maps of Vietnam.
    #try:
    #    with open(_islands_path) as _f:
    #        _islands_geojson = json.load(_f)
    #    _island_ids = [feat["properties"]["shapeID"] for feat in _islands_geojson["features"]]
    #    _island_names = {feat["properties"]["shapeID"]: feat["properties"]["shapeName"] for feat in _islands_geojson["features"]}
    #    fig.add_trace(go.Choroplethmapbox(
    #        geojson=_islands_geojson,
    #        featureidkey="properties.shapeID",
    #        locations=_island_ids,
    #        z=[0] * len(_island_ids),
    #        text=[_island_names[i] for i in _island_ids],
    #        colorscale=[[0, "#AAAAAA"], [1, "#AAAAAA"]],
    #        zmin=0, zmax=1,
    #        showscale=False,
    #        marker=dict(opacity=0.75, line=dict(color="#666666", width=0.5)),
    #        hovertemplate="<b>%{text}</b><br>Data coming soon<extra></extra>",
    #    ))
    #except Exception as _e:
    #    print(f"Island overlay skipped: {_e}")

    fig.update_layout(**_map_layout)
    return fig.to_json(), quarter, cards_payload, slider_style


@app.callback(
    Output("drought-map-container", "children"),
    Output("drought-slider-label", "children"),
    Output("date-slider-card", "style"),
    #Output("region-kpi-cards", "children"),
    Input("drought-date-slider", "value"),
    Input("climate-indicator-select", "value"),
    Input("ag-area-filter", "value"),
    Input("infrastructure-layer-select", "value"),
)
def update_drought_map(slider_idx, indicator, min_ag_area, infrastructure_layer):
    if isinstance(infrastructure_layer, (list, tuple, set)):
        selected_layers = tuple(
            str(layer).strip().lower()
            for layer in infrastructure_layer
            if str(layer).strip()
        )
    elif infrastructure_layer:
        selected_layers = (str(infrastructure_layer).strip().lower(),)
    else:
        selected_layers = tuple()

    fig_json, quarter, cards_payload, slider_style = _build_drought_map_cached(
        int(slider_idx or 0),
        indicator or "",
        float(min_ag_area) or 0,
        selected_layers,
    )
    cfg = commune_indicator_cfg.get(indicator or "")

    #cards = [
    #    dbc.Col(
    #        make_region_kpi_card(
    #            payload["region"],
    #            payload["quarter_value"],
    #            payload["all_values"],
    #            payload["all_quarters"],
    #            payload["slope"],
    #            payload["indicator_label"],
    #            cfg=cfg,
    #        ),
    #        md=3,
    #        style={"display": "flex"},
    #    )

    return (
        dcc.Graph(
            figure=_figure_from_json(fig_json),
            config={"displayModeBar": False, "scrollZoom": True},
            style={"height": "100%", "width": "100%"},
        ),
        quarter,
        slider_style,
        #dbc.Row(cards),
    )


@app.callback(
    Output("climate-indicator-description", "children"),
    Input("climate-indicator-select", "value"),
    State("climate-indicator-descriptions", "data"),
    prevent_initial_call=False
)
def update_climate_indicator_description(indicator, descriptions):
    if not indicator or not descriptions:
        return ""
    desc = descriptions.get(indicator, "No description available for this indicator.")
    return desc


@app.callback(
    Output("resilience-view-container", "children"),
    Input("resilience_view-select", "value"),
    State("resilience-spatial-data", "data"),
    prevent_initial_call=False,
)
def update_resilience_view_layout(view_selection, spatial_data):
    if view_selection == "Resilience Indicator Trends":
        return render_temporal_resilience_layout()

    if view_selection == "Land-use & Land-cover":
        return render_lulc_resilience_layout(_get_lulc_context()["indicator_options"])

    spatial_data = spatial_data or {}
    climate_indicator_options = spatial_data.get("climate_indicator_options", [])
    indicator_descriptions = spatial_data.get("indicator_descriptions", {})
    infrastructure_options = spatial_data.get("infrastructure_options") or [
        {'value': 'canal_drain_ditch', 'label': 'Irrigation Canals / Drainage Ditches'},
        {'value': 'rivers', 'label': 'Rivers'},
        {'value': 'streams', 'label': 'Streams'},
    ]

    n_raw = spatial_data.get("n", 1)
    try:
        n = max(1, int(n_raw))
    except (TypeError, ValueError):
        n = 1

    quarter_marks_raw = spatial_data.get("quarter_marks", {0: {"label": "", "style": {"fontSize": "10px", "color": "#8c8590"}}})
    quarter_marks = {int(k): v for k, v in quarter_marks_raw.items()}

    return render_spatial_climate_resilience_layout(
        climate_indicator_options,
        indicator_descriptions,
        infrastructure_options,
        n,
        quarter_marks,
    )


@lru_cache(maxsize=32)
def _build_lulc_map_cached(indicator):
    lulc_ctx = _get_lulc_context()
    lulc_stats_gdf = lulc_ctx["gdf"]
    lulc_map_center = lulc_ctx["map_center"]

    map_layout = dict(
        mapbox=dict(style="carto-positron", center=lulc_map_center, zoom=9),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
    )

    if lulc_stats_gdf is None or not indicator or indicator not in lulc_stats_gdf.columns:
        return go.Figure().update_layout(**map_layout).to_json()

    plot_gdf = lulc_stats_gdf.copy()
    plot_gdf["__rid"] = plot_gdf["__rid"].astype(str)
    plot_gdf["__value"] = pd.to_numeric(plot_gdf[indicator], errors="coerce")
    overlay = plot_gdf[plot_gdf["__value"].notna()].copy()

    indicator_l = str(indicator).lower()
    if any(k in indicator_l for k in ["water", "aqua"]):
        lulc_colorscale = "Blues"
    elif any(k in indicator_l for k in ["urban", "built"]):
        lulc_colorscale = "Reds"
    elif any(k in indicator_l for k in ["barren"]):
        lulc_colorscale = "YlOrBr"
    elif any(k in indicator_l for k in ["mangrove"]):
        lulc_colorscale = "Tealgrn"
    elif any(k in indicator_l for k in ["forest", "rice", "crop", "grass", "woody", "plantation", "deciduous", "evergreen"]):
        lulc_colorscale = "YlGn"
    else:
        lulc_colorscale = "Viridis"

    fig = go.Figure()

    if not overlay.empty:
        zvals = overlay["__value"].to_numpy(dtype=float)
        zmin = float(np.nanmin(zvals))
        zmax = float(np.nanmax(zvals))
        if zmax <= zmin:
            zmax = zmin + 1e-9

        if zmax <= 1.0 and zmin >= 0.0:
            hover_val_fmt = "%{z:.1%}"
            colorbar_tickformat = ".0%"
        elif zmax <= 100.0 and zmin >= 0.0:
            hover_val_fmt = "%{z:.1f}%"
            colorbar_tickformat = ".0f"
        else:
            hover_val_fmt = "%{z:.3f}"
            colorbar_tickformat = ".2f"

        minx, miny, maxx, maxy = overlay.total_bounds
        fig.update_layout(
            mapbox=dict(
                center={"lat": float((miny + maxy) / 2.0), "lon": float((minx + maxx) / 2.0)},
                zoom=9,
                style="carto-positron",
            )
        )

        label_col = None
        for candidate in ["Name", "Dist_Name", "Dist_name", "shapeName"]:
            if candidate in overlay.columns:
                label_col = candidate
                break

        if label_col is None:
            hover_text = overlay["__rid"].astype(str)
        else:
            hover_text = overlay[label_col].astype(str)

        overlay_for_map = overlay.copy()
        overlay_for_map["_fid"] = overlay_for_map.index.astype(str)

        fig.add_trace(go.Choroplethmapbox(
            geojson=json.loads(overlay_for_map.to_json()),
            featureidkey="id",
            locations=overlay_for_map["_fid"],
            z=overlay["__value"],
            text=hover_text,
            colorscale=lulc_colorscale,
            zmin=zmin,
            zmax=zmax,
            marker=dict(opacity=0.78, line=dict(color="black", width=0.4)),
            hovertemplate="<b>%{text}</b><br>" + indicator + ": " + hover_val_fmt + "<extra></extra>",
            colorbar=dict(
                title=None,
                thickness=8,
                len=0.28,
                x=0.99,
                y=0.98,
                xanchor="right",
                yanchor="top",
                outlinewidth=0,
                tickfont=dict(size=9),
                tickformat=colorbar_tickformat,
            ),
            showscale=True,
        ))

    fig.update_layout(**map_layout)
    return fig.to_json()


@app.callback(
    Output("lulc-map-container", "children"),
    Input("lulc-indicator-select", "value"),
)
def update_lulc_map(indicator):
    return dcc.Graph(
        figure=_figure_from_json(_build_lulc_map_cached(indicator or "")),
        config={"displayModeBar": False, "scrollZoom": True},
        style={"height": "100%", "width": "100%"},
    )

# Expose the Flask server for production deployment
server = app.server

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8051))
    debug = os.environ.get('PORT') is None
    app.run(debug=debug, host='0.0.0.0', port=port)