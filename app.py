import os
import csv
import time
from dotenv import load_dotenv
load_dotenv()
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

from data_access import (
    load_indicator_atlas_records as _load_indicator_atlas_records,
    atlas_records,
    is_indicator_available_for_city,
    df_mpi,
    df_mpi_hanoi,
    MPI,
    geojson,
    mpi_vars,
    variables,
    df_sh,
    outlets_geojson_files_addis,
    df_policies_addis,
    df_indicators,
    df_lca,
    df_sankey,
    MPI_hanoi,
    geojson_hanoi,
    df_sh_hanoi,
    df_policies_hanoi,
    isochrones_geojson_files_hanoi,
    df_affordability_hanoi,
    df_diet_2_hanoi,
    accessibility_outlet_options_addis,
    accessibility_zonal_stats_addis,
    accessibility_subcity_columns_addis,
    accessibility_population_options_addis,
    accessibility_offer_options_addis,
)
from cache_helpers import (
    _path_mtime,
    _figure_from_json,
    _read_geojson_cached,
    _load_food_env_layer,
    _build_isochrone_union_geojson,
    _travel_time_to_seconds,
    _format_accessibility_label,
    _selected_offer_categories,
)
from tab_layouts import (
    _hidden_tab_stubs,
    indicator_atlas_layout_hanoi,
    _render_subdomain_hub_layout,
    _is_subdomain_coming_soon,
    landing_page_layout,
    make_region_kpi_card,
)
from config import (
    brand_colors,
    plotting_palette_cat,
    green_scale,
    red_scale,
    grey_scale,
    _BASEMAP_TILE,
    REGION_COLOURS,
    sub_city_level_metrics,
    cols_labels_hex_vars,
    FOOD_ENV_NEG_SCALE,
    FOOD_ENV_POS_SCALE,
    FOOD_ENV_NEUTRAL_BONE_SCALE,
    VIRIDIS_SCALE,
    BLUES_SCALE,
    YLORBR_SCALE,
    HOT_SCALE,
    metric_color_scale,
    kpi_card_style,
    header_style,
    card_style,
)

import warnings
warnings.filterwarnings("ignore")

from dashboard_components import create_nutrition_kpi_card
import addis_config
import hanoi_config
from shared_components import sidebar, footer, city_selector
from chatbot_ui import chatbot_widget, render_messages, render_pending_turn, render_quota_status
import chatbot_engine
import groq
from flask import request as flask_request
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

from app_setup import app


@lru_cache(maxsize=4)
def _get_food_env_geojson(city_key):
    gdf = gdf_summary_stats_addis if city_key == "addis" else gdf_food_env_hanoi if city_key == "hanoi" else None
    if gdf is None:
        return None

    keep_cols = [c for c in ["Dist_Name", "Dist_name", "shapeName", "commune", "name", "ma_xa"] if c in gdf.columns]
    slim_gdf = gdf[keep_cols + ["geometry"]].copy() if keep_cols else gdf[["geometry"]].copy()
    return slim_gdf.to_json()


#colors = {
#  'eco_green': '#AFC912',
#  'forest_green': '#4C7A2E',
#  'earth_brown': '#7B5E34',
#  'harvest_yellow': '#F2D16B',
#  'neutral_light': '#F5F5F5',
#  'dark_text': '#333333',
#  'accent_warm': '#E07A5F'
#}

_cmap_full = plt.get_cmap('RdYlBu_r')
_cmap = mcolors.LinearSegmentedColormap.from_list(
    'RdYlGn_r_clipped',
    _cmap_full(np.linspace(0.25, 1.0, 256))
)

drought_colorscale = [[round(i/9, 2), mcolors.to_hex(_cmap(i/9))] for i in range(10)]

# -------------------------- Loading and Formatting All Data ------------------------- #
# Most eager data loading (MPI, geojson, df_sh, df_policies, df_indicators,
# df_lca, df_sankey, and their Hanoi equivalents) now lives in data_access.py
# (imported at the top of this file) - both app.py and addis_layouts.py/
# hanoi_layouts.py import directly from there instead of the old
# `import app as main` reverse-dependency workaround. What remains below is
# data/paths only ever used within app.py itself (accessibility, EMDAT,
# climate/LULC, adm3 boundaries).

homepath = os.path.dirname(os.path.abspath(__file__))
data_root = os.path.join(homepath, "assets", "data")

