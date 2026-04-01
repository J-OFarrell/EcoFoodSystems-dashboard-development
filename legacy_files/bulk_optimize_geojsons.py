from __future__ import annotations

import json
import shutil
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely

ROOT = Path(__file__).resolve().parents[1] / "assets" / "data"
BACKUP_ROOT = ROOT / "_geojson_legacy_backups_20260401"
REPORT_PATH = Path(__file__).resolve().parent / "reduced_geojson_tests" / "geojson_bulk_optimization_report.csv"


def optimize_geojson(path: Path) -> dict:
    rel = path.relative_to(ROOT).as_posix()
    before_bytes = path.stat().st_size

    backup_path = BACKUP_ROOT / rel
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    if not backup_path.exists():
        shutil.copy2(path, backup_path)

    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326", allow_override=True)

    working = gdf.copy()
    geom_types = set(working.geom_type.dropna().astype(str).unique()) if "geometry" in working else set()
    has_precision = hasattr(shapely, "set_precision") and not working.empty and bool(geom_types)

    if has_precision:
        try:
            metric_crs = working.estimate_utm_crs() if working.crs and working.crs.is_geographic else working.crs
        except Exception:
            metric_crs = None

        if metric_crs:
            working = working.to_crs(metric_crs)
            working["geometry"] = gpd.GeoSeries(
                [shapely.set_precision(geom, grid_size=1) if geom is not None else None for geom in working.geometry],
                index=working.index,
                crs=metric_crs,
            )
            if any(gt in {"Polygon", "MultiPolygon"} for gt in geom_types):
                working = working[working.geometry.notna() & ~working.geometry.is_empty].copy()
                working["geometry"] = working.geometry.buffer(0)
            working = working.to_crs("EPSG:4326")
        elif working.crs and str(working.crs).upper() != "EPSG:4326":
            working = working.to_crs("EPSG:4326")
    elif working.crs and str(working.crs).upper() != "EPSG:4326":
        working = working.to_crs("EPSG:4326")

    obj = json.loads(working.to_json(drop_id=True))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, separators=(",", ":"), ensure_ascii=False)

    after_bytes = path.stat().st_size
    return {
        "path": rel,
        "before_mb": round(before_bytes / (1024 * 1024), 3),
        "after_mb": round(after_bytes / (1024 * 1024), 3),
        "saved_mb": round((before_bytes - after_bytes) / (1024 * 1024), 3),
        "saved_pct": round((1 - after_bytes / before_bytes) * 100, 1) if before_bytes else 0.0,
        "status": "optimized",
    }


def main() -> None:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    geo_files = [
        p for p in ROOT.rglob("*.geojson")
        if BACKUP_ROOT.name not in p.parts and "legacy" not in p.parts
    ]

    rows = []
    total_before = 0
    total_after = 0

    for path in sorted(geo_files):
        before = path.stat().st_size
        total_before += before
        try:
            row = optimize_geojson(path)
            rows.append(row)
            total_after += path.stat().st_size
        except Exception as exc:
            rows.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "before_mb": round(before / (1024 * 1024), 3),
                    "after_mb": round(before / (1024 * 1024), 3),
                    "saved_mb": 0.0,
                    "saved_pct": 0.0,
                    "status": f"error: {exc}",
                }
            )
            total_after += before

    report = pd.DataFrame(rows).sort_values(["saved_mb", "before_mb"], ascending=False)
    report.to_csv(REPORT_PATH, index=False)

    print(f"PROCESSED {len(report)} files")
    print(f"TOTAL_BEFORE_MB {total_before / (1024 * 1024):.3f}")
    print(f"TOTAL_AFTER_MB {total_after / (1024 * 1024):.3f}")
    print(f"TOTAL_SAVED_MB {(total_before - total_after) / (1024 * 1024):.3f}")
    print(f"TOTAL_SAVED_PCT {(1 - total_after / total_before) * 100:.1f}")
    print(f"BACKUP_ROOT {BACKUP_ROOT}")
    print(f"REPORT {REPORT_PATH}")
    print("\nTOP_SAVINGS")
    print(report.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
