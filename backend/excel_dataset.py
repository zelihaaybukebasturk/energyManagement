"""
Auxiliary Excel dataset loader for building energy records.
Uses the dataset for validation, benchmarking, and optional RAG context.
Does NOT replace deterministic KPI formulas or rule-based efficiency logic.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


# Default path: project root or env
def _default_excel_path() -> Path:
    root = Path(__file__).parent.parent
    env_path = os.getenv("EXCEL_DATASET_PATH")
    if env_path and Path(env_path).exists():
        return Path(env_path)
    # Check common locations
    for name in ["Analiz-Lokman Hekim Rev.00.2.xlsx", "building_energy_data.xlsx"]:
        p = root / name
        if p.exists():
            return p
    return root / "data" / "building_energy_data.xlsx"


def load_excel_dataset(path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load building energy records from Excel (Lokman Hekim / generic structure).
    Each row becomes a record with: year, building_area_m2, total_energy_kwh, (optional) occupancy, source.
    Used only as auxiliary data for validation, benchmarking, or RAG context.
    """
    if not HAS_PANDAS:
        return []

    filepath = Path(path) if path else _default_excel_path()
    if not filepath.exists():
        return []

    records = []
    try:
        xl = pd.ExcelFile(filepath)
        # Turkish sheet names (may be encoding-dependent)
        ref_name = next((s for s in xl.sheet_names if "Referans" in s or "referans" in s.lower()), None)
        gosterge_name = next((s for s in xl.sheet_names if "sterge" in s or "Gosterge" in s or "Gösterge" in s), None)

        # Referans Tablolar: Year column + "Toplam Yıllık Saha/Nihai* Enerji Kullanımı [kWh]" or similar
        if ref_name:
            df_ref = pd.read_excel(filepath, sheet_name=ref_name)
            year_col = df_ref.columns[0]
            # Prefer "Toplam Yıllık Saha/Nihai* Enerji Kullanımı [kWh]" (total final energy), not electricity-only
            kwh_col = None
            for c in df_ref.columns:
                cstr = str(c).lower()
                if "kwh" in cstr and ("saha" in cstr or "nihai" in cstr):
                    kwh_col = c
                    break
            if kwh_col is None:
                for c in df_ref.columns:
                    cstr = str(c).lower()
                    if "kwh" in cstr and "toplam" in cstr:
                        kwh_col = c
                        break
            if kwh_col is None:
                for c in df_ref.columns:
                    if "kwh" in str(c).lower():
                        kwh_col = c
                        break
            if kwh_col:
                for _, row in df_ref.iterrows():
                    try:
                        y = row.get(year_col)
                        kwh = row.get(kwh_col)
                        if pd.isna(y) or pd.isna(kwh):
                            continue
                        y = int(float(y)) if isinstance(y, (int, float)) else None
                        if y is None or not (2000 <= y <= 2100):
                            continue
                        kwh = float(kwh)
                        if kwh <= 0:
                            continue
                        records.append({
                            "year": y,
                            "total_energy_kwh": kwh,
                            "building_area_m2": None,
                            "occupancy": None,
                            "source": ref_name,
                            "building_type": "hospital",
                        })
                    except (ValueError, TypeError):
                        continue

        # Gösterge Tablolar: row "Bina İnşaat Alanı" -> area; row "Yıllık Toplam Enerji Tüketimi" -> total kWh; year columns 2022, 2023, 2024
        if gosterge_name:
            df_g = pd.read_excel(filepath, sheet_name=gosterge_name)
            area_row = None
            total_energy_row = None
            for i in range(min(len(df_g), 20)):
                row = df_g.iloc[i]
                desc = str(row.iloc[1]) if len(row) > 1 else ""
                desc_lower = desc.lower()
                # Match exactly the building area row (Bina İnşaat Alanı), not "Armatür" etc.
                if ("bina" in desc_lower or "inşaat" in desc_lower) and ("alan" in desc_lower or "area" in desc_lower):
                    area_row = i
                if "toplam" in desc_lower and "enerji" in desc_lower and ("tüketim" in desc_lower or "tüketimi" in desc_lower):
                    total_energy_row = i
            area_m2 = None
            if area_row is not None:
                for c in range(2, min(6, len(df_g.columns))):
                    try:
                        v = df_g.iloc[area_row, c]
                        if pd.notna(v):
                            val = float(v)
                            if 100 <= val <= 1e7:  # sensible m² range
                                area_m2 = val
                                break
                    except (ValueError, TypeError):
                        pass
            year_cols = [c for c in df_g.columns if isinstance(c, (int, float)) and 2000 <= c <= 2100]
            if not year_cols:
                year_cols = [c for c in df_g.columns if "202" in str(c)]
            for ycol in year_cols:
                try:
                    y = int(ycol) if isinstance(ycol, (int, float)) else int(str(ycol)[:4])
                except Exception:
                    continue
                kwh = None
                if total_energy_row is not None:
                    try:
                        idx = list(df_g.columns).index(ycol)
                        kwh = float(df_g.iloc[total_energy_row, idx])
                    except Exception:
                        pass
                if kwh is None or kwh <= 0:
                    continue
                records.append({
                    "year": y,
                    "total_energy_kwh": kwh,
                    "building_area_m2": area_m2,
                    "occupancy": None,
                    "source": gosterge_name,
                    "building_type": "hospital",
                })
    except Exception as e:
        # Log but don't break the app
        print(f"Excel dataset load warning: {e}")
    return records


def get_dataset_stats(records: List[Dict]) -> Dict[str, Any]:
    """Compute simple stats from dataset for benchmarking (no change to core formulas)."""
    if not records:
        return {"count": 0, "message": "No records loaded."}
    total_kwh = [r["total_energy_kwh"] for r in records if r.get("total_energy_kwh")]
    areas = [r["building_area_m2"] for r in records if r.get("building_area_m2") and r["building_area_m2"] > 0]
    energy_per_sqm = []
    for r in records:
        a, e = r.get("building_area_m2"), r.get("total_energy_kwh")
        if a and a > 0 and e and e > 0:
            energy_per_sqm.append(e / a)
    out = {
        "count": len(records),
        "total_energy_kwh": {"min": min(total_kwh), "max": max(total_kwh), "mean": sum(total_kwh) / len(total_kwh)} if total_kwh else None,
        "building_area_m2": {"min": min(areas), "max": max(areas), "mean": sum(areas) / len(areas)} if areas else None,
        "energy_per_sqm_kwh": {"min": min(energy_per_sqm), "max": max(energy_per_sqm), "mean": sum(energy_per_sqm) / len(energy_per_sqm)} if energy_per_sqm else None,
    }
    return out


def get_records_for_rag(records: List[Dict], building_type: str, energy_per_sqm: float, limit: int = 5) -> List[Dict]:
    """
    Return a few similar records (by building type and energy/m²) for RAG context.
    Does not change how KPIs or efficiency are computed.
    """
    with_area = [r for r in records if r.get("building_area_m2") and r.get("total_energy_kwh")]
    if not with_area:
        return []
    for r in with_area:
        r["_energy_per_sqm"] = r["total_energy_kwh"] / r["building_area_m2"]
    typed = [r for r in with_area if (r.get("building_type") or "").lower() == building_type.lower()]
    if not typed:
        typed = with_area
    typed.sort(key=lambda r: abs(r["_energy_per_sqm"] - energy_per_sqm))
    return [{"year": r["year"], "total_energy_kwh": r["total_energy_kwh"], "building_area_m2": r["building_area_m2"], "energy_per_sqm_kwh": round(r["_energy_per_sqm"], 2)} for r in typed[:limit]]
