"""
Tool functions exposed to the dashboard assistant chatbot.

Each tool is deliberately narrow: it returns only the specific fields asked
for, never a raw dataframe dump. All data comes from data_access.py (a
clean, dedicated module) - not from app.py's internals.
"""

import pandas as pd

from data_access import (
    atlas_records,
    is_indicator_available_for_city,
    df_mpi,
    df_mpi_hanoi,
    df_lca,
    df_affordability_hanoi,
    df_diet_2_hanoi,
    accessibility_zonal_stats_addis,
)

_REGION_COLUMN = {"addis": "Dist_Name", "hanoi": "Name"}

_ACCESSIBILITY_DISTRICT_COLUMNS = [
    "Akaki Kality", "Nifas Silk Lafto", "Kolfe Keraniyo", "Bole", "Lideta",
    "Kirkos", "Yeka", "Addis Ketema", "Arada", "Gulele", "Lemi Kura",
]
_ACCESSIBILITY_TIME_MINUTES_TO_SECONDS = {5: 300, 10: 600, 15: 900}


def _resolve_categorical(value, valid_values):
    """Exact-then-substring match against a small fixed set of valid values."""
    value_lower = value.strip().lower()
    for v in valid_values:
        if v.lower() == value_lower:
            return v
    for v in valid_values:
        if value_lower in v.lower():
            return v
    return None

# Long-format Hanoi time-series datasets (Year, Cat, Reg, value columns -
# identically named on both, just different column order) tried by
# get_indicator_value when the MPI dataset has no match. See that function's
# docstring for why not every dataset in the app is wired up this way yet.
_HANOI_TIME_SERIES_DATASETS = [df_affordability_hanoi, df_diet_2_hanoi]


def describe_indicator(indicator_name):
    """Look up an indicator's description, pillar, sub-domain, and documented data source from the atlas."""
    name_lower = indicator_name.strip().lower()

    for rec in atlas_records:
        if rec.get("Indicator name", "").strip().lower() == name_lower:
            return {
                "indicator_name": rec.get("Indicator name"),
                "pillar": rec.get("FCD Primary Pillar"),
                "sub_domain": rec.get("FCD Sub-domain"),
                "domain": rec.get("Domain / Sub-theme"),
                "data_source": rec.get("Data source") or "Not documented in the atlas.",
                "data_accessibility": rec.get("Data accessibility (open/internal/restricted)") or None,
            }

    candidates = [
        rec.get("Indicator name") for rec in atlas_records
        if name_lower in rec.get("Indicator name", "").strip().lower()
    ]
    if candidates:
        return {"note": "No exact match. Did you mean one of these?", "candidates": candidates[:5]}
    return {"error": f"No indicator found matching '{indicator_name}'."}


def list_available_indicators(city, pillar=None):
    """List indicators available (not 'coming soon') for a city, optionally filtered by pillar."""
    city = city.strip().lower()
    results = []
    for rec in atlas_records:
        if not is_indicator_available_for_city(rec, city):
            continue
        if pillar and pillar.strip().lower() not in (rec.get("FCD Primary Pillar") or "").strip().lower():
            continue
        results.append({
            "indicator_name": rec.get("Indicator name"),
            "pillar": rec.get("FCD Primary Pillar"),
            "sub_domain": rec.get("FCD Sub-domain"),
            "domain": rec.get("Domain / Sub-theme"),
        })
    return {"city": city, "count": len(results), "indicators": results}


