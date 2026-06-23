"""
Shared UI components for EcoFoodSystems Dashboard
"""

import csv
import os
from io import StringIO

from dash import html, dcc
import dash_bootstrap_components as dbc
from config import brand_colors, sidebar_colors, hero_gradient

# ========================== Sidebar ==========================


_ATLAS_CSV_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "EcoFoodSystems_FCD_aligned.csv",
)

ATLAS_COLUMNS = [
    "FCD Primary Pillar",
    "FCD Sub-domain",
    "Indicator name",
]

_SIDEBAR_PILLARS = [
    {"key": "drivers", "label": "Drivers"},
    {"key": "food-supply-chains", "label": "Food Supply Chains"},
    {"key": "food-environments", "label": "Food Environments"},
    {"key": "individual-factors", "label": "Individual Factors"},
    {"key": "cross-cutting-issues", "label": "Cross-Cutting Issues"},
    {"key": "outcomes", "label": "Outcomes"},
]

_PRIMARY_LABEL_TO_KEY = {
    "drivers": "drivers",
    "food supply chains": "food-supply-chains",
    "food environments": "food-environments",
    "individual factors": "individual-factors",
    "cross-cutting issues": "cross-cutting-issues",
    "outcomes": "outcomes",
}

_TAB_BG_KEY_BY_ID = {
    "tab-1-stakeholders": "stakeholders",
    "tab-2-supply": "supply",
    "tab-3-sustainability": "sustainability",
    "tab-4-poverty": "poverty",
    "tab-5-labour": "labour",
    "tab-6-resilience": "resilience",
    "tab-7-food-environments": "food-environments",
    "tab-8-losses": "losses",
    "tab-9-policies": "policies",
    "tab-10-nutrition": "nutrition",
    "tab-11-footprints": "footprints",
    "tab-12-behaviour": "behaviour",
}


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


def _atlas_available_for_city(rec, selected_city):
    field = 'Available Hanoi' if selected_city == 'hanoi' else 'Available Addis'
    val = str(rec.get(field, '')).strip().lower()
    return val in {'1', 'true', 'yes', 'y'}


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


def _record_primary_pillar_key(rec):
    primary = str(rec.get('FCD Primary Pillar', '')).strip().lower().replace('&', 'and')
    primary = ' '.join(primary.split())
    mapped = _PRIMARY_LABEL_TO_KEY.get(primary)
    if mapped:
        return mapped

    fallback = _record_pillar_key(rec)
    fallback_map = {
        'diets': 'food-environments',
        'environment': 'drivers',
        'livelihoods': 'individual-factors',
        'governance': 'cross-cutting-issues',
        'resilience': 'outcomes',
    }
    return fallback_map.get(fallback)


def _record_target_tab(rec):
    domain = (rec.get('Domain / Sub-theme') or '').lower()
    name = (rec.get('Indicator name') or '').lower()
    text = f"{domain} {name}"

    if 'stakeholder' in text:
        return 'tab-1-stakeholders', None
    if 'flow' in text or 'supply chain' in text:
        return 'tab-2-supply', None

    if 'resilience' in text:
        if 'land-use & land-cover distribution' in name:
            return 'tab-6-resilience', 'Land-use & Land-cover'
        if any(k in name for k in ['agricultural climate resilience indicator', 'water storage anomalies', 'natural disasters database']):
            return 'tab-6-resilience', 'Biophysical shocks'
        if 'food price resilience indicator' in name:
            return 'tab-6-resilience', 'Socio-Economic Shocks'
        return 'tab-6-resilience', 'Resilience Indicator Trends'

    if 'food environments' in domain or 'afford' in text:
        return 'tab-7-food-environments', None
    if 'loss' in text or 'waste' in text:
        return 'tab-8-losses', None
    if 'policies' in text or 'governance' in text:
        return 'tab-9-policies', None
    if 'nutrition' in text or 'health' in text or 'food safety' in text:
        return 'tab-10-nutrition', None
    if 'footprint' in text or 'life cycle' in text:
        return 'tab-11-footprints', None
    if 'behaviour' in text or 'behavior' in text or 'chatbot' in text or 'game' in text:
        return 'tab-12-behaviour', None
    if 'sustainability' in text:
        return 'tab-3-sustainability', None
    if 'labour' in text or 'green job' in text or 'skills' in text:
        return 'tab-5-labour', None
    if 'poverty' in text:
        return 'tab-4-poverty', None

    return 'tab-home', None


