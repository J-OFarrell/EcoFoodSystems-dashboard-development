"""
Shared data access for EcoFoodSystems Dashboard.

Consolidates data loading that both app.py and other modules (shared_components.py,
chatbot_tools.py) need, so they read from one place instead of each loading it
independently.
"""

import csv
import json
import os
from io import StringIO

import geopandas as gpd
import pandas as pd

_HOMEPATH = os.path.dirname(os.path.abspath(__file__))
_DATA_ROOT = os.path.join(_HOMEPATH, "assets", "data")

_ADDIS_ROOT = os.path.join(_DATA_ROOT, "addis")
_ADDIS_MPI_DIR = os.path.join(_ADDIS_ROOT, "drivers_income-growth-and-distribution")
_ADDIS_STAKEHOLDERS_DIR = os.path.join(_ADDIS_ROOT, "cross-cutting-issues_governance")
_ADDIS_FOOD_ENV_DIR = os.path.join(_ADDIS_ROOT, "food-environments_vendor-properties")
_ADDIS_POLICY_DIR = os.path.join(_ADDIS_ROOT, "drivers_policies-and-leadership")
_ADDIS_ENVIRONMENT_DIR = os.path.join(_ADDIS_ROOT, "drivers_environment-and-climate-change")

_HANOI_ROOT = os.path.join(_DATA_ROOT, "hanoi")
_HANOI_MPI_DIR = os.path.join(_HANOI_ROOT, "drivers_income-growth-and-distribution")
_HANOI_STAKEHOLDERS_DIR = os.path.join(_HANOI_ROOT, "cross-cutting-issues_governance")
_HANOI_POLICY_DIR = os.path.join(_HANOI_ROOT, "drivers_policies-and-leadership")
_HANOI_SUPPLY_DIR = os.path.join(_HANOI_ROOT, "food-supply-chains_production-systems-and-input-supply")
_HANOI_AFFORDABILITY_DIR = os.path.join(_HANOI_ROOT, "food-environments_food-affordability")
_HANOI_NUTRITION_DIR = os.path.join(_HANOI_ROOT, "outcomes_nutritional-status")
_HANOI_FOOD_ENV_DIR = os.path.join(_HANOI_ROOT, "food-environments_vendor-properties")

ATLAS_CSV_PATH = os.path.join(_HOMEPATH, "EcoFoodSystems_FCD_aligned.csv")


def load_indicator_atlas_records(csv_path):
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

    if rows is None:
        with open(csv_path, 'rb') as f:
            text = f.read().decode('utf-8', errors='replace')
        rows = list(csv.reader(StringIO(text)))

    if len(rows) < 2:
        return []

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


def is_indicator_available_for_city(rec, selected_city):
    field = 'Available Hanoi' if selected_city == 'hanoi' else 'Available Addis'
    val = str(rec.get(field, '')).strip().lower()
    return val in {'1', 'true', 'yes', 'y'}


atlas_records = load_indicator_atlas_records(ATLAS_CSV_PATH)

# The exact, complete set of top-level pillar names, derived from the atlas
# itself rather than hardcoded - so if the CSV's pillar set ever changes,
# this stays correct automatically instead of silently going stale.
PILLARS = sorted({
    rec.get("FCD Primary Pillar", "").strip()
    for rec in atlas_records
    if rec.get("FCD Primary Pillar", "").strip()
})

df_mpi = pd.read_csv(os.path.join(_ADDIS_MPI_DIR, "addis_drv_igd_mpi_indicators_long.csv"))
df_mpi_hanoi = pd.read_csv(os.path.join(_HANOI_MPI_DIR, "hanoi_drv_igd_mpi_indicators_long.csv"))

# addis_drv_igd_mpi_indicators_long.csv only has the 6 MPI sub-components
# (Assets, Cooking fuel, Drinking water, Electricity, Housing, Sanitation) -
# the composite "Multidimensional Poverty Index" score lives separately in the
# boundaries GeoJSON (wide format). Append it as long-format rows so df_mpi is
# a complete, consistent (Dist_Name, Variable, Value) table like df_mpi_hanoi.
_addis_mpi_boundaries = gpd.read_file(
    os.path.join(_ADDIS_MPI_DIR, "addis_drv_igd_mpi_boundaries.geojson")
)
_composite_mpi_rows = _addis_mpi_boundaries[["Dist_Name", "Multidimensional Poverty Index"]].rename(
    columns={"Multidimensional Poverty Index": "Value"}
)
_composite_mpi_rows["Value"] = pd.to_numeric(_composite_mpi_rows["Value"], errors="coerce")
_composite_mpi_rows["Variable"] = "Multidimensional Poverty Index"
df_mpi = pd.concat([df_mpi, _composite_mpi_rows[["Dist_Name", "Variable", "Value"]]], ignore_index=True)

