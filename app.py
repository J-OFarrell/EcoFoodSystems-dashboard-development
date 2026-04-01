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
from dash import Dash, html, dcc, Output, Input, State, callback, dash_table, ALL
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

import warnings
warnings.filterwarnings("ignore")

from dashboard_components import create_nutrition_kpi_card
import addis_config
import hanoi_config
from shared_components import sidebar, footer, city_selector
from addis_layouts import (
    stakeholders_tab_layout, supply_tab_layout, poverty_tab_layout,
    affordability_tab_layout, sustainability_tab_layout, policies_tab_layout,
    health_nutrition_tab_layout, footprints_tab_layout, addis_resilience_tab_layout
)
from hanoi_layouts import (
    hanoi_stakeholders_tab_layout, hanoi_supply_tab_layout,
    hanoi_poverty_tab_layout, hanoi_affordability_tab_layout,
    hanoi_health_nutrition_tab_layout, hanoi_policies_tab_layout, 
    hanoi_resilience_tab_layout,
    render_spatial_resilience_layout,
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
    gdf = gdf_food_env if city_key == "addis" else gdf_food_env_hanoi if city_key == "hanoi" else None
    if gdf is None:
        return None

    keep_cols = [c for c in ["Dist_Name", "Dist_name", "shapeName", "district", "name", "ma_xa"] if c in gdf.columns]
    slim_gdf = gdf[keep_cols + ["geometry"]].copy() if keep_cols else gdf[["geometry"]].copy()
    return slim_gdf.to_json()


@lru_cache(maxsize=48)
def _build_isochrone_union_geojson(isochrones_path_local, selected_isochrones_key):
    if not selected_isochrones_key:
        return None

    geoms = []
    for filename in selected_isochrones_key:
        path = os.path.join(isochrones_path_local, filename)
        if os.path.exists(path):
            gdf = _read_geojson_cached(path)
            geoms.extend([geom for geom in gdf.geometry if geom is not None and not geom.is_empty])

    if not geoms:
        return None

    unioned = unary_union(geoms)
    union_gdf = gpd.GeoDataFrame({"geometry": [unioned]}, crs="EPSG:4326")
    return union_gdf.to_json()

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
atlas_csv_path = os.path.join(homepath, "EcoFoodSystems_indicator_architecture - 260326 - Hanoi_rewritten_descriptions_final.csv")

# Loading and Formatting MPI Data
MPI = gpd.read_file(os.path.join(addis_mpi_dir, "addis_districts_MPI.geojson"))#.set_index('Dist_Name')
MPI['Multidimensional Poverty Index'] = MPI['Multidimensional Poverty Index'].astype(float)
MPI['Dist_Name'] = MPI['Dist_Name'].astype(str)
geojson = json.loads(MPI.to_json())

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

# Loading GeoJSON files for Isochrones (30-minute accessibility polygons)
isochrones_path = os.path.join(addis_food_env_dir, "isochrones_addis")
isochrones_geojson_files_addis = sorted(os.listdir(isochrones_path)) if os.path.exists(isochrones_path) else []
food_env_path = os.path.join(addis_food_env_dir, "addis_diet_env_mapping.geojson")
gdf_food_env = gpd.read_file(food_env_path).to_crs('EPSG:4326')

# Define food environment metrics and their labels
cols_food_env = ['density_healthyout', 'density_unhealthyout', 'density_mixoutlets',
                 'ratio_obesogenic'] #, 'pct_access_healthy', 'ptc_access_unhealthy']

data_labels_food_env = ['Healthy Outlet Density', 'Unhealthy Outlet Density', 'Mixed Outlet Density',
                        'Obesogenic Ratio'] #, 'Percent Access to Healthy Food', 'Percent Access to Unhealthy Food']

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

# Loading supply flow data for Sankey Diagram
df_sankey = pd.read_csv(os.path.join(hanoi_supply_dir, 'hanoi_supply.csv'))

df_policies_addis = pd.read_csv(os.path.join(addis_policy_dir, 'addis_policy_database.csv')).drop('Unnamed: 0',axis=1)
# Ensure link columns render as markdown links in the DataTable
if 'Document Link' in df_policies_addis.columns:
    df_policies_addis['Document Link'] = df_policies_addis['Document Link'].apply(
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
df_diet_hanoi = pd.read_csv(os.path.join(hanoi_nutrition_dir, 'hanoi_health_nutrition_cleaned.csv'))
df_diet_2_hanoi = pd.read_csv(os.path.join(hanoi_nutrition_dir, 'hanoi_health_nutrition_cleaned_2.csv'))


def _load_indicator_atlas_records(csv_path):
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
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


atlas_records_hanoi = _load_indicator_atlas_records(atlas_csv_path)



# ── District climate indicators ───────────────────────────────────────────────
_climate_csv  = os.path.join(hanoi_climate_dir, "vietnam_climate_resilience_quarterly_v1.csv")
_districts_path = os.path.join(hanoi_climate_dir, "resilience_districts_base_precision_200m_min.geojson")

_lulc_stats_path = os.path.join(hanoi_resilience_dir, "lulc_stats_gdf.geojson")
_region_quarterly_path = os.path.join(hanoi_climate_dir, "regional_quarterly_climate.csv")
_slopes_path = os.path.join(hanoi_climate_dir, "regional_indicator_slopes.csv")


@lru_cache(maxsize=1)
def _get_resilience_context():
    district_climate_df = pd.read_csv(_climate_csv).reset_index()
    district_climate_df["quarter"] = district_climate_df["quarter"].astype(str)

    resilience_gdf = _read_geojson_cached(_districts_path).copy()

    # Prefer shapeID for district joins when available; shapeName can be ambiguous.
    if ("shapeID" in resilience_gdf.columns) and ("shapeID" in district_climate_df.columns):
        join_key = "shapeID"
        featureidkey = "properties.shapeID"
        districts_unique = (
            resilience_gdf[["shapeID", "shapeName", "geometry"]]
            .dissolve(by="shapeID", as_index=False)
            .reset_index(drop=True)
        )
    else:
        join_key = "shapeName"
        featureidkey = "properties.shapeName"
        districts_unique = (
            resilience_gdf[["shapeName", "geometry"]]
            .dissolve(by="shapeName", as_index=False)
            .reset_index(drop=True)
        )

    return {
        "district_climate_df": district_climate_df,
        "districts_unique": districts_unique,
        "resilience_base_geojson": json.loads(districts_unique.to_json()),
        "join_key": join_key,
        "featureidkey": featureidkey,
        "all_quarters": tuple(sorted(district_climate_df["quarter"].unique())),
    }


@lru_cache(maxsize=1)
def _get_lulc_context():
    lulc_stats_gdf = None
    indicator_options = []
    map_center = {"lat": 21.03, "lon": 105.85}

    if os.path.exists(_lulc_stats_path):
        try:
            lulc_stats_gdf = _read_geojson_cached(_lulc_stats_path).copy()
            lulc_stats_gdf["geometry"] = lulc_stats_gdf["geometry"].buffer(0)
            lulc_stats_gdf = lulc_stats_gdf[lulc_stats_gdf["geometry"].is_valid & ~lulc_stats_gdf["geometry"].is_empty].copy()
            lulc_stats_gdf["__rid"] = lulc_stats_gdf.index.astype(str)

            if not lulc_stats_gdf.empty:
                minx, miny, maxx, maxy = lulc_stats_gdf.total_bounds
                map_center = {
                    "lat": float((miny + maxy) / 2.0),
                    "lon": float((minx + maxx) / 2.0),
                }

            excluded_lulc_cols = {"Dis_code", "Dist_name", "Dist_Name", "geometry", "__rid"}
            lulc_columns = []
            for c in lulc_stats_gdf.columns:
                if c in excluded_lulc_cols:
                    continue
                numeric_vals = pd.to_numeric(lulc_stats_gdf[c], errors="coerce")
                if numeric_vals.notna().any():
                    lulc_columns.append(c)

            indicator_options = [{"label": c, "value": c} for c in lulc_columns]
        except Exception as exc:
            print(f"[WARN] Could not load LULC stats geojson: {exc}")

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


@app.callback(
    Output('resilience-emdat-graph', 'figure'),
    Input('selected-city', 'data')
)
def update_resilience_emdat(selected_city):
    return build_resilience_figure_from_cache(size_max=20)


district_indicator_cfg = {
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


ATLAS_SECTIONS = [
    ("Food Systems Stakeholders", "tab-1-stakeholders"),
    ("Food Flows & Supply Chains", "tab-2-supply"),
    ("Sustainability Metrics", "tab-3-sustainability"),
    ("Multidimensional Poverty", "tab-4-poverty"),
    ("Resilience Indicators", "tab-6-resilience"),
    ("Food Environments", "tab-7-food-environments"),
    ("Food Losses & Waste", "tab-8-losses"),
    ("Policies & Regulation", "tab-9-policies"),
    ("Nutrition & Health", "tab-10-nutrition"),
    ("Environmental Footprints", "tab-11-footprints"),
    ("Behaviour Change Tool (AI Chatbot & Game)", "tab-12-behaviour"),
    #("Other Indicators", "tab-3-sustainability"),
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

    if 'stakeholder' in name or 'stakeholder' in domain:
        return "Food Systems Stakeholders", "tab-1-stakeholders", None
    if 'flow' in name or 'supply' in domain or 'value chain' in domain:
        return "Food Flows & Supply Chains", "tab-2-supply", None
    if 'poverty' in domain or 'multidimensional poverty' in domain:
        return "Multidimensional Poverty", "tab-4-poverty", None
    if 'resilience' in domain or 'resilience' in theme:
        resilience_text = f"{domain} {theme} {name}"
        if any(k in resilience_text for k in ['Land-use & Land-cover distribution']):
            return "Resilience Indicators", "tab-6-resilience", "Land-use & Land-cover"
        if any(k in resilience_text for k in  ['Agricultural climate resilience indicator' , 'Water storage anomalies', 'Natural disasters database']):
            return "Resilience Indicators", "tab-6-resilience", "Biophysical shocks"
        if any(k in resilience_text for k in ['food price resilience indicator']):
            return "Resilience Indicators", "tab-6-resilience", "Socio-Economic Shocks"
        return "Resilience Indicators", "tab-6-resilience", "Resilience Indicator Trends"
    if 'food environments' in domain or 'afford' in name or 'afford' in domain or 'dietary mapping' in domain:
        return "Food Environments", "tab-7-food-environments", None
    if 'loss' in domain or 'waste' in domain:
        return "Food Losses & Waste", "tab-8-losses", None
    if 'policy' in name or 'polic' in domain or 'governance' in theme:
        return "Policies & Regulation", "tab-9-policies", None
    if 'nutrition' in domain or 'health' in domain or 'food safety' in domain:
        return "Nutrition & Health", "tab-10-nutrition", None
    if 'footprint' in domain or 'life cycle' in name:
        return "Environmental Footprints", "tab-11-footprints", None
    if 'behaviour' in domain or 'behavior' in domain or 'chatbot' in name or 'game' in name:
        return "Behaviour Change Tool (AI Chatbot & Game)", "tab-12-behaviour", None
    if 'sustainability' in domain or 'sustainability' in name:
        return "Sustainability Metrics", "tab-3-sustainability", None
    return "Other Indicators", "tab-home", None


def indicator_atlas_layout_hanoi(records):
    section_map = {title: [] for title, _ in ATLAS_SECTIONS}

    for idx, rec in enumerate(records):
        section_title, target_tab, target_subview = _atlas_target_for_record(rec)
        indicator_name = (rec.get('Indicator name') or '').strip()
        definition = (rec.get('Definition (what the indicator measures)') or '').strip()
        relevance = (rec.get('Relevance (why it matters for the project)') or '').strip()
        source = (rec.get('Data source') or '').strip()
        hanoi_available = _is_indicator_available_for_city(indicator_name, "hanoi", target_tab)
        addis_available = _is_indicator_available_for_city(indicator_name, "addis", target_tab)

        section_map.setdefault(section_title, []).append(
            dbc.Card(
                dbc.CardBody([
                    html.H6(indicator_name, style={"fontWeight": "bold", "marginBottom": "8px", "color": brand_colors['Brown']}),
                    html.P(definition or "No definition available.", style={"fontSize": "0.9em", "marginBottom": "8px"}),
                    html.P(relevance or "No relevance note available.", style={"fontSize": "0.88em", "marginBottom": "8px", "color": "#4d4d4d"}),
                    html.Div([
                        html.Span("Source: ", style={"fontWeight": "bold"}),
                        html.Span(source or "Not specified")
                    ], style={"fontSize": "0.82em", "color": "#555", "marginBottom": "10px"}),
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
                            color="secondary",
                            size="sm",
                            disabled=not hanoi_available,
                            title=None if hanoi_available else "Not available for Hanoi",
                            style={
                                "borderRadius": "20px",
                                "fontWeight": "bold",
                                "backgroundColor": "#d9d9d9" if not hanoi_available else None,
                                "borderColor": "#d9d9d9" if not hanoi_available else None,
                                "color": "#7a7a7a" if not hanoi_available else None,
                                "opacity": 0.95 if not hanoi_available else 1,
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
                            color="secondary",
                            size="sm",
                            disabled=not addis_available,
                            title=None if addis_available else "Not available for Addis Ababa",
                            style={
                                "borderRadius": "20px",
                                "fontWeight": "bold",
                                "backgroundColor": "#d9d9d9" if not addis_available else None,
                                "borderColor": "#d9d9d9" if not addis_available else None,
                                "color": "#7a7a7a" if not addis_available else None,
                                "opacity": 0.95 if not addis_available else 1,
                                "cursor": "not-allowed" if not addis_available else "pointer",
                            }
                        ),
                    ], style={"display": "flex", "gap": "8px", "flexWrap": "wrap"}),
                ]),
                style={"borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.08)", "marginBottom": "12px"}
            )
        )

    section_blocks = []
    for title, _ in ATLAS_SECTIONS:
        cards = section_map.get(title, [])
        if not cards:
            continue
        section_blocks.append(
            dbc.Card([
                dbc.CardHeader(html.H4(title, style={"margin": 0, "fontWeight": "bold", "color": brand_colors['Brown']}),
                               style={"backgroundColor": brand_colors['Mid green']}),
                dbc.CardBody(cards),
            ], style={"marginBottom": "14px", "borderRadius": "12px", "boxShadow": "0 2px 6px rgba(0,0,0,0.08)"})
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
        html.Div([sidebar], style={
            "width": "15%",
            "height": "100%",
            "display": "flex",
            "vertical-align": 'top',
            "flexDirection": "column",
            "justifyContent": "flex-start",
        }),
        html.Div([
            html.Div(section_blocks),
        ], style={"flex": "1", "padding": "10px", "overflowY": "auto", "backgroundColor": brand_colors['Light green']})
    ], style={"display": "flex", "width": "100vw", "height": "100%"})


# ----------------------- App Layout Components -------------------------- #
# sidebar and footer are now imported from shared_components.py

# ------------------------- Main app layout ------------------------- #

def landing_page_layout(background_image=None, tab_backgrounds=None, selected_city='hanoi'):
    """
    Generate landing page layout for a city.
    
    Args:
        background_image: URL to background image (default: selected city)
        tab_backgrounds: Dict mapping tab_id to background color (default: selected city)
        selected_city: Currently selected city ('addis' or 'hanoi')
    """
    if background_image is None:
        background_image = hanoi_config.BACKGROUND_IMAGE if selected_city == 'hanoi' else addis_config.BACKGROUND_IMAGE
    if tab_backgrounds is None:
        tab_backgrounds = hanoi_config.TAB_BACKGROUNDS if selected_city == 'hanoi' else addis_config.TAB_BACKGROUNDS
    
    tab_labels = [
        "Food Systems Stakeholders", "Food Flows & Supply Chains", "Sustainability Metrics", "Multidimensional Poverty",
        "Labour, skills & green jobs", "Resilience Indicators", "Food Environments", "Food Losses & Waste",
        "Policies & Regulations", "Nutrition & Health", "Environmental Footprints", "Behaviour Change Tool (AI Chatbot & Game)"
    ]

    tab_ids = [
        "stakeholders", "supply", "sustainability", "poverty",
        "labour", "resilience", "food-environments", "losses",
        "policies", "nutrition", "footprints", "behaviour"]

    # Keep callback ids user-friendly while remaining compatible with existing background keys.
    tab_background_keys = [
        "stakeholders", "supply", "sustainability", "poverty",
        "labour", "resilience", "food-environments", "losses",
        "policies", "nutrition", "footprints", "behaviour"]
    
    # Use passed-in background_colours
    background_colours = tab_backgrounds
    
    # Create grid items
    grid_items = []
    for i, (tab_id, bg_key, label) in enumerate(zip(tab_ids, tab_background_keys, tab_labels)):
        grid_items.append(
            dbc.Card([
                dbc.Button(label, id=f"tab-{i+1}-{tab_id}", color="light", 
                           className="dash-landing-btn",
                           style={
                                "width": "100%",
                                "height": "100%",
                                "fontWeight": "bold",
                                "fontSize": "clamp(1.5em, 1.5em, 2.25em)",
                                "color": brand_colors['Brown'],
                                "backgroundColor": background_colours[bg_key],
                                "borderRadius": "10px",
                                "boxShadow": "0 4px 8px rgba(0,0,0,0.08)",
                                "border": f"2px solid {brand_colors['White']}",
                                "whiteSpace": "normal",
                                "padding": "18px 12px",
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

    # Put sidebar and main landing content side-by-side so the Home tab id exists
    main_content = html.Div([
        # Hidden home button so `tab-home` exists for callbacks but sidebar is not shown on landing page
        html.Button(id='tab-home', n_clicks=0, style={'display': 'none'}),
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
        "width": "100%",
        "padding": "0",
        "margin": "0",
        "boxSizing": "border-box",
        'overflowY':'auto'
    })

    # Return only the main landing content (no sidebar visible on homepage)
    return main_content


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
    dcc.Store(id='selected-city', data='hanoi'),
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
    Output('bar-plot', 'figure'),
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
            labels={'Dist_Name': "District", selected_variable: 'Percentage of Deprived Households'},
            color_discrete_sequence=[brand_colors['Red']]
        )

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

    # Choose choropleth column: prefer selected variable if present in GeoJSON, else fall back to 'Multidimensional Poverty Index'
    choropleth_col = selected_variable if selected_variable in MPI.columns else ('Multidimensional Poverty Index' if 'Multidimensional Poverty Index' in MPI.columns else None)

    if choropleth_col is None:
        empty_fig = go.Figure()
        empty_fig.update_layout(paper_bgcolor=brand_colors['White'], plot_bgcolor=brand_colors['White'], margin=dict(l=0, r=0, t=0, b=0))
        return empty_fig

    labels = {choropleth_col: choropleth_col, 'Dist_Name': 'District Name'}

    fig = px.choropleth_mapbox(
        MPI,
        geojson=geojson,
        locations="Dist_Name",
        featureidkey="properties.Dist_Name",
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

    # For the outlets map, use the selected variable if available so color matches the main choropleth
    choropleth_col = selected_variable if selected_variable in MPI.columns else ('Multidimensional Poverty Index' if 'Multidimensional Poverty Index' in MPI.columns else None)
    if choropleth_col is None:
        empty_fig = go.Figure()
        empty_fig.update_layout(paper_bgcolor=brand_colors['White'], plot_bgcolor=brand_colors['White'], margin=dict(l=0, r=0, t=0, b=0))
        return empty_fig

    labels = {choropleth_col: choropleth_col, 'Dist_Name': 'District Name'}

    fig = px.choropleth_mapbox(
        MPI,
        geojson=geojson,
        locations="Dist_Name",
        featureidkey="properties.Dist_Name",
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
    

def _build_affordability_figure(
    selected_outlets,
    selected_metric,
    relayout_data,
    outlets_geojson_files_local,
    isochrones_geojson_files_local,
    outlets_path_local,
    isochrones_path_local,
    gdf_food_env_local=None,
    cols_food_env_local=None,
    data_labels_food_env_local=None,
    metric_direction_local=None,
    center_default=None,
    zoom_default=11,
    city_key=None,
):
    # Normalize selection
    if selected_outlets and "SELECT_ALL" in selected_outlets:
        selected_outlets = outlets_geojson_files_local.copy()
    elif not selected_outlets:
        selected_outlets = []
    else:
        selected_outlets = [item for item in selected_outlets if item != "SELECT_ALL"]

    # Derive isochrones
    selected_isochrones = []
    if selected_outlets:
        for outlet_file in selected_outlets:
            iso_file = outlet_file.replace('.geojson', '_isochrone30min.geojson')
            if iso_file in isochrones_geojson_files_local:
                selected_isochrones.append(iso_file)

    # Preserve zoom/center
    if relayout_data and 'mapbox.center' in relayout_data:
        center = relayout_data['mapbox.center']
        zoom = relayout_data.get('mapbox.zoom', zoom_default)
    else:
        center = center_default or {"lat": 0, "lon": 0}
        zoom = zoom_default

    fig = go.Figure()

    # Choropleth if provided
    if selected_metric and gdf_food_env_local is not None and cols_food_env_local is not None:
        gdf = gdf_food_env_local.copy()
        if selected_metric in gdf.columns:
            gdf[selected_metric] = pd.to_numeric(gdf[selected_metric], errors='coerce')
            metric_label = (
                data_labels_food_env_local[cols_food_env_local.index(selected_metric)]
                if (data_labels_food_env_local is not None and selected_metric in cols_food_env_local)
                else selected_metric
            )

            direction = None
            if metric_direction_local is not None:
                direction = metric_direction_local.get(selected_metric, None)

            if direction is True:
                colorscale = FOOD_ENV_POS_SCALE
            elif direction is False:
                colorscale = FOOD_ENV_NEG_SCALE
            else:
                colorscale = FOOD_ENV_NEUTRAL_BONE_SCALE

            hover_label_col = next(
                (c for c in ["Dist_Name", "Dist_name", "shapeName", "district", "name", "ma_xa"] if c in gdf.columns),
                None,
            )
            hover_text = gdf[hover_label_col].astype(str) if hover_label_col else gdf.index.astype(str)

            geojson_cols = [hover_label_col, "geometry"] if hover_label_col else ["geometry"]
            if city_key in {"addis", "hanoi"}:
                cached_geojson = _get_food_env_geojson(city_key)
                geojson_data = json.loads(cached_geojson) if cached_geojson else json.loads(gdf[geojson_cols].to_json())
            else:
                geojson_data = json.loads(gdf[geojson_cols].to_json())

            fig.add_trace(go.Choroplethmapbox(
                geojson=geojson_data,
                locations=gdf.index,
                z=gdf[selected_metric],
                colorscale=colorscale,
                marker=dict(opacity=0.7, line=dict(color='#222', width=1)),
                hovertemplate='<b>%{text}</b><br>' + metric_label + ': %{z:.2f}<extra></extra>',
                text=hover_text,
                showscale=False
            ))

    # Isochrones: union selected isochrone polygons into a single layer with fixed opacity
    if selected_isochrones:
        try:
            union_geojson = _build_isochrone_union_geojson(
                isochrones_path_local,
                tuple(sorted(selected_isochrones)),
            )
            if union_geojson:
                geojson_data = json.loads(union_geojson)
                # single uniform color (light orange) with requested alpha (0.6)
                iso_color = '#83dfe9'
                fig.add_trace(go.Choroplethmapbox(
                    geojson=geojson_data,
                    locations=[0],
                    z=[1],
                    colorscale=[[0, iso_color], [1, iso_color]],
                    marker=dict(opacity=0.6, line=dict(width=0)),
                    hovertemplate='<b>Isochrone (combined)</b><extra></extra>',
                    showscale=False,
                    name='Isochrones (combined)'
                ))
        except Exception as e:
            print(f"Error unioning isochrones: {e}")

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
                    marker=dict(size=6, color=marker_color, opacity=0.8),
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
    Output('affordability-map', 'figure'),
    [Input("food-outlets-and-isochrones", "value"), Input("choropleth-select", "value")],
    [State('affordability-map', 'relayoutData')]
)
def update_affordability_map(selected_outlets, selected_metric, relayout_data):
    return _build_affordability_figure(
        selected_outlets,
        selected_metric,
        relayout_data,
        outlets_geojson_files_addis,
        isochrones_geojson_files_addis,
        outlets_path,
        isochrones_path,
        gdf_food_env_local=gdf_food_env,
        cols_food_env_local=cols_food_env,
        data_labels_food_env_local=data_labels_food_env,
        metric_direction_local=metric_direction,
        center_default={"lat": 9.0192, "lon":  38.752},
        zoom_default=11,
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

# Linking the tabs to page content loading 
@app.callback(
    Output("tab-content", "children"),
    [
        Input("tab-home", "n_clicks"),
        Input("tab-1-stakeholders", "n_clicks"),
        Input("tab-2-supply", "n_clicks"),
        Input("tab-3-sustainability", "n_clicks"),
        Input("tab-4-poverty", "n_clicks"),
        Input("tab-5-labour", "n_clicks"),
        Input("tab-6-resilience", "n_clicks"),
        Input("tab-7-food-environments", "n_clicks"),
        Input("tab-8-losses", "n_clicks"),
        Input("tab-9-policies", "n_clicks"),
        Input("tab-10-nutrition", "n_clicks"),
        Input("tab-11-footprints", "n_clicks"),
        Input("tab-12-behaviour", "n_clicks"),
        Input("atlas-top-button", "n_clicks"),
        Input("city-selector", "value"),
        Input("atlas-open-tab", "data"),
    ],
    [State("selected-city", "data")]
)
def render_tab_content(n_home, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n_atlas_top, city_value, atlas_open_tab, selected_city):
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
        tab_id = 'tab-3-sustainability'
        atlas_subview = None
        atlas_city = None
    else:
        if trigger_id == 'atlas-open-tab' and atlas_open_tab:
            if isinstance(atlas_open_tab, dict):
                tab_id = atlas_open_tab.get('tab')
                atlas_subview = atlas_open_tab.get('subview')
                atlas_city = atlas_open_tab.get('city')
            else:
                tab_id = atlas_open_tab
                atlas_subview = None
                atlas_city = None
        else:
            tab_id = trigger_id
            atlas_subview = None
            atlas_city = None

    route_city = atlas_city if atlas_city in ('addis', 'hanoi') else selected_city
    
    # Route to city-specific dashboards
    if route_city == 'hanoi':
        # Hanoi-specific tabs
        if tab_id == "tab-1-stakeholders":
            return hanoi_stakeholders_tab_layout()
        elif tab_id == "tab-2-supply":
            return hanoi_supply_tab_layout()
        elif tab_id == "tab-3-sustainability":
            return indicator_atlas_layout_hanoi(atlas_records_hanoi)
        elif tab_id == "tab-4-poverty":
            return hanoi_poverty_tab_layout()
        elif tab_id == "tab-6-resilience":
            resilience_ctx = _get_resilience_context()
            return hanoi_resilience_tab_layout(list(resilience_ctx["all_quarters"]), default_view=atlas_subview or 'Biophysical shocks')
        elif tab_id == "tab-7-food-environments":
            return hanoi_affordability_tab_layout()
        elif tab_id == "tab-9-policies":
            return hanoi_policies_tab_layout()
        elif tab_id == "tab-10-nutrition":
            return hanoi_health_nutrition_tab_layout()
        elif tab_id == "tab-home":
            return landing_page_layout(
                background_image=hanoi_config.BACKGROUND_IMAGE,
                tab_backgrounds=hanoi_config.TAB_BACKGROUNDS,
                selected_city='hanoi'
            )
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
    
    elif tab_id == "tab-7-food-environments":
        return affordability_tab_layout()
    
    elif tab_id == "tab-9-policies":
        return policies_tab_layout()

    elif tab_id == "tab-10-nutrition":
        return health_nutrition_tab_layout()
    
    elif tab_id == "tab-11-footprints":
        return footprints_tab_layout()
    
    elif tab_id == "tab-6-resilience":
        return addis_resilience_tab_layout(default_view=atlas_subview)
    
    elif tab_id == "tab-home":
        return landing_page_layout()

    else:
        return landing_page_layout()


@app.callback(
    Output("atlas-open-tab", "data"),
    Input({"type": "atlas-view-btn", "target": ALL, "subview": ALL, "city": ALL, "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_atlas_target_tab(_n_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    trig = ctx.triggered[0]["prop_id"].split(".")[0]
    try:
        trig_obj = json.loads(trig)
    except Exception:
        return dash.no_update

    target_tab = trig_obj.get("target")
    if not target_tab:
        return dash.no_update
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
        margin=dict(l=0, r=0, t=0, b=0)
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
    [Input("food-outlets-and-isochrones-hanoi", "value"), Input("choropleth-select-hanoi", "value")],
    [State('affordability-map-hanoi', 'relayoutData')]
)
def update_affordability_map_hanoi(selected_outlets, selected_metric, relayout_data):
    # Delegate to shared builder to avoid duplicate callbacks
    return _build_affordability_figure(
        selected_outlets,
        selected_metric,
        relayout_data,
        outlets_geojson_files_hanoi,
        isochrones_geojson_files_hanoi,
        outlets_path_hanoi,
        isochrones_path_hanoi,
        gdf_food_env_local=gdf_food_env_hanoi,
        cols_food_env_local=cols_food_env if gdf_food_env_hanoi is not None else None,
        data_labels_food_env_local=data_labels_food_env if gdf_food_env_hanoi is not None else None,
        metric_direction_local=metric_direction if gdf_food_env_hanoi is not None else None,
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

# ── Drought Indicator callback ────────────────────────────────────────────────────────

@lru_cache(maxsize=64)
def _build_drought_map_cached(slider_idx, indicator):
    resilience_ctx = _get_resilience_context()
    district_climate_df = resilience_ctx["district_climate_df"]
    districts_unique = resilience_ctx["districts_unique"]
    resilience_base_geojson = resilience_ctx["resilience_base_geojson"]
    district_join_key = resilience_ctx["join_key"]
    district_featureidkey = resilience_ctx["featureidkey"]
    all_quarters = resilience_ctx["all_quarters"]

    region_ctx = _get_region_quarterly_context()
    region_quarterly = region_ctx["region_quarterly"]
    slopes_df = region_ctx["slopes_df"]

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
    cfg = district_indicator_cfg.get(indicator)

    if cfg is None:
        empty_fig = go.Figure().update_layout(**_map_layout)
        return empty_fig.to_json(), quarter, [], {"display": "block"}

    col = cfg["col"]
    keep_cols = [district_join_key, col]
    if ("shapeName" in district_climate_df.columns) and ("shapeName" != district_join_key):
        keep_cols.append("shapeName")

    if isinstance(indicator, str) and (indicator.startswith("class_") or indicator.startswith("drought_resistance")):
        spei_csv = os.path.join(hanoi_climate_dir, "static_climate_composites.csv")
        spei_df = pd.read_csv(spei_csv)
        df = spei_df[keep_cols].dropna(subset=[col])
        slider_style = {"display": "none"}
        plot_gdf = districts_unique.merge(df, on=district_join_key, how="left")
    else:
        df = (
            district_climate_df[district_climate_df["quarter"] == quarter][keep_cols]
            .dropna(subset=[col])
        )
        plot_gdf = districts_unique.merge(df, on=district_join_key, how="left")
        slider_style = {"display": "block"}

    overlay = plot_gdf[plot_gdf[col].notna()].copy()

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
        hover_label_col = district_join_key

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
            featureidkey=district_featureidkey,
            locations=overlay[district_join_key],
            z=overlay[col],
            text=overlay[hover_label_col].astype(str) if hover_label_col else overlay[district_join_key].astype(str),
            colorscale=cfg["colorscale"],
            zmin=zmin, zmax=zmax,
            marker=dict(opacity=0.78, line=dict(color="black", width=0.4)),
            showscale=True,
            colorbar=colorbar_map,
            hovertemplate=(
                "<b>%{text}</b><br>"
                + f"{col}: "
                + "%{z:.3f}<extra></extra>"
            ),
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

    fig.update_layout(**_map_layout)
    return fig.to_json(), quarter, cards_payload, slider_style


@app.callback(
    Output("drought-map-container", "children"),
    Output("drought-slider-label", "children"),
    Output("region-kpi-cards", "children"),
    Output("date-slider-card", "style"),
    Input("drought-date-slider", "value"),
    Input("climate-indicator-select", "value"),
)
def update_drought_map(slider_idx, indicator):
    fig_json, quarter, cards_payload, slider_style = _build_drought_map_cached(int(slider_idx or 0), indicator or "")
    cfg = district_indicator_cfg.get(indicator or "")

    cards = [
        dbc.Col(
            make_region_kpi_card(
                payload["region"],
                payload["quarter_value"],
                payload["all_values"],
                payload["all_quarters"],
                payload["slope"],
                payload["indicator_label"],
                cfg=cfg,
            ),
            md=3,
            style={"display": "flex"},
        )
        for payload in cards_payload
    ]

    return (
        dcc.Graph(
            figure=_figure_from_json(fig_json),
            config={"displayModeBar": False, "scrollZoom": True},
            style={"height": "100%", "width": "100%"},
        ),
        quarter,
        dbc.Row(cards),
        slider_style,
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

    n_raw = spatial_data.get("n", 1)
    try:
        n = max(1, int(n_raw))
    except (TypeError, ValueError):
        n = 1

    quarter_marks_raw = spatial_data.get("quarter_marks", {0: {"label": "", "style": {"fontSize": "10px", "color": "#8c8590"}}})
    quarter_marks = {int(k): v for k, v in quarter_marks_raw.items()}

    return render_spatial_resilience_layout(
        climate_indicator_options,
        indicator_descriptions,
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
        for candidate in ["Dist_Name", "Dist_name", "shapeName"]:
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