def get_indicator_value(city, indicator_key, region=None, year=None):
    """Look up the actual value(s) of a named indicator for a city/region.

    Tries the Multidimensional Poverty Index (MPI) dataset first, then - for
    Hanoi - the affordability and diet time-series datasets, since those are
    the three datasets currently wired up here. (Food-item-keyed LCA data has
    a different shape entirely - see get_food_item_environmental_impact.
    Several other real datasets in the app - resilience/climate, disaster,
    land-use, food-environment accessibility - are NOT wired up yet; if none
    of the tried datasets match, say plainly that this indicator's data isn't
    available through this tool rather than concluding the dashboard has no
    such data at all.)

    The atlas's conceptual indicator names (e.g. "Living standard dimension")
    don't always match a dataset's literal variable/category names (e.g.
    "Multidimensional Poverty Index", "riceAfford") - so an exact match is
    tried first, then a substring match, before giving up. On total failure,
    the real available keys are returned so the caller (the model) can retry
    with a valid one instead of concluding no data exists at all.
    """
    city = city.strip().lower()
    key_lower = indicator_key.strip().lower()
    region_col = _REGION_COLUMN.get(city, "Dist_Name")

    # 1. MPI dataset (original behavior, unchanged)
    df = df_mpi_hanoi if city == "hanoi" else df_mpi
    variable_series = df["Variable"].str.strip()
    matches = df[variable_series.str.lower() == key_lower]

    resolved_key = indicator_key
    if matches.empty:
        substring_matches = variable_series[variable_series.str.lower().str.contains(key_lower, na=False)]
        if not substring_matches.empty:
            resolved_key = substring_matches.iloc[0]
            matches = df[variable_series == resolved_key]

    if region and not matches.empty:
        matches = matches[matches[region_col].str.strip().str.lower() == region.strip().lower()]

    if not matches.empty:
        return {
            "city": city,
            "indicator": resolved_key,
            "values": [
                {"region": row[region_col], "value": row["Value"]}
                for _, row in matches.iterrows()
            ],
        }

    mpi_available = set(variable_series.unique().tolist())

    # 2. Hanoi time-series datasets (affordability, diet) - Hanoi only
    if city == "hanoi":
        for ts_df in _HANOI_TIME_SERIES_DATASETS:
            cat_series = ts_df["Cat"].str.strip()
            ts_matches = ts_df[cat_series.str.lower() == key_lower]
            ts_resolved_key = indicator_key
            if ts_matches.empty:
                ts_substring = cat_series[cat_series.str.lower().str.contains(key_lower, na=False)]
                if not ts_substring.empty:
                    ts_resolved_key = ts_substring.iloc[0]
                    ts_matches = ts_df[cat_series == ts_resolved_key]

            if ts_matches.empty:
                continue

            if year is not None:
                ts_matches = ts_matches[ts_matches["Year"] == int(year)]
            else:
                latest_year = ts_matches["Year"].max()
                ts_matches = ts_matches[ts_matches["Year"] == latest_year]

            if region and not ts_matches.empty:
                ts_matches = ts_matches[ts_matches["Reg"].str.strip().str.lower() == region.strip().lower()]

            if not ts_matches.empty:
                return {
                    "city": city,
                    "indicator": ts_resolved_key,
                    "year": int(ts_matches["Year"].iloc[0]),
                    "values": [
                        {"region": row["Reg"], "value": row["value"]}
                        for _, row in ts_matches.iterrows()
                    ],
                }

    # Total failure across every dataset tried for this city
    available = set(mpi_available)
    if city == "hanoi":
        for ts_df in _HANOI_TIME_SERIES_DATASETS:
            available.update(ts_df["Cat"].str.strip().unique().tolist())

    detail = f" region '{region}'" if region else ""
    return {
        "error": f"No data found for indicator '{indicator_key}' in {city}{detail}.",
        "available_indicator_keys_for_this_city": sorted(available),
    }


def get_food_item_environmental_impact(food_item=None, food_group=None):
    """Look up Life Cycle Assessment (LCA) environmental-impact values for
    Addis Ababa food items: GHG emissions, freshwater consumption,
    acidification, and eutrophication. Addis-only - no Hanoi data exists for
    this indicator.

    Accepts either a specific food_item (e.g. 'Injera') or a food_group (e.g.
    'Cereals & Grains') to return every item in that group - the dashboard
    page groups items by food group, so a user referencing the group they're
    looking at (rather than one specific item) should still get real data
    back, not a "no match" error.
    """
    if not food_item and not food_group:
        return {"error": "Provide either food_item or food_group."}

    if food_item:
        item_series = df_lca["Item Cd"].str.strip()
        key_lower = food_item.strip().lower()
        matches = df_lca[item_series.str.lower() == key_lower]
        if matches.empty:
            matches = df_lca[item_series.str.lower().str.contains(key_lower, na=False)]
    else:
        group_series = df_lca["Food Group"].str.strip()
        key_lower = food_group.strip().lower()
        matches = df_lca[group_series.str.lower() == key_lower]
        if matches.empty:
            matches = df_lca[group_series.str.lower().str.contains(key_lower, na=False)]

    if matches.empty:
        return {
            "error": (
                f"No matching food item or food group found for "
                f"food_item={food_item!r}, food_group={food_group!r}."
            ),
            "available_food_items": sorted(df_lca["Item Cd"].unique().tolist()),
            "available_food_groups": sorted(df_lca["Food Group"].unique().tolist()),
        }

    return {
        "city": "addis",
        "items": [
            {
                "food_item": row["Item Cd"],
                "food_group": row["Food Group"],
                "total_ghg_emissions": row["Total GHG Emissions"],
                "freshwater_consumption_liters": row["Freshwater Comsumption (l)"],
                "acidification_kg_so2eq": row["Acidification (kg SO2eq)"],
                "eutrophication_kg_po4eq": row["Eutrophication (kg PO43-eq)"],
            }
            for _, row in matches.iterrows()
        ],
    }


