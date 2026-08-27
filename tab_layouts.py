"""
Pure layout-builder functions for the dashboard: the indicator atlas, the
home/landing page (pillar cards, sub-domain rows), and small KPI card
builders. No @app.callback functions live here - those stay in app.py, which
imports what it needs from this module.

_resolve_subdomain_layout is a deliberate exception - it's a router function
that otherwise belongs here alongside _render_subdomain_hub_layout, but it
calls _get_resilience_context(), which still lives in app.py (not every
cache-style helper has been split out yet - see cache_helpers.py's docstring).
Moving it here would recreate exactly the app.py <-> tab_layouts.py circular
import this refactor exists to avoid, so it stays in app.py instead.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objects as go
import plotly.colors as pc

import addis_config
import hanoi_config
from config import brand_colors
from data_access import atlas_records
from shared_components import city_selector, footer


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
