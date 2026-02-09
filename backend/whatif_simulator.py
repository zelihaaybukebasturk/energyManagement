"""
What-if simulation engine (room / zone scale).

Inputs are intentionally simple and presentation-friendly:
- room_m2
- people_count
- electricity_kwh (for selected period)
- room_temp_c

Scenarios supported:
- led
- occupancy_down_20
- hours_shorter
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


DEFAULT_SHARES_BY_BUILDING = {
    "office": {"lighting": 0.20, "hvac": 0.45, "plug": 0.35},
    "school": {"lighting": 0.25, "hvac": 0.40, "plug": 0.35},
    "university": {"lighting": 0.22, "hvac": 0.43, "plug": 0.35},
    "hotel": {"lighting": 0.18, "hvac": 0.52, "plug": 0.30},
    "residential": {"lighting": 0.12, "hvac": 0.45, "plug": 0.43},
    "hospital": {"lighting": 0.18, "hvac": 0.55, "plug": 0.27},
}


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _round(x: Optional[float], nd: int = 2) -> Optional[float]:
    if x is None:
        return None
    try:
        return round(float(x), nd)
    except Exception:
        return None


@dataclass(frozen=True)
class SimulationInputs:
    room_m2: float
    people_count: int
    electricity_kwh: float
    period_months: float
    room_temp_c: float
    building_type: str = "office"
    baseline_hours_per_day: float = 9.0
    new_hours_per_day: Optional[float] = None
    electricity_price_tl_per_kwh: float = 3.5
    grid_emission_factor_kgco2_per_kwh: float = 0.42
    outdoor_temp_c: Optional[float] = None


def compute_kpis(
    total_kwh: float,
    room_m2: float,
    people_count: int,
    period_months: float,
    price_tl_per_kwh: float,
    emission_factor: float,
) -> Dict[str, Any]:
    annual_multiplier = 12.0 / period_months if period_months and period_months > 0 else 12.0
    total_kwh_annual = total_kwh * annual_multiplier

    per_person_kwh = (total_kwh / people_count) if people_count and people_count > 0 else None
    per_sqm_kwh = (total_kwh / room_m2) if room_m2 and room_m2 > 0 else None
    per_person_co2 = (per_person_kwh * emission_factor) if per_person_kwh is not None else None

    return {
        "area_m2": _round(room_m2, 2),
        "people_count": int(people_count) if people_count is not None else None,
        "period_months": _round(period_months, 2),
        "total_kwh": _round(total_kwh, 2),
        "total_kwh_annual_est": _round(total_kwh_annual, 2),
        "energy_per_person_kwh": _round(per_person_kwh, 2),
        "energy_per_sqm_kwh": _round(per_sqm_kwh, 3),
        "co2_per_person_kg": _round(per_person_co2, 2),
        "cost_tl": _round(total_kwh * price_tl_per_kwh, 2),
        "cost_tl_annual_est": _round(total_kwh_annual * price_tl_per_kwh, 2),
    }


def simulate_whatif(inputs: SimulationInputs, scenario: str) -> Dict[str, Any]:
    scenario = (scenario or "").strip().lower()
    if scenario not in {"led", "occupancy_down_20", "hours_shorter"}:
        scenario = "led"

    btype = (inputs.building_type or "office").lower()
    shares = DEFAULT_SHARES_BY_BUILDING.get(btype, DEFAULT_SHARES_BY_BUILDING["office"])

    base_total = float(inputs.electricity_kwh)
    base_people = int(inputs.people_count) if inputs.people_count is not None else 0
    base_room_m2 = float(inputs.room_m2)
    period_months = float(inputs.period_months) if inputs.period_months else 1.0

    baseline = compute_kpis(
        total_kwh=base_total,
        room_m2=base_room_m2,
        people_count=base_people,
        period_months=period_months,
        price_tl_per_kwh=float(inputs.electricity_price_tl_per_kwh),
        emission_factor=float(inputs.grid_emission_factor_kgco2_per_kwh),
    )

    lighting_kwh = base_total * shares["lighting"]
    hvac_kwh = base_total * shares["hvac"]
    plug_kwh = base_total * shares["plug"]

    whatif_people = base_people
    new_total = base_total
    notes: List[str] = []

    if scenario == "led":
        # Conservative combined impact: lighting cut + small cooling side-benefit.
        led_lighting_savings_rate = 0.55  # 50-70% typical; choose 55% as base
        heat_gain_side_benefit = 0.08     # small HVAC reduction due to reduced internal heat

        lighting_saved = lighting_kwh * led_lighting_savings_rate
        hvac_side_saved = lighting_saved * heat_gain_side_benefit
        new_total = base_total - lighting_saved - hvac_side_saved

        notes.append("LED dönüşümü aydınlatma tüketimini düşürür; ayrıca iç ısı kazançları azaldığı için soğutma yükünde küçük bir ek iyileşme görülebilir.")
        notes.append("Bu hesapta aydınlatma için %55 tasarruf ve HVAC için ek %8 yan-etki varsayılmıştır.")

    elif scenario == "occupancy_down_20":
        # Energy doesn't scale 1:1 with occupancy: fixed + variable loads.
        fixed_share = 0.60
        variable_share = 1.0 - fixed_share

        whatif_people = max(1, int(round(base_people * 0.8)))
        fixed_kwh = base_total * fixed_share
        variable_kwh = base_total * variable_share
        new_total = fixed_kwh + variable_kwh * (whatif_people / base_people if base_people > 0 else 1.0)

        notes.append("Kişi sayısı azalınca tüketim tamamen aynı oranda düşmez; sabit yükler (sunucular, standby, temel HVAC) devam eder.")
        notes.append("Bu hesapta %60 sabit, %40 değişken tüketim varsayılmıştır.")

    elif scenario == "hours_shorter":
        base_h = float(inputs.baseline_hours_per_day or 9.0)
        new_h = float(inputs.new_hours_per_day) if inputs.new_hours_per_day is not None else base_h * 0.8

        base_h = _clamp(base_h, 1.0, 24.0)
        new_h = _clamp(new_h, 1.0, 24.0)
        ratio = _clamp(new_h / base_h if base_h > 0 else 1.0, 0.2, 1.2)

        schedule_dependent_share = 0.65
        base_load_share = 1.0 - schedule_dependent_share
        new_total = base_total * base_load_share + base_total * schedule_dependent_share * ratio

        notes.append("Çalışma saatleri kısalınca özellikle aydınlatma, HVAC ve priz yükleri (planlı yükler) düşer; ancak bazı sabit tüketimler devam eder.")
        notes.append(f"Bu hesapta planlı yük oranı %65 varsayıldı; saat oranı ≈ %{round(ratio*100,1)} olarak uygulandı.")

    new_total = max(0.0, float(new_total))
    whatif = compute_kpis(
        total_kwh=new_total,
        room_m2=base_room_m2,
        people_count=whatif_people,
        period_months=period_months,
        price_tl_per_kwh=float(inputs.electricity_price_tl_per_kwh),
        emission_factor=float(inputs.grid_emission_factor_kgco2_per_kwh),
    )

    savings_kwh = base_total - new_total
    savings_pct = (savings_kwh / base_total * 100.0) if base_total > 0 else 0.0
    savings_tl_annual = (baseline["cost_tl_annual_est"] or 0) - (whatif["cost_tl_annual_est"] or 0)

    # Weather context (doesn't change totals; adds interpretation).
    weather_context = None
    if inputs.outdoor_temp_c is not None:
        try:
            dt = abs(float(inputs.room_temp_c) - float(inputs.outdoor_temp_c))
            hvac_load_index = dt / 20.0  # 20°C delta as "neutral-ish" reference
            weather_context = {
                "outdoor_temp_c": _round(float(inputs.outdoor_temp_c), 1),
                "indoor_setpoint_c": _round(float(inputs.room_temp_c), 1),
                "delta_t_c": _round(dt, 1),
                "hvac_load_index": _round(hvac_load_index, 2),
                "comment": (
                    "ΔT yüksekse HVAC yükü artma eğilimindedir; bu da saat kısaltma / setpoint optimizasyonu gibi önlemlerin etkisini güçlendirebilir."
                    if hvac_load_index >= 1.0
                    else "ΔT görece düşük; HVAC yükü daha ılımlı olabilir."
                ),
            }
        except Exception:
            weather_context = None

    # Build 3 solution scenarios (presentation-friendly, with estimated totals).
    solutions: List[Dict[str, Any]] = []
    if scenario == "led":
        # Scenario 1: LED only
        s1_total = new_total
        # Scenario 2: LED + occupancy sensors (extra 15% of remaining lighting)
        s2_total = base_total - (lighting_kwh * 0.55) - (lighting_kwh * 0.45 * 0.15) - ((lighting_kwh * 0.55) * 0.08)
        # Scenario 3: LED + sensors + scheduling (small HVAC + plug reduction)
        s3_total = s2_total * (1.0 - 0.05)  # 5% whole-building ops tuning
        solutions = [
            {"name": "Senaryo 1", "summary": "Sadece LED dönüşümü", "total_kwh": _round(max(0.0, s1_total), 2)},
            {"name": "Senaryo 2", "summary": "LED + hareket sensörü + zamanlayıcı", "total_kwh": _round(max(0.0, s2_total), 2)},
            {"name": "Senaryo 3", "summary": "LED + sensör + otomasyon (saat/kapama disiplinleri)", "total_kwh": _round(max(0.0, s3_total), 2)},
        ]
    elif scenario == "occupancy_down_20":
        # Scenario 1: No space consolidation (baseline fixed stays)
        s1_total = new_total
        # Scenario 2: Consolidate spaces -> reduce fixed by 10%
        fixed_share = 0.60
        variable_share = 0.40
        fixed_kwh = base_total * fixed_share
        variable_kwh = base_total * variable_share
        s2_total = fixed_kwh * 0.90 + variable_kwh * 0.80
        # Scenario 3: Consolidate + demand-controlled ventilation -> extra 6% cut
        s3_total = s2_total * 0.94
        solutions = [
            {"name": "Senaryo 1", "summary": "Kişi azalır ama alanlar aynı kalır (sabit yükler korunur)", "total_kwh": _round(max(0.0, s1_total), 2)},
            {"name": "Senaryo 2", "summary": "Alan konsolidasyonu + program optimizasyonu (sabit yüklerde azalma)", "total_kwh": _round(max(0.0, s2_total), 2)},
            {"name": "Senaryo 3", "summary": "Konsolidasyon + talep kontrollü havalandırma (DCV)", "total_kwh": _round(max(0.0, s3_total), 2)},
        ]
    else:
        # hours_shorter
        s1_total = new_total
        # Scenario 2: Better shutdown discipline (extra 4% whole-building)
        s2_total = s1_total * 0.96
        # Scenario 3: Automation + HVAC setback (extra 8% whole-building)
        s3_total = s1_total * 0.92
        solutions = [
            {"name": "Senaryo 1", "summary": "Çalışma saatini kısaltma", "total_kwh": _round(max(0.0, s1_total), 2)},
            {"name": "Senaryo 2", "summary": "Saat kısaltma + mesai dışı kapama disiplini", "total_kwh": _round(max(0.0, s2_total), 2)},
            {"name": "Senaryo 3", "summary": "Saat kısaltma + otomasyon + HVAC setback", "total_kwh": _round(max(0.0, s3_total), 2)},
        ]

    def _solution_metrics(total_kwh: float) -> Dict[str, Any]:
        k = compute_kpis(
            total_kwh=float(total_kwh),
            room_m2=base_room_m2,
            people_count=whatif_people if scenario != "occupancy_down_20" else max(1, int(round(base_people * 0.8))),
            period_months=period_months,
            price_tl_per_kwh=float(inputs.electricity_price_tl_per_kwh),
            emission_factor=float(inputs.grid_emission_factor_kgco2_per_kwh),
        )
        save_kwh = base_total - float(total_kwh)
        save_pct = (save_kwh / base_total * 100.0) if base_total > 0 else 0.0
        save_tl_annual = (baseline["cost_tl_annual_est"] or 0) - (k["cost_tl_annual_est"] or 0)
        return {"kpis": k, "savings_percent": _round(save_pct, 2), "annual_savings_tl_est": _round(save_tl_annual, 2)}

    solutions_out = []
    for s in solutions:
        total = float(s["total_kwh"] or 0)
        sm = _solution_metrics(total)
        solutions_out.append({**s, **sm})

    return {
        "scenario": scenario,
        "assumptions": {
            "building_type": btype,
            "shares": shares,
            "lighting_kwh_est": _round(lighting_kwh, 2),
            "hvac_kwh_est": _round(hvac_kwh, 2),
            "plug_kwh_est": _round(plug_kwh, 2),
        },
        "baseline": baseline,
        "whatif": whatif,
        "delta": {
            "savings_kwh": _round(savings_kwh, 2),
            "savings_percent": _round(savings_pct, 2),
            "annual_savings_tl_est": _round(savings_tl_annual, 2),
        },
        "weather_context": weather_context,
        "notes": notes,
        "solutions": solutions_out,
    }

