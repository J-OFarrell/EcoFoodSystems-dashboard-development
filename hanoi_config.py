"""
Hà Nội city-specific configuration
"""

CITY_NAME = "Hà Nội"
BACKGROUND_IMAGE = "/assets/photos/hanoi_header.png"

# Tab background colors for landing page
white_tab_bg = "rgba(255, 255, 255, 0.7)"
grey_tab_bg = "rgba(173, 181, 189, 0.7)"

TAB_BACKGROUNDS = {
    "stakeholders": white_tab_bg, 
    "supply": white_tab_bg,
    "sustainability": grey_tab_bg, 
    "poverty": white_tab_bg,
    "labour": grey_tab_bg,
    "resilience": grey_tab_bg, 
    "affordability": white_tab_bg, 
    "losses": grey_tab_bg,
    "policies": grey_tab_bg, 
    "nutrition": white_tab_bg, 
    "footprints": grey_tab_bg, 
    "behaviour": grey_tab_bg
}