addis_root = os.path.join(data_root, "addis")
addis_food_env_dir = os.path.join(addis_root, "food-environments_vendor-properties")
addis_adm3_dir = os.path.join(addis_root, "drivers_income-growth-and-distribution_adm3")

hanoi_root = os.path.join(data_root, "hanoi")
hanoi_mpi_dir = os.path.join(hanoi_root, "drivers_income-growth-and-distribution")
hanoi_food_env_dir = os.path.join(hanoi_root, "food-environments_vendor-properties")
hanoi_resilience_dir = os.path.join(hanoi_root, "cross-cutting-issues_resilience")
hanoi_climate_dir = os.path.join(hanoi_resilience_dir, "precomputed_hanoi_climate_vars")
hanoi_infrastructure_dir = os.path.join(hanoi_resilience_dir, "osm_infrastructure")

adm3_eth_gdf = gpd.read_file(os.path.join(addis_adm3_dir, "addis_drv_igd_adm3_boundaries.geojson")).to_crs("EPSG:4326")
adm3_eth_gdf = adm3_eth_gdf.reset_index(drop=True)
adm3_eth_gdf["adm3_id"] = adm3_eth_gdf.index.astype(str)
adm3_eth_geojson = json.loads(adm3_eth_gdf[["adm3_id", "ADM3_EN", "geometry"]].to_json())

# MPI, mpi_vars, variables, df_sh, and outlets_geojson_files_addis are now
# imported from data_access.py (see top of file).

# Pre-calculate fixed column widths (6px per character, min 80px, max 200px)
column_widths = {}
for col in df_sh.columns:
    max_len = max(len(str(col)), df_sh[col].astype(str).str.len().max())
    column_widths[col] = min(max(max_len * 6, 80), 200)

total_table_width = sum(column_widths.values())

# Loading GeoJSON files for Food Outlets
outlets_path = os.path.join(addis_food_env_dir, "jsons_addis_foodoutlets")

# accessibility_outlet_options_addis, accessibility_zonal_stats_addis,
# accessibility_subcity_columns_addis, accessibility_population_options_addis,
# and accessibility_offer_options_addis are now imported from data_access.py
# (also needed by addis_layouts.py, previously via `import app as main`).

# Loading GeoJSON files for Isochrones (30-minute accessibility polygons)
isochrones_path = os.path.join(addis_food_env_dir, "isochrones_addis_all")
summary_stats_path_addis = os.path.join(addis_food_env_dir, "addis_fev_vp_fenv_subcity_summary.geojson")
gdf_summary_stats_addis = gpd.read_file(summary_stats_path_addis).to_crs('EPSG:4326')
hex_vars_addis = gpd.read_file(os.path.join(addis_food_env_dir, "addis_fev_vp_fenv_hexgrid_population.geojson")).to_crs('EPSG:4326')
hex_vars_addis_geojson = json.loads(hex_vars_addis.to_crs("EPSG:4326").to_json())

# Define food environment metrics and their labels
# (sub_city_level_metrics, cols_labels_hex_vars, REGION_COLOURS, green_scale,
# red_scale, grey_scale, FOOD_ENV_*_SCALE, VIRIDIS/BLUES/YLORBR/HOT_SCALE, and
# metric_color_scale now live in config.py - imported at the top of this file)

# df_sankey, df_policies_addis, df_indicators, df_lca, MPI_hanoi, geojson_hanoi,
# df_sh_hanoi, df_policies_hanoi, isochrones_geojson_files_hanoi,
# df_affordability_hanoi, and df_diet_2_hanoi are now imported from
# data_access.py (see top of file). gdf_food_env_hanoi below is app.py-local
# (not reached into by the layout files, so it stayed here).

# -------------------------- Loading Hanoi Data ------------------------- #

# Hanoi food-environment choropleth (minified base geometry + values CSV when available)
food_env_path_hanoi = os.path.join(hanoi_food_env_dir, "hanoi_fev_vp_fenv_subcity_summary.geojson")
food_env_values_path_hanoi = os.path.join(hanoi_food_env_dir, "hanoi_fev_vp_fenv_indicators.csv")
gdf_food_env_hanoi = None
try:
    gdf_food_env_hanoi = _load_food_env_layer(
        food_env_path_hanoi,
        food_env_values_path_hanoi,
        join_key_candidates=["ma_xa", "shapeID", "Dist_Name", "Dist_name"],
    )
