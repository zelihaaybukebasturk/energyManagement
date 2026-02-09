"""
Deterministic KPI Calculation Engine
Computes energy consumption metrics normalized by building characteristics.
"""

from typing import Dict, Optional


class KPICalculator:
    """Calculates energy consumption KPIs for buildings."""
    
    def __init__(self):
        """Initialize the KPI calculator."""
        pass
    
    def calculate_kpis(
        self,
        total_energy_kwh: float,
        building_area_m2: float,
        occupancy: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Calculate all energy consumption KPIs.
        
        Args:
            total_energy_kwh: Total energy consumption in kWh
            building_area_m2: Building area in square meters
            occupancy: Number of occupants (optional)
        
        Returns:
            Dictionary containing calculated KPIs
        """
        kpis = {
            "total_energy_kwh": total_energy_kwh,
            "energy_per_sqm_kwh": total_energy_kwh / building_area_m2 if building_area_m2 > 0 else 0,
            "building_area_m2": building_area_m2,
        }
        
        if occupancy and occupancy > 0:
            kpis["occupancy"] = occupancy
            kpis["energy_per_occupant_kwh"] = total_energy_kwh / occupancy
        else:
            kpis["occupancy"] = None
            kpis["energy_per_occupant_kwh"] = None
        
        return kpis
    
    def normalize_by_climate(
        self,
        energy_per_sqm: float,
        heating_degree_days: Optional[float] = None,
        cooling_degree_days: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Normalize energy consumption by climate factors.
        
        Args:
            energy_per_sqm: Energy per square meter
            heating_degree_days: Annual heating degree days
            cooling_degree_days: Annual cooling degree days
        
        Returns:
            Dictionary with normalized metrics
        """
        normalized = {
            "energy_per_sqm_kwh": energy_per_sqm,
            "heating_degree_days": heating_degree_days,
            "cooling_degree_days": cooling_degree_days,
        }
        
        # Simple normalization: adjust by degree days if available
        if heating_degree_days and heating_degree_days > 0:
            # Normalize to 3000 HDD baseline
            normalized["normalized_energy_per_sqm"] = energy_per_sqm * (3000 / heating_degree_days)
        else:
            normalized["normalized_energy_per_sqm"] = energy_per_sqm
        
        return normalized