def get_food_accessibility_value(population_category, offer_category, transport_mode=None, travel_time_minutes=None):
    """Look up what percentage of a population group, per Addis Ababa district,
    lives within reach of a given food-outlet category (e.g. 'what % of men
    are within a 15-minute walk of a beverage shop, by district').

    Backed by a dataset shaped very differently from get_indicator_value's -
    districts are COLUMNS here, not rows, and the row you need is selected by
    FOUR filters (population category, outlet category, transport mode,
    travel time) rather than a single indicator name. Addis-only. transport_mode
    defaults to 'walk' and travel_time_minutes defaults to 15 (the widest,
    most inclusive catchment) if not specified.
    """
    df = accessibility_zonal_stats_addis
    pop_values = sorted(df["pop_cat"].dropna().unique().tolist())
    offer_values = sorted(df["offer_cat"].dropna().unique().tolist())

    resolved_pop = _resolve_categorical(population_category, pop_values)
    resolved_offer = _resolve_categorical(offer_category, offer_values)

    if resolved_pop is None or resolved_offer is None:
        return {
            "error": (
                f"Could not resolve population_category={population_category!r} "
                f"or offer_category={offer_category!r}."
            ),
            "available_population_categories": pop_values,
            "available_offer_categories": offer_values,
        }

    mode = (transport_mode or "walk").strip().lower()
    if mode not in ("walk", "drive", "multimodal"):
        mode = "walk"

    time_minutes = int(travel_time_minutes) if travel_time_minutes else 15
    time_seconds = _ACCESSIBILITY_TIME_MINUTES_TO_SECONDS.get(time_minutes, 900)

    row = df[
        (df["pop_cat"] == resolved_pop)
        & (df["offer_cat"] == resolved_offer)
        & (df["mode"] == mode)
        & (df["time"] == time_seconds)
    ]

    if row.empty:
        return {
            "error": (
                f"No data found for population_category={resolved_pop!r}, "
                f"offer_category={resolved_offer!r}, transport_mode={mode!r}, "
                f"travel_time_minutes={time_minutes!r}."
            ),
        }

    row = row.iloc[0]
    values = {
        district: (None if pd.isna(row[district]) else row[district])
        for district in _ACCESSIBILITY_DISTRICT_COLUMNS
    }

    return {
        "city": "addis",
        "population_category": resolved_pop,
        "offer_category": resolved_offer,
        "transport_mode": mode,
        "travel_time_minutes": time_minutes,
        "values_by_district_pct": values,
    }


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "describe_indicator",
            "description": (
                "Get the description, pillar, sub-domain, and documented data source "
                "of a named dashboard indicator. Use when the user asks what an "
                "indicator means, where to find it, or where its data comes from."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "indicator_name": {
                        "type": "string",
                        "description": "e.g. 'Multidimensional Poverty Index'",
                    }
                },
                "required": ["indicator_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_indicators",
            "description": (
                "List which indicators are currently available (not 'coming soon') "
                "for a given city, optionally filtered by pillar. Use for navigation "
                "questions like 'where do I find X' or 'what's available for Hanoi'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "enum": ["addis", "hanoi"]},
                    "pillar": {
                        "type": ["string", "null"],
                        "description": "Optional pillar name, e.g. 'Drivers', 'Food Environments'. Omit or use null if not filtering.",
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_indicator_value",
            "description": (
                "Look up the actual current value(s) of an indicator for a city, "
                "optionally for one specific district/commune/region and (for "
                "time-series indicators) one specific year. Covers the "
                "Multidimensional Poverty Index (MPI) dataset for both cities, "
                "plus - Hanoi only - food affordability and child/maternal diet "
                "indicators. Does NOT cover food-item-level environmental/LCA data "
                "(use get_food_item_environmental_impact for that) or several other "
                "dashboard datasets not yet wired up (e.g. resilience/climate, "
                "disaster, land-use, food-environment accessibility) - if this "
                "returns no match, say the data isn't available through this tool "
                "rather than concluding the dashboard has no such data at all."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "enum": ["addis", "hanoi"]},
                    "indicator_key": {
                        "type": "string",
                        "description": (
                            "e.g. 'Multidimensional Poverty Index', 'Cooking fuel', "
                            "'Housing', 'Sanitation' (both cities); 'foodExp_totalExp', "
                            "'riceAfford' (Hanoi affordability); 'Stunting in children "
                            "under 5 years' (Hanoi diet)"
                        ),
                    },
                    "region": {
                        "type": ["string", "null"],
                        "description": "Optional district/commune/region name to filter to one region (e.g. 'Hanoi', 'Vietnam' for the time-series datasets). Omit or use null if not filtering.",
                    },
                    "year": {
                        "type": ["integer", "null"],
                        "description": "Optional year, only meaningful for the Hanoi affordability/diet time-series datasets (ignored for MPI). Omit or use null for the most recent available year.",
                    },
                },
                "required": ["city", "indicator_key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_food_item_environmental_impact",
            "description": (
                "Look up Life Cycle Assessment (LCA) environmental-impact data for "
                "Addis Ababa food items: GHG emissions, freshwater consumption, "
                "acidification, and eutrophication. Addis-only, no Hanoi data. Use "
                "for the 'Life cycle assessment of food items' indicator (Processing "
                "and packaging / Food Supply Chains). Pass food_group (e.g. 'Cereals "
                "& Grains') to get every item in that group at once if the user "
                "references a group/page rather than one specific item."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "food_item": {
                        "type": ["string", "null"],
                        "description": "e.g. 'Injera', 'Maize', 'Teff'. Omit or use null if querying by food_group instead.",
                    },
                    "food_group": {
                        "type": ["string", "null"],
                        "description": "e.g. 'Cereals & Grains', 'Dairy & Eggs', 'Meat'. Omit or use null if querying by food_item instead.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_food_accessibility_value",
            "description": (
                "Look up what percentage of a population group, by Addis Ababa "
                "district, lives within reach of a given food-outlet category - "
                "e.g. 'what % of men are within a 15-minute walk of a beverage "
                "shop, by district'. Use for the 'Food outlet accessibility' "
                "indicator (Food Environments / Vendor properties) and similar "
                "accessibility questions. Addis-only, no Hanoi data. Districts are "
                "returned as one value each per call - there is no single "
                "'the value' the way get_indicator_value returns; population "
                "category and outlet category are both required."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "population_category": {
                        "type": "string",
                        "description": "e.g. 'men', 'women', 'total', 'youth', 'elderly', 'children_u5', 'women_rep'",
                    },
                    "offer_category": {
                        "type": "string",
                        "description": "e.g. 'beverages', 'bakery', 'healthy_offers', 'unhealthy_offers', 'supermarket', 'fast_food'",
                    },
                    "transport_mode": {
                        "type": ["string", "null"],
                        "description": "'walk', 'drive', or 'multimodal'. Omit or use null to default to 'walk'.",
                    },
                    "travel_time_minutes": {
                        "type": ["integer", "null"],
                        "description": "5, 10, or 15 minutes. Omit or use null to default to 15 (the widest catchment).",
                    },
                },
                "required": ["population_category", "offer_category"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "describe_indicator": describe_indicator,
    "list_available_indicators": list_available_indicators,
    "get_indicator_value": get_indicator_value,
    "get_food_item_environmental_impact": get_food_item_environmental_impact,
    "get_food_accessibility_value": get_food_accessibility_value,
}
