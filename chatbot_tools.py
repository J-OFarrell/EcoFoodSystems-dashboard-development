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
    df_affordability_hanoi,
    df_diet_2_hanoi,
    find_temporal_indicator,
    df_lca,
    accessibility_zonal_stats_addis,
    accessibility_population_options_addis,
    accessibility_offer_options_addis,
    accessibility_zonal_stats_hanoi,
    accessibility_population_options_hanoi,
    accessibility_offer_options_hanoi,
)

_REGION_COLUMN = {"addis": "Dist_Name", "hanoi": "Name"}

# Datasets get_indicator_value searches, in order, for a given city. Each is a
# "long format" table: one categorical column names the indicator, one column
# holds its value, one names the region. MPI has no Year (single snapshot);
# affordability/nutrition are yearly and only have 'Hanoi'/'Vietnam' as their
# two region values (no per-district breakdown), unlike MPI's real districts.
_INDICATOR_DATASETS = {
    "addis": [
        {"df": df_mpi, "category_col": "Variable", "value_col": "Value", "region_col": "Dist_Name", "year_col": None},
    ],
    "hanoi": [
        {"df": df_mpi_hanoi, "category_col": "Variable", "value_col": "Value", "region_col": "Name", "year_col": None},
        {"df": df_affordability_hanoi, "category_col": "Cat", "value_col": "value", "region_col": "Reg", "year_col": "Year"},
        {"df": df_diet_2_hanoi, "category_col": "Cat", "value_col": "value", "region_col": "Reg", "year_col": "Year"},
    ],
}


