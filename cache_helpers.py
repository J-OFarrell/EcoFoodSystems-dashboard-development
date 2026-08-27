"""
Small, closure-free caching/compute helpers used by app.py's callbacks.

Each function here takes explicit arguments and depends on nothing beyond
what's passed in (plus, where noted, a stable dataframe already relocated to
data_access.py) - no closures over app.py's own module-level globals. That's
what makes them safe to live in their own module: a broader set of
cache-flavoured functions in app.py still depend on eager-loaded geodataframes
and path constants that remain in app.py itself, so those stay put for now
rather than being split apart from the data they operate on.
"""

import os
from functools import lru_cache

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from shapely.ops import unary_union

from data_access import accessibility_zonal_stats_addis


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
        return None

    geoms = []
    for outlet_category in selected_isochrones_key:
        # Map outlet category to isochrone filename
        # E.g., 'shop_bakery' -> 'isochrone_shop_bakery_multimodal.geojson'
        iso_filename = f"isochrone_{outlet_category}_{selected_transport_mode}.geojson"
        iso_path = os.path.join(isochrones_path_local, iso_filename)

        if os.path.exists(iso_path):
            try:
                gdf = _read_geojson_cached(iso_path)

                # Filter by selected travel time label (time_seconds column)
                if 'threshold_s' in gdf.columns:
                    gdf["threshold_s"] = pd.to_numeric(gdf["threshold_s"], errors='coerce')
                    filtered_gdf = gdf[gdf['threshold_s'].astype(int) == int(selected_time_seconds)]
                    geoms.extend([geom for geom in filtered_gdf.geometry if geom is not None and not geom.is_empty])
                else:
                    geoms.extend([geom for geom in gdf.geometry if geom is not None and not geom.is_empty])
            except Exception:
                import traceback
                traceback.print_exc()
        else:
            print(f"DEBUG: Isochrone file not found: {iso_path}")

    try:
        unioned = unary_union(geoms)
        # Create GeoDataFrame in EPSG:4326 (isochrones already in this CRS)
        union_gdf = gpd.GeoDataFrame({"geometry": [unioned]}, crs="EPSG:4326")
        return union_gdf.to_json()
    except Exception:
        import traceback
        traceback.print_exc()
        return None


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
