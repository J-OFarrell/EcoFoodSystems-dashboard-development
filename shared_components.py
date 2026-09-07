"""
Shared UI components for EcoFoodSystems Dashboard
"""

import re

from dash import html, dcc
import dash_bootstrap_components as dbc
from config import brand_colors
from data_access import (
    is_indicator_available_for_city as _atlas_available_for_city,
    atlas_records,
)


# ========================== Sidebar ==========================

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


def _record_primary_pillar_key(rec):
    """Map a record's 'FCD Primary Pillar' cell to its sidebar section key."""
    primary = str(rec.get('FCD Primary Pillar', '')).strip().lower().replace('&', 'and')
    primary = ' '.join(primary.split())
    return _PRIMARY_LABEL_TO_KEY.get(primary)


# Maps the CSV's 'FCD Sub-domain' text to the sub-domain keys used by
# app.py's _SUBDOMAIN_GROUPS / _resolve_subdomain_layout (the pillar-page
# sub-domain switcher). Keys with typos (e.g. 'nutrional-status',
# 'retail-markerting') intentionally match the existing app.py keys.
_CSV_SUBDOMAIN_TO_KEY = {
    "income growth and distribution": "income-growth-distribution",
    "environment and climate change": "environment-climate-change",
    "socio-cultural context": "socio-cultural-context",
    "population growth and migration": "population-growth-migration",
    "globalization and trade": "globalization-trade",
    "urbanization": "urbanization",
    "storage and distribution": "storage-distrbution",
    "processing and packaging": "processing-packing",
    "production systems and input supply": "production-systems-input-supply",
    "retail and marketing": "retail-markerting",
    "food affordability": "food-affordability",
    "vendor properties": "vendor-properties",
    "food safety": "food-safety",
    "food messaging": "food-messaging",
    "economic": "economic",
    "behavioral": "behavioral",
    "resilience": "resilience",
    "governance": "governance",
    "nutritional status": "nutrional-status",
    "noncommunicable diseases": "noncommunicable-diseases",
    "livelihoods, poverty, and equity": "livelihoods-poverty-equity",
    "environmental impacts": "environmental-impacts",
    "food security": "food-security",
    "dietary intake": "dietary-intake",
}


def _slugify_subdomain(label):
    """Fallback for any 'FCD Sub-domain' value not yet in _CSV_SUBDOMAIN_TO_KEY."""
    slug = re.sub(r"[^a-z0-9]+", "-", label.strip().lower()).strip("-")
    return slug or "other"


def _record_subdomain_key(rec):
    """Look up which pillar-page sub-domain an indicator belongs to."""
    label = (rec.get('FCD Sub-domain') or '').strip().lower()
    return _CSV_SUBDOMAIN_TO_KEY.get(label) or _slugify_subdomain(label)


def _build_pillar_groups(selected_city):
    """Group atlas records by sidebar pillar -> sub-domain, deduped by indicator name.

    Availability (greyed-out "Coming soon" state) comes directly from the
    CSV's 'Available Hanoi' / 'Available Addis' columns via
    `is_indicator_available_for_city` - nothing else gates it.
    """
    groups = {p['key']: {} for p in _SIDEBAR_PILLARS}
    seen = {p['key']: set() for p in _SIDEBAR_PILLARS}

    for idx, rec in enumerate(atlas_records):
        pillar_key = _record_primary_pillar_key(rec)
        if pillar_key not in groups:
            continue

        indicator_name = (rec.get('Indicator name') or '').strip()
        if not indicator_name:
            continue

        dedupe_key = indicator_name.lower()
        if dedupe_key in seen[pillar_key]:
            continue
        seen[pillar_key].add(dedupe_key)

        subdomain = (rec.get('FCD Sub-domain') or '').strip() or 'Other'
        groups[pillar_key].setdefault(subdomain, []).append((idx, rec, indicator_name))

    return groups


def _make_indicator_button(idx, rec, indicator_name, selected_city):
    available = _atlas_available_for_city(rec, selected_city)
    subdomain_key = _record_subdomain_key(rec)

    return html.Button(
        [
            html.Span(indicator_name),
            html.Span("Coming soon", className="dash-landing-btn-coming-soon") if not available else None,
        ],
        id={
            'type': 'sidebar-indicator-btn',
            'target': 'subdomain',
            'subview': subdomain_key,
            'city': selected_city,
            'index': idx,
        },
        n_clicks=0,
        className='dash-sidebar-subtab-btn',
        disabled=not available,
        style={
            'opacity': 0.45 if not available else 1,
            'cursor': 'not-allowed' if not available else 'pointer',
        },
    )


def make_sidebar(selected_city='hanoi', dark=False):
    home_button = html.Button([
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
            ], id={'type': 'sidebar-home-btn', 'city': selected_city, 'index': 0}, n_clicks=0, className="dash-sidebar-home-btn")

    pillar_groups = _build_pillar_groups(selected_city)

    pillar_sections = []
    for pillar in _SIDEBAR_PILLARS:
        subdomain_groups = pillar_groups.get(pillar['key'], {})
        subdomain_sections = []
        for subdomain_name, indicators in subdomain_groups.items():
            buttons = [
                _make_indicator_button(idx, rec, indicator_name, selected_city)
                for idx, rec, indicator_name in indicators
            ]
            subdomain_sections.append(
                html.Details(
                    [
                        html.Summary(subdomain_name, className='dash-sidebar-subdomain-toggle'),
                        html.Div(buttons, className='dash-sidebar-subtab-group'),
                    ],
                    className='dash-sidebar-subdomain-card'
                )
            )

        if not subdomain_sections:
            subdomain_sections = [
                html.Div('No indicators available yet for this city.', className='dash-sidebar-empty-text')
            ]

        pillar_sections.append(
            html.Details(
                [
                    html.Summary(pillar["label"], className='dash-sidebar-pillar-toggle'),
                    html.Div(subdomain_sections, className="dash-sidebar-subdomain-group"),
                ],
                className='dash-sidebar-pillar-card'
            )
        )

    bg_color = "#1d574f" if dark else "#f0f6e5"
    card_class = "dash-sidebar-card dash-sidebar-card--dark" if dark else "dash-sidebar-card"

    return dbc.Card([
        html.Div(home_button, className="dash-sidebar-home-wrap"),
        html.Div(pillar_sections, className="dash-sidebar-pillar-list"),
    ], className=card_class, style={
        #"boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
        "borderRadius": "12px",
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

def city_selector(selected_city='hanoi', visible=True):
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
                    "color": brand_colors['Brown'],
                    "backgroundColor": brand_colors['Mid green'],
                    "padding": "12px 20px",
                    "boxShadow": "0 4px 10px rgba(0,0,0,0.12)",
                    "minWidth": "160px",
                }
            )
        ], style={
            "position": "absolute",
            "left": "2%",
            "top": "50%",
            "transform": "translateY(-50%)",
            "display": "flex" if visible else "none",
            "alignItems": "center",
        }),

        # Dropdown selector
        html.Div([
            html.Label("City:", style={
                "color": brand_colors['Brown'],
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
            "top": "50%",
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