except Exception as e:
    print(f"Error loading Hanoi food environment layer: {e}")

# isochrones_path_hanoi is still used directly below (Hanoi accessibility map
# callback); isochrones_geojson_files_hanoi itself is now imported.
isochrones_path_hanoi = os.path.join(hanoi_food_env_dir, "isochrones_hanoi")


# ── commune climate indicators ───────────────────────────────────────────────
_climate_csv  = os.path.join(hanoi_climate_dir, "hanoi_env_clim_resilience_quarterly_v1.csv")
_communes_path = os.path.join(hanoi_climate_dir, "hanoi_env_clim_boundaries_communes_2025.geojson")
_islands_path = os.path.join(hanoi_resilience_dir, "hanoi_cci_res_clim_vietnam_islands.geojson")

_lulc_stats_csv = os.path.join(hanoi_resilience_dir, "hanoi_cci_res_lulc_statistics.csv")
_communes_geojson_path = os.path.join(hanoi_mpi_dir, "hanoi_drv_igd_mpi_boundaries_communes.geojson")
_region_quarterly_path = os.path.join(hanoi_climate_dir, "hanoi_env_clim_regional_quarterly.csv")
_slopes_path = os.path.join(hanoi_climate_dir, "hanoi_env_clim_regional_slopes.csv")


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
EMDAT_COUNTS_PQ = os.path.join(hanoi_resilience_dir, "hanoi_cci_res_clim_emdat_counts.parquet")
EMDAT_TOTALS_PQ = os.path.join(hanoi_resilience_dir, "hanoi_cci_res_clim_emdat_totals.parquet")
EMDAT_COUNTS_CSV = os.path.join(hanoi_resilience_dir, "hanoi_cci_res_clim_emdat_counts.csv")
EMDAT_TOTALS_CSV = os.path.join(hanoi_resilience_dir, "hanoi_cci_res_clim_emdat_totals.csv")

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

# kpi_card_style, header_style, and card_style below were confirmed
# byte-identical to config.py's copies and are now imported from there
# instead (see the config import block at the top of this file).
# tabs_style and kpi_card_style_2 are NOT deduplicated - they differ from
# config.py's same-named dicts (and dashboard_components.py has a THIRD,
# also-different kpi_card_style_2), so unifying them would be a real visual
# change, not a pure refactor. Left as-is here; flagged separately.

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

# get_sdg_numbers, ATLAS_*, tab-atlas/home-page layout builders (_normalize_indicator_name, _hidden_tab_stubs, indicator_atlas_layout_hanoi,
# _build_home_indicator_buttons, _render_subdomain_hub_layout, landing_page_layout,
# make_region_kpi_card, etc.) now live in tab_layouts.py - imported at the top of
# this file. _resolve_subdomain_layout stays here (not tab_layouts.py) since it calls
# _get_resilience_context(), which is still local to this file.

def _resolve_subdomain_layout(route_city, subdomain_key):
    # Check if subdomain is marked as coming soon
    if _is_subdomain_coming_soon(route_city, subdomain_key):
        return html.Div([
            html.H3('Coming Soon', style={'textAlign': 'center', 'color': '#9ca3af', 'marginTop': '40px'}),
            html.P('This section is currently under development. Check back soon!', 
                   style={'textAlign': 'center', 'color': '#9ca3af', 'fontSize': '16px'})
        ], style={'padding': '20px'})
    
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

# app.layout and its clientside callback now live in app_setup.py, alongside
# the Dash instantiation/auth - imported as `app` at the top of this file.

# ------------------------- Callbacks ------------------------- #


# Callback to store selected city
@app.callback(
    Output('selected-city', 'data'),
    Input('city-selector', 'value')
)
def store_selected_city(city):
    return city


# ------------------------- Chatbot Assistant Callbacks ------------------------- #
# Note: opening/closing/dragging the chatbot widget is handled entirely by
# assets/chatbot_drag.js (plain JS), not a Dash callback - mixing Dash-managed
# style updates with JS-driven drag positioning on the same element risks
# Dash's virtual DOM silently overwriting the dragged position on any
# unrelated re-render. Removing the Dash Output here means Dash never retakes
# ownership of chatbot-panel's style after first render, so JS can safely own
# it completely.


_CHATBOT_ERROR_STYLE_VISIBLE = {
    "display": "block", "padding": "6px 12px", "color": "#a80050",
    "fontSize": "0.85em", "backgroundColor": "white",
}
_CHATBOT_ERROR_STYLE_HIDDEN = {"display": "none"}