def describe_indicator(indicator_name):
    """Look up an indicator's description, pillar, and sub-domain from the atlas."""
    name_lower = indicator_name.strip().lower()

    for rec in atlas_records:
        if rec.get("Indicator name", "").strip().lower() == name_lower:
            return {
                "indicator_name": rec.get("Indicator name"),
                "pillar": rec.get("FCD Primary Pillar"),
                "sub_domain": rec.get("FCD Sub-domain"),
                "domain": rec.get("Domain / Sub-theme"),
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
    """Look up specific value(s) for an MPI, Hanoi food-affordability, or Hanoi
    nutrition indicator, for a city/region/(year where applicable).

    Searches each dataset registered for the city in turn (MPI first, so its
    behaviour is unchanged from before affordability/nutrition were added).
    The atlas's conceptual indicator names (e.g. "Living standard dimension")
    don't always match a dataset's literal variable names (e.g.
    "Multidimensional Poverty Index", "Housing", "Sanitation") - so an exact
    match is tried first, then a substring match, before giving up. On total
    failure across every dataset, the real available variable names (from
    whichever dataset came closest) are returned so the caller (the model)
    can retry with a valid one instead of concluding no data exists at all.
    """
    city = city.strip().lower()
    key_lower = indicator_key.strip().lower()
    datasets = _INDICATOR_DATASETS.get(city, [])

    last_available = []
    for spec in datasets:
        df = spec["df"]
        category_col, value_col, region_col, year_col = (
            spec["category_col"], spec["value_col"], spec["region_col"], spec["year_col"]
        )

        category_series = df[category_col].astype(str).str.strip()
        matches = df[category_series.str.lower() == key_lower]

        resolved_key = indicator_key
        if matches.empty:
            substring_matches = category_series[category_series.str.lower().str.contains(key_lower, na=False)]
            if not substring_matches.empty:
                resolved_key = substring_matches.iloc[0]
                matches = df[category_series == resolved_key]

        if matches.empty:
            last_available = sorted(category_series.unique().tolist())
            continue

        if region and not matches.empty:
            matches = matches[matches[region_col].astype(str).str.strip().str.lower() == region.strip().lower()]
        if year is not None and year_col and not matches.empty:
            matches = matches[pd.to_numeric(matches[year_col], errors="coerce") == int(year)]

        if matches.empty:
            continue

        return {
            "city": city,
            "indicator": resolved_key,
            "values": [
                {
                    "region": row[region_col],
                    **({"year": int(row[year_col])} if year_col and pd.notna(row[year_col]) else {}),
                    "value": row[value_col] if pd.notna(row[value_col]) else None,
                }
                for _, row in matches.iterrows()
            ],
        }

    detail = f" region '{region}'" if region else ""
    detail += f" year {year}" if year is not None else ""
    return {
        "error": f"No data found for indicator '{indicator_key}' in {city}{detail}.",
        "available_indicator_keys_for_this_city": last_available,
    }


def get_subdomain_indicator_value(city, indicator_name, year=None):
    """Look up a value from one of the dashboard's per-subdomain time-series
    datasets (Drivers, Food Supply Chains, Food Environments, Individual
    Factors, Cross-Cutting Issues, Outcomes) - e.g. GRDP growth, population,
    literacy rate, diesel price, poverty rate, social security coverage.

    This is separate from get_indicator_value, which only covers MPI and the
    Hanoi affordability/nutrition datasets - those are different files with a
    different shape (one row per region/year) from these (one row per
    year/quarter/month, one column per indicator). Currently Hanoi-only; no
    equivalent per-subdomain files exist for Addis yet.
    """
    city = city.strip().lower()
    found = find_temporal_indicator(city, indicator_name)
    if found is None:
        return {"error": f"No time-series indicator found matching '{indicator_name}' for {city}."}

    df, match_col, subdomain = found
    df = df.copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df[match_col] = pd.to_numeric(df[match_col], errors="coerce")
    has_quarter = "Quarter" in df.columns
    has_month = "Month" in df.columns
    sort_cols = ["Year"] + (["Quarter"] if has_quarter else []) + (["Month"] if has_month else [])

    df = df.dropna(subset=["Year", match_col]).sort_values(sort_cols)
    if df.empty:
        return {"error": f"Indicator '{match_col}' exists for {city} but has no numeric data."}

    def _row_to_point(row):
        point = {"year": int(row["Year"])}
        if has_quarter and pd.notna(row.get("Quarter")):
            point["quarter"] = row["Quarter"]
        if has_month and pd.notna(row.get("Month")):
            point["month"] = row["Month"]
        point["value"] = row[match_col]
        return point

    if year is not None:
        year_rows = df[df["Year"] == int(year)]
        if year_rows.empty:
            return {
                "error": f"No data for '{match_col}' in {year}.",
                "available_years": sorted(df["Year"].astype(int).unique().tolist()),
            }
        return {
            "city": city,
            "indicator": match_col,
            "subdomain": subdomain,
            "values": [_row_to_point(row) for _, row in year_rows.iterrows()],
        }

    # No year given: return latest + earliest points, enough for a trend
    # answer without dumping a potentially multi-year monthly series.
    return {
        "city": city,
        "indicator": match_col,
        "subdomain": subdomain,
        "latest": _row_to_point(df.iloc[-1]),
        "earliest": _row_to_point(df.iloc[0]),
        "note": "Pass a specific 'year' to this tool to get all data points for that year.",
    }


def get_food_item_environmental_impact(food_item=None, food_group=None):
    """Look up a food item's (Addis-only) environmental footprint: total GHG
    emissions, freshwater consumption, acidification, and eutrophication.
    Pass food_item for one specific item, or food_group to summarize every
    item in that group. No equivalent data exists for Hanoi yet.
    """
    if not food_item and not food_group:
        return {"error": "Provide either food_item or food_group."}

    if food_item:
        item_series = df_lca["Item Cd"].astype(str).str.strip()
        key_lower = food_item.strip().lower()
        matches = df_lca[item_series.str.lower() == key_lower]
        resolved = food_item
        if matches.empty:
            substring = item_series[item_series.str.lower().str.contains(key_lower, regex=False, na=False)]
            if not substring.empty:
                resolved = substring.iloc[0]
                matches = df_lca[item_series == resolved]
        if matches.empty:
            return {
                "error": f"No food item found matching '{food_item}'.",
                "available_food_items": sorted(item_series.unique().tolist()),
            }
        row = matches.iloc[0]
        return {
            "food_item": row["Item Cd"],
            "food_group": row["Food Group"],
            "total_ghg_emissions": row["Total GHG Emissions"] if pd.notna(row["Total GHG Emissions"]) else None,
            "freshwater_consumption_l": row["Freshwater Comsumption (l)"] if pd.notna(row["Freshwater Comsumption (l)"]) else None,
            "acidification_kg_so2eq": row["Acidification (kg SO2eq)"] if pd.notna(row["Acidification (kg SO2eq)"]) else None,
            "eutrophication_kg_po43eq": row["Eutrophication (kg PO43-eq)"] if pd.notna(row["Eutrophication (kg PO43-eq)"]) else None,
        }

    group_series = df_lca["Food Group"].astype(str).str.strip()
    key_lower = food_group.strip().lower()
    matches = df_lca[group_series.str.lower() == key_lower]
    if matches.empty:
        matches = df_lca[group_series.str.lower().str.contains(key_lower, regex=False, na=False)]
    if matches.empty:
        return {
            "error": f"No food group found matching '{food_group}'.",
            "available_food_groups": sorted(group_series.unique().tolist()),
        }
    return {
        "food_group": matches["Food Group"].iloc[0],
        "items": [
            {
                "food_item": row["Item Cd"],
                "total_ghg_emissions": row["Total GHG Emissions"] if pd.notna(row["Total GHG Emissions"]) else None,
                "freshwater_consumption_l": row["Freshwater Comsumption (l)"] if pd.notna(row["Freshwater Comsumption (l)"]) else None,
                "acidification_kg_so2eq": row["Acidification (kg SO2eq)"] if pd.notna(row["Acidification (kg SO2eq)"]) else None,
                "eutrophication_kg_po43eq": row["Eutrophication (kg PO43-eq)"] if pd.notna(row["Eutrophication (kg PO43-eq)"]) else None,
            }
            for _, row in matches.iterrows()
        ],
    }


_ACCESSIBILITY_DATA = {
    "addis": {
        "df": accessibility_zonal_stats_addis,
        "population_options": accessibility_population_options_addis,
        "offer_options": accessibility_offer_options_addis,
    },
    "hanoi": {
        "df": accessibility_zonal_stats_hanoi,
        "population_options": accessibility_population_options_hanoi,
        "offer_options": accessibility_offer_options_hanoi,
    },
}

_TIME_MINUTES_TO_SECONDS = {5: 300, 10: 600, 15: 900}

# Above this many regions, returning every value would be a large, mostly
# unreadable dump (Hanoi has ~126 communes vs Addis's 10 districts) and risks
# eating into the free-tier token budget for no benefit - summarize instead.
_MAX_REGIONS_TO_LIST = 20


def _resolve_category(value, options, label):
    value_lower = value.strip().lower()
    for opt in options:
        if opt["value"].lower() == value_lower:
            return opt["value"], None
    for opt in options:
        if value_lower in opt["label"].lower() or value_lower in opt["value"].lower():
            return opt["value"], None
    return None, {"error": f"No {label} found matching '{value}'.", f"available_{label}_options": options}


def get_food_accessibility_value(city, population_category, offer_category, region=None, mode="walk", time_minutes=15):
    """Look up what fraction of a population group can reach a type of food
    outlet within a travel time, by district/commune. Covers both cities.
    Needs BOTH population_category and offer_category; mode and time_minutes
    default sensibly (walk, 15 minutes) if not given.
    """
    city = city.strip().lower()
    spec = _ACCESSIBILITY_DATA.get(city)
    if spec is None or spec["df"].empty:
        return {"error": f"No food accessibility data available for {city}."}

    df = spec["df"]

    pop_value, pop_error = _resolve_category(population_category, spec["population_options"], "population_category")
    if pop_error:
        return pop_error
    offer_value, offer_error = _resolve_category(offer_category, spec["offer_options"], "offer_category")
    if offer_error:
        return offer_error

    mode = (mode or "walk").strip().lower()
    valid_modes = set(df["mode"].dropna().unique())
    if mode not in valid_modes:
        mode = "walk" if "walk" in valid_modes else next(iter(valid_modes), mode)

    time_seconds = _TIME_MINUTES_TO_SECONDS.get(int(time_minutes), 900)

    matches = df[
        (df["pop_cat"] == pop_value)
        & (df["offer_cat"] == offer_value)
        & (df["mode"] == mode)
        & (df["time"] == time_seconds)
    ]
    if matches.empty:
        return {
            "error": (
                f"No data for population='{pop_value}', offer='{offer_value}', "
                f"mode='{mode}', time={time_minutes}min in {city}."
            )
        }

    row = matches.iloc[0]
    subcity_cols = [c for c in df.columns if c not in {"index", "pop_cat", "offer_cat", "mode", "time"}]

    base = {
        "city": city, "population_category": pop_value, "offer_category": offer_value,
        "mode": mode, "time_minutes": time_minutes,
    }

    if region:
        region_col = next((c for c in subcity_cols if c.strip().lower() == region.strip().lower()), None)
        if region_col is None:
            return {**base, "error": f"No region found matching '{region}'.", "available_regions": subcity_cols}
        value = row[region_col]
        return {**base, "region": region_col, "value_percent": value if pd.notna(value) else None}

    values = {col: (row[col] if pd.notna(row[col]) else None) for col in subcity_cols}
    if len(subcity_cols) <= _MAX_REGIONS_TO_LIST:
        return {**base, "values_by_region": [{"region": k, "value_percent": v} for k, v in values.items()]}

    numeric_values = {k: v for k, v in values.items() if v is not None}
    if not numeric_values:
        return {**base, "note": "No numeric data across any region for this combination."}
    highest = max(numeric_values, key=numeric_values.get)
    lowest = min(numeric_values, key=numeric_values.get)
    return {
        **base,
        "region_count": len(subcity_cols),
        "note": f"{len(subcity_cols)} regions available - summarized here; pass a specific 'region' for one exact value.",
        "average_percent": sum(numeric_values.values()) / len(numeric_values),
        "highest": {"region": highest, "value_percent": numeric_values[highest]},
        "lowest": {"region": lowest, "value_percent": numeric_values[lowest]},
    }


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "describe_indicator",
            "description": (
                "Get the description, pillar, and sub-domain of a named dashboard "
                "indicator. Use when the user asks what an indicator means or where "
                "to find it."
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
                "Look up value(s) of a Multidimensional Poverty Index (MPI) "
                "indicator (both cities), or - Hanoi only - a food-affordability "
                "or nutrition/diet indicator. MPI has one value per district/"
                "commune and no year (use 'region', omit 'year'). Affordability "
                "and nutrition are yearly and only split by 'Hanoi' vs 'Vietnam' "
                "(use 'year' and/or region='Hanoi'/'Vietnam', not a district). "
                "Use when the user asks for a specific number from one of these "
                "three datasets. For other topics (GRDP, population, literacy, "
                "diesel price, etc.) use get_subdomain_indicator_value instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "enum": ["addis", "hanoi"]},
                    "indicator_key": {
                        "type": "string",
                        "description": "e.g. 'Multidimensional Poverty Index', 'Cooking fuel', 'Housing', 'Sanitation', 'foodExp_totalExp', 'Stunting in children under 5 years'",
                    },
                    "region": {
                        "type": ["string", "null"],
                        "description": "Optional district/commune name (MPI) or 'Hanoi'/'Vietnam' (affordability/nutrition) to filter to one region. Omit or use null if not filtering.",
                    },
                    "year": {
                        "type": ["integer", "null"],
                        "description": "Optional year - only applies to affordability/nutrition (ignored for MPI, which has no year). Omit or use null if not filtering.",
                    },
                },
                "required": ["city", "indicator_key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_subdomain_indicator_value",
            "description": (
                "Look up value(s) of a per-subdomain time-series indicator - "
                "covers topics like GRDP growth, population, literacy rate, "
                "trade/self-sufficiency rates, diesel price, food CPI, market "
                "counts, poverty rate, social security coverage, and similar - "
                "distinct from get_indicator_value's three datasets (MPI, "
                "affordability, nutrition). Hanoi only for now; no equivalent "
                "data exists for Addis yet. Without 'year', returns the latest "
                "and earliest available points (for a quick trend read); pass "
                "'year' to get every data point in that specific year."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "enum": ["addis", "hanoi"]},
                    "indicator_name": {
                        "type": "string",
                        "description": "e.g. 'Gross Regional Domestic Product (GRDP) growth', 'Population', 'Diesel price', 'Poverty rate'",
                    },
                    "year": {
                        "type": ["integer", "null"],
                        "description": "Optional year to get all data points (e.g. all quarters/months) within. Omit or use null for just the latest/earliest points.",
                    },
                },
                "required": ["city", "indicator_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_food_item_environmental_impact",
            "description": (
                "Look up a food item's environmental footprint - total GHG "
                "emissions, freshwater consumption, acidification, and "
                "eutrophication. Addis-only, keyed by food item/food group, "
                "not by region; no equivalent data exists for Hanoi yet. If "
                "the user references a food group (e.g. 'Cereals & Grains') "
                "rather than one specific item, pass food_group and "
                "summarize the returned set."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "food_item": {
                        "type": ["string", "null"],
                        "description": "e.g. 'Teff', 'Maize (Corn)'. Omit or use null if using food_group instead.",
                    },
                    "food_group": {
                        "type": ["string", "null"],
                        "description": "e.g. 'Cereals & Grains'. Omit or use null if using food_item instead.",
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
                "Look up what percentage of a population group can reach a "
                "type of food outlet within a travel time, by district/"
                "commune. Covers both cities. Needs BOTH population_category "
                "and offer_category to return anything; mode and "
                "time_minutes default sensibly (walk, 15 minutes) if not "
                "given, so don't withhold an answer just because those two "
                "weren't specified. Omit region to get every region at once "
                "(or a summary, if there are many)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "enum": ["addis", "hanoi"]},
                    "population_category": {
                        "type": "string",
                        "description": "e.g. 'total' (Addis only), 'men', 'women', 'youth', 'children_u5', 'women_rep', 'elderly'",
                    },
                    "offer_category": {
                        "type": "string",
                        "description": "e.g. 'amenity_fast_food', 'amenity_marketplace', 'shop_bakery', 'beverages'",
                    },
                    "region": {
                        "type": ["string", "null"],
                        "description": "Optional district/commune name to filter to one region. Omit or use null for all regions / a summary.",
                    },
                    "mode": {
                        "type": ["string", "null"],
                        "description": "Travel mode: 'walk', 'drive', or 'multimodal'. Defaults to 'walk' if omitted or invalid.",
                    },
                    "time_minutes": {
                        "type": ["integer", "null"],
                        "description": "Travel time threshold in minutes: 5, 10, or 15. Defaults to 15 if omitted.",
                    },
                },
                "required": ["city", "population_category", "offer_category"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "describe_indicator": describe_indicator,
    "list_available_indicators": list_available_indicators,
    "get_indicator_value": get_indicator_value,
    "get_subdomain_indicator_value": get_subdomain_indicator_value,
    "get_food_item_environmental_impact": get_food_item_environmental_impact,
    "get_food_accessibility_value": get_food_accessibility_value,
}