def make_sidebar(selected_city='hanoi', dark=False):
    import hanoi_config
    import addis_config
    tab_backgrounds = hanoi_config.TAB_BACKGROUNDS if selected_city == 'hanoi' else addis_config.TAB_BACKGROUNDS

    home_button = html.A([
                html.Img(
                    src="/assets/logos/home_button.svg",
                    alt="Home",
                    style={
                        "height": "28px",
                        "width": "28px",
                        "verticalAlign": "middle",
                        "marginRight": "8px",
                        "marginBottom": "3px"
                    }
                ),
                html.Span("Home", style={
                    "verticalAlign": "middle",
                    "fontWeight": "bold",
                    "fontSize": "1.08em"
                })
            ], href="/", className="dash-sidebar-home-btn")

    atlas_records = _load_indicator_atlas_records(_ATLAS_CSV_PATH)

    pillar_subdomain_items = {p['key']: {} for p in _SIDEBAR_PILLARS}
    seen_by_pillar = {p['key']: set() for p in _SIDEBAR_PILLARS}

    for idx, rec in enumerate(atlas_records):
        pillar_key = _record_primary_pillar_key(rec)
        if pillar_key not in pillar_subdomain_items:
            continue

        subdomain = (rec.get('FCD Sub-domain') or '').strip() or 'Other'

        indicator_name = (rec.get('Indicator name') or '').strip()
        if not indicator_name:
            continue

        dedupe_key = indicator_name.lower()
        if dedupe_key in seen_by_pillar[pillar_key]:
            continue
        seen_by_pillar[pillar_key].add(dedupe_key)

        target_tab, target_subview = _record_target_tab(rec)
        available = _atlas_available_for_city(rec, selected_city)

        # Tab-level availability from city config also gates indicator action buttons.
        tab_bg_key = _TAB_BG_KEY_BY_ID.get(target_tab)
        tab_is_coming_soon = tab_backgrounds.get(tab_bg_key or '', '#ffffff') == '#f4f4f4'
        is_disabled = (not available) or tab_is_coming_soon

        indicator_button = (
            html.Button(
                [
                    html.Span(indicator_name),
                    html.Span("Coming soon", className="dash-landing-btn-coming-soon") if is_disabled else None,
                ],
                id={
                    'type': 'sidebar-indicator-btn',
                    'target': target_tab,
                    'subview': target_subview or '',
                    'city': selected_city,
                    'index': idx,
                },
                n_clicks=0,
                className='dash-sidebar-subtab-btn',
                disabled=is_disabled,
                style={
                    'opacity': 0.45 if is_disabled else 1,
                    'cursor': 'not-allowed' if is_disabled else 'pointer',
                },
            )
        )
        pillar_subdomain_items[pillar_key].setdefault(subdomain, []).append(indicator_button)

    pillar_sections = []
    for pillar in _SIDEBAR_PILLARS:
        subdomain_groups = pillar_subdomain_items.get(pillar['key'], {})
        subdomain_sections = []
        for subdomain_name, subdomain_buttons in subdomain_groups.items():
            subdomain_sections.append(
                html.Details(
                    [
                        html.Summary(subdomain_name, className='dash-sidebar-subdomain-toggle'),
                        html.Div(subdomain_buttons, className='dash-sidebar-subtab-group'),
                    ],
                    className='dash-sidebar-subdomain-card'
                )
            )

        if not subdomain_sections:
            subdomain_sections = [
                html.Div('No indicators available yet for this city.', className='dash-sidebar-empty-text')
            ]

        pillar_sections.append(
            html.Div([
                html.Button(
                    [
                        html.Span(pillar["label"]),
                    ],
                    id=f"pillar-toggle-{pillar['key']}",
                    n_clicks=0,
                    className="dash-sidebar-pillar-toggle",
                ),
                dbc.Collapse(
                    html.Div(subdomain_sections, className="dash-sidebar-subdomain-group"),
                    id=f"pillar-collapse-{pillar['key']}",
                    is_open=False,
                ),
            ], className="dash-sidebar-pillar-card")
        )

    bg_color = "#1d574f" if dark else "#f0f6e5"
    card_class = "dash-sidebar-card dash-sidebar-card--dark" if dark else "dash-sidebar-card"

    return dbc.Card([
        html.Div(home_button, className="dash-sidebar-home-wrap"),
        html.Div(pillar_sections, className="dash-sidebar-pillar-list"),
    ], className=card_class, style={
        #"boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
        "borderRadius": "0px",
        "padding": "10px",
        "height": "100%",
        "width": "100%",
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "flex-start",
        "overflowY": "auto",
        "backgroundColor": bg_color,
    })