@app.callback(
    Output('chatbot-messages', 'children'),
    Output('chatbot-input', 'value'),
    Output('chatbot-pending-trigger', 'data'),
    Output('chatbot-error-banner', 'children'),
    Output('chatbot-error-banner', 'style'),
    Input('chatbot-send-btn', 'n_clicks'),
    Input('chatbot-input', 'n_submit'),
    State('chatbot-input', 'value'),
    State('chatbot-history', 'data'),
    State('atlas-open-tab', 'data'),
    prevent_initial_call=True,
)
def handle_chatbot_send_optimistic(n_clicks, n_submit, user_text, history, atlas_open_tab):
    """Stage 1 (fast): show the user's message + a 'Thinking...' placeholder
    immediately, before the slow LLM call happens - same feel as Claude/ChatGPT,
    where your own message never waits on the reply to appear. Does NOT call
    the LLM and does NOT touch chatbot-history yet; stage 2
    (handle_chatbot_send_real below) does the real work once triggered by the
    chatbot-pending-trigger store changing.
    """
    if not user_text or not user_text.strip():
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    client_key = flask_request.remote_addr or "unknown"
    if not chatbot_engine.check_rate_limit(client_key):
        return (dash.no_update, "",
                dash.no_update,
                "Too many requests - please wait a moment before trying again.",
                _CHATBOT_ERROR_STYLE_VISIBLE)

    user_text = user_text.strip()
    history = history or []
    pending = {"text": user_text, "atlas_open_tab": atlas_open_tab, "sent_at": time.time()}
    return (
        render_pending_turn(history, user_text),
        "",
        pending,
        "",
        _CHATBOT_ERROR_STYLE_HIDDEN,
    )


@app.callback(
    Output('chatbot-history', 'data'),
    Output('chatbot-messages', 'children', allow_duplicate=True),
    Output('chatbot-error-banner', 'children', allow_duplicate=True),
    Output('chatbot-error-banner', 'style', allow_duplicate=True),
    Output('chatbot-quota-display', 'children'),
    Output('chatbot-quota-raw', 'data'),
    Input('chatbot-pending-trigger', 'data'),
    State('chatbot-history', 'data'),
    prevent_initial_call=True,
)
def handle_chatbot_send_real(pending, history):
    """Stage 2 (slow): actually calls the LLM (possibly several tool-call
    round trips) and replaces the 'Thinking...' placeholder with the real
    answer once it's ready. Triggered by stage 1 setting chatbot-pending-trigger."""
    if not pending:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    history = history or []
    try:
        updated_history = chatbot_engine.run_chat_turn(
            history, pending["text"], page_context=pending.get("atlas_open_tab")
        )
    except groq.RateLimitError:
        # Free-tier Groq TPM cap - a real, expected limit, not a bug. Shown
        # plainly instead of dumping the raw provider error JSON into the chat.
        quota = chatbot_engine.get_provider_quota_status()
        return (dash.no_update, render_messages(history),
                "The assistant is getting a lot of requests right now - please "
                "wait a few seconds and try again.", _CHATBOT_ERROR_STYLE_VISIBLE,
                render_quota_status(quota), quota)
    except Exception as exc:
        quota = chatbot_engine.get_provider_quota_status()
        return (dash.no_update, render_messages(history),
                f"Something went wrong: {exc}", _CHATBOT_ERROR_STYLE_VISIBLE,
                render_quota_status(quota), quota)

    quota = chatbot_engine.get_provider_quota_status()
    return (updated_history, render_messages(updated_history), "", _CHATBOT_ERROR_STYLE_HIDDEN,
            render_quota_status(quota), quota)


