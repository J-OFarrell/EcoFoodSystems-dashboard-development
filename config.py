"""
Shared configuration, styles, and constants for EcoFoodSystems Dashboard
"""

# ========================== Brand Colors ==========================


brand_colors = {
    'Black': '#333333',
    "Brown": "#313715",
    "Red": "#A80050",
    "Orange": "#D9A85C",
    "Teal": "#1d574f",
    "Light Teal": "#4e998c",
    "Dark green": "#939f5c",
    "Mid green": "#bbce8a",
    "Light green": "#E8F0DA",
    "White": "#ffffff"
}

sidebar_colors = {
'Background (light)' : '#ffffff',
'Text (light)' : '#313715',
'Hover (light)' : '#f4f7ee',
'Background (dark card)' : '#FFFFFF',
'Text (dark card)' : '#1d574f',
'Hover (dark card)' : '#E8F3F0'
}

hero_gradient = {
    "0%": "#0F2E2A",
    "50%": "#2A7A6F",
    "100%": "#5FA89A"
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

sub_header_style = {
    "color": brand_colors['Brown'],
    'fontWeight': 'bold',
    "margin": "0",
    'textAlign': 'center',
    "fontSize": "clamp(0.8em, 2vw, 1em)",
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

# ========================== Map / Chart Constants (from app.py) ==========================

# Esri World Imagery (satellite) tiles were considered for Vietnam maps while a
# compliant labelled basemap is sourced from Vietnamese partners; using the
# CartoDB light basemap instead for now.
_BASEMAP_TILE = [
    {
        "below": "traces",
        "sourcetype": "raster",
        "source": [
            "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
        ],
    }
]

REGION_COLOURS = {
    "Red River Delta": "#e63946",
    "Northeast": "#457b9d",
    "Northwest": "#2a9d8f",
    "North Central Coast": "#e9c46a",
    "South Central Coast": "#f4a261",
    "Central Highlands": "#264653",
    "Southeast": "#a8dadc",
    "Mekong Delta": "#06d6a0",
}

# Food environment metrics: household/demographic sub-city breakdown labels
sub_city_level_metrics = {
    'density_he': 'Healthy Outlet Density',
    'density_un': 'Unhealthy Outlet Density',
    'density_mi': 'Mixed Outlet Density',
    'ratio_obes': 'Obesogenic Ratio',
    'children_u5': 'Children (0-5 years)',
    'elderly': 'Elderly (60+ years)',
    'women_rep': 'Women of Reproductive Age (15-49 years)',
    'youth': 'Youth (15-24 years)',
    'men': 'Men',
    'women': 'Women',
    'total': 'Total',
}

cols_labels_hex_vars = {
    'children_u5': 'Children (0-5 years)',
    'elderly': 'Elderly (60+ years)',
    'women_rep': 'Women of Reproductive Age (15-49 years)',
    'youth': 'Youth (15-24 years)',
    'men': 'Men',
    'women': 'Women',
    'total': 'Total',
    'canopy_cover_pixels': 'Canopy Cover (m²)',
    'mean_lst': 'Average Land Surface Temperature (°C)',
}

# Food-environment choropleth palettes (Plotly scale names/definitions)
FOOD_ENV_NEG_SCALE = "YlOrRd"
FOOD_ENV_POS_SCALE = "YlGn"
FOOD_ENV_NEUTRAL_BONE_SCALE = [
    [0.00, "#fffdf8"],
    [0.25, "#f7f1e3"],
    [0.50, "#eadfc8"],
    [0.75, "#d8c9ab"],
    [1.00, "#c5b395"],
]
VIRIDIS_SCALE = "Viridis"
BLUES_SCALE = "Blues"
YLORBR_SCALE = "YlOrBr"
HOT_SCALE = "Hot"

# Maps each food-environment metric to its choropleth color scale. Named
# metric_color_scale (not metric_direction) to avoid colliding with this
# file's own metric_direction above, which is a different concept (bool
# "higher is better" flag) that happens to share app.py's original name.
metric_color_scale = {
    'density_he': FOOD_ENV_POS_SCALE,
    'density_un': FOOD_ENV_NEG_SCALE,
    'density_mi': FOOD_ENV_NEUTRAL_BONE_SCALE,
    'ratio_obes': FOOD_ENV_NEG_SCALE,
    'children_u5': YLORBR_SCALE,
    'elderly': YLORBR_SCALE,
    'women_rep': YLORBR_SCALE,
    'youth': YLORBR_SCALE,
    'men': YLORBR_SCALE,
    'women': YLORBR_SCALE,
    'total': YLORBR_SCALE,
    'canopy_cover_pixels': FOOD_ENV_POS_SCALE,
    'mean_lst': HOT_SCALE,
}

# ========================== Tab Labels ==========================

tabs = [
    'Food Systems Stakeholders',                 
    'Food Flows & Supply Chains',         
    'Sustainability Metrics',       
    'Multidimensional Poverty',                  
    'Resilience',          
    'Food Environments',           
    'Food Losses & Waste',                      
    'Policies & Regulation',                     
    'Nutrition & Health',                       
    'Environmental Footprints',  
    'Behaviour Change Tool (AI Chatbot & Game)'  
]