sidebar_hanoi = make_sidebar('hanoi', dark=True)
sidebar_addis = make_sidebar('addis', dark=True)
sidebar_addis_vendor = make_sidebar('addis', dark=True)
sidebar = sidebar_hanoi  # backward-compat for app.py import


# ========================== City Selector ==========================

def city_selector(selected_city='addis', visible=True):
    """
    City selector dropdown component.
    Must be included in all layouts for callbacks to work properly.
    Set visible=False to hide it on tab pages.
    """
    return html.Div([
        # Indicator Atlas button
        html.Div([
            dbc.Button(
                "Indicator Atlas",
                id='atlas-top-button',
                color='danger',
                n_clicks=0,
                style={
                    "fontSize": "1.1em",
                    "fontWeight": "bold",
                    "borderRadius": "10px",
                    "border": "none",
                    "color": hero_gradient['0%'],
                    "backgroundColor": brand_colors['Mid green'],
                    "padding": "12px 20px",
                    "boxShadow": "0 4px 10px rgba(0,0,0,0.12)",
                    "minWidth": "160px",
                }
            )
        ], style={
            "position": "absolute",
            "left": "1%",
            "top": "70%",
            "transform": "translateY(-50%)",
            "display": "flex" if visible else "none",
            "alignItems": "center",
        }),

        # Dropdown selector
        html.Div([
            html.Label("City:", style={
                "color": hero_gradient['0%'],
                "fontSize": "0.9em",
                "marginRight": "8px",
                "fontWeight": "600"
            }),
            dcc.Dropdown(
                id='city-selector',
                options=[
                    {'label': 'Addis Ababa', 'value': 'addis'},
                    {'label': 'Hanoi', 'value': 'hanoi'}
                ],
                value=selected_city,
                clearable=False,
                searchable=False,
                style={
                    "width": "200px",
                    "fontSize": "0.95em"
                }
            )
        ], style={
            "position": "absolute",
            "right": "2%",
            "top": "60%",
            "transform": "translateY(-50%)",
            "display": "flex" if visible else "none",
            "alignItems": "center",
            "gap": "3px"
        })
    ])


# ========================== Footer ==========================

footer = html.Footer([
    html.Div([
        html.Img(src="/assets/logos/EcoFoodSystems.svg", style={'height': '45px', 'margin': '0 30px'}),
        html.Img(src="/assets/logos/WUR.png", style={'height': '50px', 'margin': '0px 30px'}),
        html.Img(src="/assets/logos/DeSIRA.png", style={'height': '50px', 'margin': '0 30px'}),
        html.Img(src="/assets/logos/IFAD.png", style={'height': '50px', 'margin': '0 30px'}),
        html.Img(src="/assets/logos/Rikolto.png", style={'height': '30px', 'margin': '0 30px'}),
        html.Img(src="/assets/logos/RyanInstitute.png", style={'height': '60px', 'margin': '0 30px'})
    ], style={
        "display": "flex",
        "justifyContent": "center",
        "alignItems": "flex-end",
        "margin": "20px 0px",
    })
])