# ============================================================================
# Data below was originally loaded directly in app.py and reached into via
# `import app as main` (inside function bodies) by addis_layouts.py and
# hanoi_layouts.py - a circular-dependency workaround, since app.py imports
# layout functions FROM those files at the top. Moving the loading here lets
# both app.py and the layout files import these names directly instead.
# ============================================================================

# Addis MPI geodataframe (used directly by app.py's Addis map/bar callbacks,
# and to compute `variables` below).
MPI = gpd.read_file(os.path.join(_ADDIS_MPI_DIR, "addis_drv_igd_mpi_boundaries.geojson"))
MPI['Multidimensional Poverty Index'] = MPI['Multidimensional Poverty Index'].astype(float)
MPI['Dist_Name'] = MPI['Dist_Name'].astype(str)
geojson = json.loads(MPI.to_json())

for _col in MPI.columns:
    if _col in ['geometry', 'Dist_Name']:
        continue
    _coerced = pd.to_numeric(MPI[_col], errors='coerce')
    if _coerced.notna().any():
        MPI[_col] = _coerced

# Universal list of MPI variables (source of truth for dropdown ordering)
mpi_vars = [
    'Multidimensional Poverty Index',
    'Cooking fuel',
    'Housing',
    'Assets',
    'Drinking water',
    'Sanitation',
    'Electricity',
]

# For Addis, use the universal list but only include variables present in the GeoDataFrame
variables = [v for v in mpi_vars if v in MPI.columns]

# Food Systems Stakeholders Data (Addis)
df_sh = pd.read_csv(
    os.path.join(_ADDIS_STAKEHOLDERS_DIR, "addis_cci_gov_stk_database_cleaned.csv")
).dropna(how='any').astype(str)
df_sh.rename(columns={'Area of Activity (Food Systems Value Chain)': 'Area of Activity'}, inplace=True)
if 'Website' in df_sh.columns:
    df_sh['Website'] = df_sh['Website'].apply(
        lambda x: f'[Link Available]({x})' if x and x.startswith('http') else '--'
    )

# Food outlet GeoJSON file list (Addis)
outlets_geojson_files_addis = sorted(os.listdir(os.path.join(_ADDIS_FOOD_ENV_DIR, "jsons_addis_foodoutlets")))

# Policy database (Addis)
df_policies_addis = pd.read_csv(os.path.join(_ADDIS_POLICY_DIR, 'addis_drv_pl_pol_faolex.csv'))
for _col in ('Document URL', 'Record URL', 'Available website'):
    if _col in df_policies_addis.columns:
        df_policies_addis[_col] = df_policies_addis[_col].apply(
            lambda x: f'[Link Available]({x})' if x and str(x).startswith('http') else '--'
        )

# SDG/policy indicators (Addis) - shared by 3 layout call sites
df_indicators = pd.read_csv(os.path.join(_ADDIS_POLICY_DIR, 'addis_drv_pl_pol_expanded_sdg.csv'))


def _get_sdg_numbers(row):
    sdg_cols = ['SDG_1', 'SDG_2', 'SDG_3', 'SDG_4', 'SDG_5']
    sdg_numbers = []
    for col in sdg_cols:
        if pd.notna(row[col]) and str(row[col]).strip():
            sdg_num = str(row[col]).split('.')[0]
            if sdg_num.isdigit() and sdg_num not in sdg_numbers:
                sdg_numbers.append(sdg_num)
    return ', '.join(sdg_numbers) if sdg_numbers else '--'


df_indicators['SDG Numbers'] = df_indicators.apply(_get_sdg_numbers, axis=1)

# LCA/environmental footprints (Addis)
df_lca = pd.read_csv(os.path.join(_ADDIS_ENVIRONMENT_DIR, 'addis_drv_ecc_env_lca_pivot.csv'))

