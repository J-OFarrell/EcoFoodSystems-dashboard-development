# Quick Reference: Naming Schema for New Data Files

Keep this handy when adding new indicators to the dashboard.

## Naming Formula

```
{city}_{pillar_short}_{domain_short}_{data_type}_{variation}.{extension}
```

## Quick Lookup Tables

### Pillar Abbreviations (Choose one)

| Pillar | Code | When To Use |
|--------|------|------------|
| Diets, Nutrition & Health | `dnh` | Food/nutrition data, health outcomes, diet patterns |
| Livelihoods, Poverty & Equity | `lpe` | MPI, poverty, income, employment data |
| Food System Structure | `fss` | Stakeholders, supply chains, infrastructure |
| Food Policies & Governance | `fpg` | Policies, regulations, governance frameworks |
| Environment & Sustainability | `env` | Climate, LCA, resilience, environmental metrics |

### Domain Abbreviations (Choose one)

| Domain | Code | Pillar | Example Files |
|--------|------|--------|----------------|
| Nutrition | `nut` | dnh | health indicators, stunting, wasting |
| Food Environments | `fenv` | dnh | diet env mapping, outlet accessibility |
| Affordability | `afford` | dnh | food prices, cost of living |
| Multidimensional Poverty Index | `mpi` | lpe | poverty dimensions, deprivation |
| Stakeholders | `stk` | fss | stakeholder database, organizations |
| Supply Chain | `supply` | fss | supply flows, distribution chains |
| Policy | `pol` | fpg | policy databases, regulations |
| Life Cycle Assessment | `lca` | env | carbon footprint, environmental impact |
| Climate & Resilience | `clim` | env | climate variables, disaster events, drought |
| OSM Infrastructure | `osm` | env | water systems, roads, connectivity |

### Data Type Keywords

```
indicators      — Statistical indicators, metrics, or measurements
boundaries      — Geographic boundaries (geojson/shapefiles)
outlets         — Food venue point data (amenities, shops)
mapping         — Thematic mapping data with summaries
database        — Database extracts, reference tables
statistics      — Statistical summaries or aggregations
values          — Tabular values/attributes
flows           — Flow data (sankey, supply chains)
```

### Variation Keywords (Optional)

```
_long           — Long-format data (tidy format for plotting)
_cleaned        — Processed/cleaned version
_v1, _v2        — Version numbers
_quarterly      — Time-series aggregation
_regional       — Regional aggregation
_composite      — Composite indicator
```

### File Extensions

```
.csv            — Tabular data (for tables, charts, analysis)
.geojson        — Geographic data (for maps, spatial analysis)
.json           — Semi-structured data
.parquet        — Compressed tabular data (for large datasets)
```

---

## Example Naming Scenarios

### Scenario 1: New nutrition indicator for Addis
**What:** Monthly prevalence of anemia in children by district  
**Pillar:** Diets, Nutrition & Health → `dnh`  
**Domain:** Nutrition → `nut`  
**Data Type:** Indicators + boundaries  
**Files:**
- `addis_dnh_nut_anemia_prevalence.csv` (data table)
- `addis_dnh_nut_anemia_boundaries.geojson` (district boundaries with values)

### Scenario 2: Climate resilience indicator for Hanoi
**What:** Seasonal drought risk by commune  
**Pillar:** Environment & Sustainability → `env`  
**Domain:** Climate & Resilience → `clim`  
**Data Type:** Indicators + boundaries  
**Files:**
- `hanoi_env_clim_drought_risk_quarterly.csv` (quarterly values)
- `hanoi_env_clim_drought_risk_boundaries.geojson` (commune boundaries)

### Scenario 3: New food outlet type for Hanoi
**What:** Juice bars and smoothie shops  
**Pillar:** Diets, Nutrition & Health → `dnh`  
**Domain:** Food Environments → `fenv`  
**Data Type:** Outlet points  
**File:**
- `hanoi_dnh_fenv_outlet_shop_juices.geojson`

### Scenario 4: New policy database
**What:** Updated FAO-LEX policies for Addis  
**Pillar:** Food Policies & Governance → `fpg`  
**Domain:** Policy → `pol`  
**Data Type:** Database + version  
**Files:**
- `addis_fpg_pol_faolex_v2.csv` (new version with more entries)

---

## Directory Organization

Place new files in the existing city/domain folders:

```
assets/data/
├── addis/{domain}/
│   ├── addis_dnh_nut_*.csv/geojson
│   ├── addis_lpe_mpi_*.csv/geojson
│   ├── addis_fss_stk_*.csv
│   ├── addis_fpg_pol_*.csv
│   └── addis_env_*.csv/geojson
│
└── hanoi/{domain}/
    ├── hanoi_dnh_nut_*.csv/geojson
    ├── hanoi_dnh_afford_*.csv
    ├── hanoi_dnh_fenv_*.csv/geojson
    ├── hanoi_lpe_mpi_*.csv/geojson
    ├── hanoi_fss_stk_*.csv
    ├── hanoi_fss_supply_*.csv
    ├── hanoi_fpg_pol_*.csv
    └── hanoi/resilience/
        ├── hanoi_env_clim_*.csv/geojson
        ├── hanoi_env_lulc_*.csv
        └── osm_infrastructure/
            └── hanoi_env_osm_*.geojson
```

---

## Quick Checklist for New Files

- [ ] **Pillar identified:** Which pillar does this indicator belong to?
- [ ] **Domain identified:** Which domain/theme is it part of?
- [ ] **City prefix added:** `addis_` or `hanoi_`?
- [ ] **Descriptive name:** Is the file name self-explanatory?
- [ ] **Extension correct:** `.csv`, `.geojson`, `.json`, or `.parquet`?
- [ ] **Folder placed correctly:** In the appropriate domain subfolder?
- [ ] **Code updated:** Are file path references in Python code updated?

---

## Questions?

Refer back to the full schema: [DATA_NAMING_SCHEMA.md](DATA_NAMING_SCHEMA.md)
