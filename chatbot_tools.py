"""
Tool functions exposed to the dashboard assistant chatbot.

Each tool is deliberately narrow: it returns only the specific fields asked
for, never a raw dataframe dump. All data comes from data_access.py (a
clean, dedicated module) - not from app.py's internals.
"""

from data_access import atlas_records, is_indicator_available_for_city, df_mpi, df_mpi_hanoi

_REGION_COLUMN = {"addis": "Dist_Name", "hanoi": "Name"}


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


def get_indicator_value(city, indicator_key, region=None):
    """Look up specific Multidimensional Poverty Index (MPI) value(s) for a city/region.

    The atlas's conceptual indicator names (e.g. "Living standard dimension")
    don't always match the MPI dataset's literal variable names (e.g.
    "Multidimensional Poverty Index", "Housing", "Sanitation") - so an exact
    match is tried first, then a substring match, before giving up. On total
    failure, the real available variable names are returned so the caller
    (the model) can retry with a valid one instead of concluding no data
    exists at all.
    """
    city = city.strip().lower()
    df = df_mpi_hanoi if city == "hanoi" else df_mpi
    region_col = _REGION_COLUMN.get(city, "Dist_Name")
    key_lower = indicator_key.strip().lower()

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

    if matches.empty:
        available = sorted(variable_series.unique().tolist())
        detail = f" region '{region}'" if region else ""
        return {
            "error": f"No data found for indicator '{indicator_key}' in {city}{detail}.",
            "available_indicator_keys_for_this_city": available,
        }

    return {
        "city": city,
        "indicator": resolved_key,
        "values": [
            {"region": row[region_col], "value": row["Value"]}
            for _, row in matches.iterrows()
        ],
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
                "Look up the actual current value(s) of a Multidimensional Poverty "
                "Index (MPI) related indicator for a city, optionally for one specific "
                "district/commune. Use when the user asks for a specific number."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "enum": ["addis", "hanoi"]},
                    "indicator_key": {
                        "type": "string",
                        "description": "e.g. 'Multidimensional Poverty Index', 'Cooking fuel', 'Housing', 'Sanitation'",
                    },
                    "region": {
                        "type": ["string", "null"],
                        "description": "Optional district/commune name to filter to one region. Omit or use null if not filtering.",
                    },
                },
                "required": ["city", "indicator_key"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "describe_indicator": describe_indicator,
    "list_available_indicators": list_available_indicators,
    "get_indicator_value": get_indicator_value,
}