# Supply flow data for the Hanoi Sankey diagram (both `update_sankey` and
# `update_sankey_hanoi` callbacks in app.py use this - it's genuinely Hanoi
# data despite the unsuffixed callback's ids not saying so).
df_sankey = pd.read_csv(os.path.join(_HANOI_SUPPLY_DIR, 'hanoi_fsc_psis_supply_flows.csv'))

# Hanoi MPI geodataframe (commune level)
MPI_hanoi = gpd.read_file(os.path.join(_HANOI_MPI_DIR, "hanoi_drv_igd_mpi_boundaries_communes.geojson"))
MPI_hanoi['Name'] = MPI_hanoi['Name'].astype(str)
MPI_hanoi['ma_xa'] = MPI_hanoi['ma_xa'].astype(str)

_df_mpi_wide = df_mpi_hanoi.pivot_table(index='Name', columns='Variable', values='Value').reset_index()
_df_mpi_wide.columns.name = None
MPI_hanoi = MPI_hanoi.merge(_df_mpi_wide, on='Name', how='left')

for _col in MPI_hanoi.columns:
    if _col in ['geometry', 'Name', 'ma_xa']:
        continue
    _coerced = pd.to_numeric(MPI_hanoi[_col], errors='coerce')
    if _coerced.notna().any():
        MPI_hanoi[_col] = _coerced

geojson_hanoi = json.loads(MPI_hanoi.to_json())

# Stakeholders Data (Hanoi)
df_sh_hanoi = pd.read_csv(
    os.path.join(_HANOI_STAKEHOLDERS_DIR, "hanoi_cci_gov_stk_database.csv")
).dropna(how='any').astype(str)
if 'Website' in df_sh_hanoi.columns:
    df_sh_hanoi['Website'] = df_sh_hanoi['Website'].apply(
        lambda x: f'[Link Available]({x})' if x and x.startswith('http') else '--'
    )

# Policy database (Hanoi)
df_policies_hanoi = pd.read_csv(os.path.join(_HANOI_POLICY_DIR, 'hanoi_drv_pl_pol_database_cleaned.csv'))
if 'Document Link' in df_policies_hanoi.columns:
    df_policies_hanoi['Document Link'] = df_policies_hanoi['Document Link'].apply(
        lambda x: f'[Link Available]({x})' if x and str(x).startswith('http') else '--'
    )
    df_policies_hanoi['Available website'] = df_policies_hanoi['Available website'].apply(
        lambda x: f'[Link Available]({x})' if x and str(x).startswith('http') else '--'
    )

# Isochrone GeoJSON file list (Hanoi)
_isochrones_path_hanoi = os.path.join(_HANOI_FOOD_ENV_DIR, "isochrones_hanoi")
isochrones_geojson_files_hanoi = (
    sorted(os.listdir(_isochrones_path_hanoi)) if os.path.exists(_isochrones_path_hanoi) else []
)

# Affordability data (Hanoi)
df_affordability_hanoi = pd.read_csv(
    os.path.join(_HANOI_AFFORDABILITY_DIR, 'hanoi_fev_aff_afford_indicators_cleaned.csv')
)

# Dietary/nutrition data (Hanoi)
df_diet_2_hanoi = pd.read_csv(
    os.path.join(_HANOI_NUTRITION_DIR, 'hanoi_out_ns_nut_health_indicators_cleaned.csv')
)

# Accessibility outlet dropdown options + zonal stats (Addis) - needed by
# both app.py's own accessibility-map callbacks and addis_layouts.py's
# accessibility tab (previously reached via `import app as main`).

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

_accessibility_zonal_stats_path_addis = os.path.join(_ADDIS_FOOD_ENV_DIR, "addis_fev_vp_fenv_accessibility_stats.csv")


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


(
    accessibility_zonal_stats_addis,
    accessibility_subcity_columns_addis,
    accessibility_population_options_addis,
    accessibility_offer_options_addis,
) = _load_accessibility_zonal_stats(_accessibility_zonal_stats_path_addis)

# NOTE: outlets_geojson_files_hanoi is intentionally NOT defined here. In the
# original app.py it was commented out (never loaded), while
# hanoi_layouts.py::food_affordability_tab_layout unconditionally read
# `main.outlets_geojson_files_hanoi` with no fallback - meaning that tab has
# always raised AttributeError when opened. This refactor preserves that
# pre-existing bug exactly rather than silently fixing it (see hanoi_layouts.py).