@app.callback(
    Output('chatbot-quota-display', 'children', allow_duplicate=True),
    Input('chatbot-quota-tick', 'n_intervals'),
    State('chatbot-quota-raw', 'data'),
    prevent_initial_call=True,
)
def refresh_quota_display_age(_n_intervals, quota):
    """Re-render the quota line periodically so the 'as of Xs/m ago' wording
    keeps ticking up between messages - no new API call happens here, since
    Groq only reveals quota state as a side effect of an actual request; this
    just recomputes the age text from the already-known snapshot."""
    if not quota:
        return dash.no_update
    return render_quota_status(quota)


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
        metric_direction_local=metric_color_scale,
        center_default={"lat": 9.0192, "lon":  38.752},
        zoom_default=11,
        city_key="addis",
    )


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
def update_addis_resilience_view(selected_view):
    from addis_layouts import render_addis_resilience_view
    return render_addis_resilience_view(selected_view)

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
        metric_direction_local=metric_color_scale,
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
def _build_drought_map_cached(slider_idx, indicator, min_ag_area=0, infrastructure_layers=(), selected_district=None):
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
        uirevision="resilience-map-ui",
        mapbox_uirevision="resilience-map-ui",
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
        spei_csv = os.path.join(hanoi_climate_dir, "hanoi_env_clim_static_composites.csv")
        spei_df = pd.read_csv(spei_csv)
        spei_df[commune_join_key] = spei_df[commune_join_key].astype(str)
        df = spei_df[keep_cols].dropna(subset=[col])
        slider_style = {"display": "none"}
        plot_gdf = communes_unique.merge(df, on=commune_join_key, how="left")
        #print("DEBUG: plot_gdf columns:", plot_gdf.columns)
    else:
        spei_csv = os.path.join(hanoi_climate_dir, "hanoi_env_clim_static_composites.csv")
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

        choro_opacity = 0.78 if not infrastructure_layers else 0.5

        fig.add_trace(go.Choroplethmapbox(
            geojson=resilience_base_geojson,
            featureidkey=commune_featureidkey,
            locations=overlay[commune_join_key],
            z=overlay[col],
            text=overlay[hover_label_col].astype(str) if hover_label_col else overlay[commune_join_key].astype(str),
            colorscale=cfg["colorscale"],
            zmin=zmin, zmax=zmax,
            marker=dict(opacity=choro_opacity, line=dict(color="white", width=0.4)),
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

    selected_key = str(selected_district).strip() if selected_district is not None else ""
    if selected_key and selected_key in plot_gdf[commune_join_key].astype(str).values:
        selected_geom_series = plot_gdf.loc[
            plot_gdf[commune_join_key].astype(str) == selected_key,
            "geometry",
        ]
        if not selected_geom_series.empty:
            selected_geom = selected_geom_series.iloc[0]
            boundary_traces = []

            def _append_polygon_boundary(poly):
                if poly is None or poly.is_empty:
                    return
                x, y = poly.exterior.xy
                boundary_traces.append(go.Scattermapbox(
                    lon=list(x),
                    lat=list(y),
                    mode='lines',
                    line=dict(color=brand_colors['White'], width=3),
                    hoverinfo='skip',
                    showlegend=False,
                    name='selected-boundary',
                ))

            geom_type = getattr(selected_geom, "geom_type", "")
            if geom_type == "Polygon":
                _append_polygon_boundary(selected_geom)
            elif geom_type == "MultiPolygon":
                for poly in selected_geom.geoms:
                    _append_polygon_boundary(poly)

            # Draw selected boundary last so it remains the top-most map layer.
            for boundary_trace in boundary_traces:
                fig.add_trace(boundary_trace)

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
    Output("resilience-map", "figure"),
    Output("drought-slider-label", "children"),
    Output("date-slider-card", "style"),
    #Output("region-kpi-cards", "children"),
    Input("drought-date-slider", "value"),
    Input("climate-indicator-select", "value"),
    Input("ag-area-filter", "value"),
    Input("infrastructure-layer-select", "value"),
    Input("selected-district", "data"),
)
def update_drought_map(slider_idx, indicator, min_ag_area, infrastructure_layer, selected_district):
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
        str(selected_district).strip() if selected_district else None,
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
        _figure_from_json(fig_json),
        quarter,
        slider_style,
        #dbc.Row(cards),
    )


@app.callback(
    Output("selected-district", "data"),
    Input("resilience-map", "clickData"),
    State("selected-district", "data"),
    prevent_initial_call=True,
)
def persist_selected_district(click_data, prev_selected):
    if not click_data or not click_data.get("points"):
        return prev_selected

    point = click_data["points"][0]
    clicked = point.get("location") or point.get("text") or point.get("hovertext")
    if clicked is None:
        return prev_selected

    clicked_key = str(clicked).strip()
    prev_key = str(prev_selected).strip() if prev_selected else ""

    # Click-to-toggle: clicking the same district again clears selection.
    if clicked_key == prev_key:
        return None
    return clicked_key


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