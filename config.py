"""
Shared configuration, styles, and constants for EcoFoodSystems Dashboard
"""

# ========================== Brand Colors ==========================

brand_colors = {
    'Black': '#333333',
    "Brown": "#313715",
    "Red": "#A80050",
    "Dark green": "#939f5c",
    "Mid green": "#bbce8a",
    "Light green": "#E8F0DA",
    "White": "#ffffff"
}

# ========================== Color Palettes ==========================

green_gradient = [
    "#095d40",
    "#206044",
    "#3a6649",
    "#547d5b",
    "#6f946d",
    "#8aa97f",
    "#a5be91",
    "#b8d099",
    "#c1d88e",
    "#d1e7a8"
]

greens_pie_palette = [
    brand_colors['Light green'],   # "#E8F0DA"
    brand_colors['Mid green'],     # "#bbce8a"
    brand_colors['Dark green'],    # "#939f5c"
    "#b7c49a",                     # lighter tint of Dark green
    "#d6e5b8",                     # lighter tint of Mid green
    "#e3f6d5",                     # very light green
    "#c1d88e",                     # soft khaki-green
    "#d1e7a8",                     # pastel green
    "#aabf7e",                     # olive green
    "#8aa97f",                     # muted green
]

reds_pie_palette = [
    "#a80050",   # main brand red
    "#84003d",   # deep accent red
    "#C97A9A",   # soft pink
    "#E07A5F",   # warm accent
    "#F2D16B",   # harvest yellow (for contrast)
    "#F5F5F5",   # neutral light
    "#7B5E34",   # earth brown
    "#C97A9A",   # repeat pink
    "#E07A5F",   # repeat accent
    "#F2D16B"    # repeat yellow
]

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

# ========================== Dashboard Styles ==========================

tabs_style = {
    "backgroundColor": brand_colors['Mid green'],
    "color": brand_colors['Brown'],
    "width": "100%",
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

kpi_card_style = {
    "textAlign": "center",
    "backgroundColor": brand_colors['White'],
    "color": brand_colors['Brown'],
    "font-weight": "bold",
    "border-radius": "8px",
    "padding": "10px",
    "margin-bottom": "10px",
    "flexDirection": "column",
    "border": "2px solid " + brand_colors['White'],
}

kpi_card_style_2 = {
    "textAlign": "center",
    "backgroundColor": brand_colors['White'],
    "borderRadius": "12px",
    "boxShadow": "0 4px 16px rgba(0,0,0,0.10)",
    "padding": "clamp(4px, 3vw, 12px)",
    "padding": "6px",
    "marginBottom": "12px",
    "width": "100%",
}

header_style = {
    "color": brand_colors['Brown'],
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
    "padding": "20px",
    "margin-bottom": "15px"
}

# ========================== Food Environment Config ==========================

# Color schemes for choropleth maps
green_scale = ['#e3f6d5', '#c1d88e', '#a5be91', '#6f946d', '#3a6649']
red_scale = ['#fee5d9', '#fcbba1', '#fc9272', '#fb6a4a', '#de2d26']
grey_scale = ['#f7f7f7', '#d9d9d9', '#bdbdbd', '#969696', '#636363']

# Food environment metrics and labels
cols_food_env = [
    'density_healthyout', 'density_unhealthyout', 'density_mixoutlets',
    'ratio_obesogenic', 'pct_access_healthy', 'ptc_access_unhealthy'
]

data_labels_food_env = [
    'Healthy Outlet Density', 'Unhealthy Outlet Density', 'Mixed Outlet Density',
    'Obesogenic Ratio', 'Percent Access to Healthy Food', 'Percent Access to Unhealthy Food'
]

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

# ========================== Tab Labels ==========================

tabs = [
    'Food Systems Stakeholders',                 # Populated
    'Food Flows, Supply & Value Chains',         # Populated
    'Sustainability Metrics & Indicators',       # Currently empty
    'Multidimensional Poverty',                  # Populated
    'Resilience to Food System Shocks',          # In progress
    'Dietary Mapping & Affordability',           # Semi-Populated (In development)
    'Food Losses & Waste',                       # Currently empty
    'Food System Policies',                      # Currently empty
    'Health & Nutrition',                        # Populated
    'Environmental Footprints of Food & Diets',  # Currently empty
    'Behaviour Change Tool (AI Chatbot & Game)'  # Currently empty (In development)
]
