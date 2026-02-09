"""
Rule-Based Efficiency Evaluation Engine
Classifies buildings as efficient, moderately efficient, or inefficient
based on building type and reference benchmarks.
"""

from typing import Dict, Literal, Optional
from enum import Enum


class EfficiencyLevel(str, Enum):
    """Efficiency classification levels."""
    EFFICIENT = "efficient"
    MODERATELY_EFFICIENT = "moderately_efficient"
    INEFFICIENT = "inefficient"


class EfficiencyEvaluator:
    """Evaluates building energy efficiency using rule-based benchmarks."""
    
    # Reference energy intensity values (kWh/m²/year)
    # Based on engineering norms and best practices
    BENCHMARKS = {
        "school": {
            "efficient": 80,      # Excellent performance
            "moderate": 120,       # Average performance
            "inefficient": 150,    # Poor performance threshold
        },
        "university": {
            "efficient": 100,
            "moderate": 150,
            "inefficient": 200,
        },
        "hotel": {
            "efficient": 120,
            "moderate": 180,
            "inefficient": 250,
        },
        "residential": {
            "efficient": 60,
            "moderate": 100,
            "inefficient": 150,
        },
        "office": {
            "efficient": 100,
            "moderate": 150,
            "inefficient": 200,
        },
        "hospital": {
            "efficient": 150,
            "moderate": 250,
            "inefficient": 350,
        },
    }
    
    def __init__(self):
        """Initialize the efficiency evaluator."""
        pass
    
    def evaluate_efficiency(
        self,
        energy_per_sqm_kwh: float,
        building_type: str,
        period_months: float = 12.0
    ) -> Dict[str, any]:
        """
        Evaluate building energy efficiency.
        
        Args:
            energy_per_sqm_kwh: Energy consumption per square meter (for the period)
            building_type: Type of building (school, university, hotel, etc.)
            period_months: Period of measurement in months (default: 12 for annual)
        
        Returns:
            Dictionary containing efficiency classification and details
        """
        # Normalize to annual if needed
        annual_energy_per_sqm = energy_per_sqm_kwh * (12.0 / period_months)
        
        # Get benchmarks for building type
        building_type_lower = building_type.lower()
        if building_type_lower not in self.BENCHMARKS:
            # Default to office if unknown type
            building_type_lower = "office"
        
        benchmarks = self.BENCHMARKS[building_type_lower]
        
        # Classify efficiency
        if annual_energy_per_sqm <= benchmarks["efficient"]:
            level = EfficiencyLevel.EFFICIENT
            score = "excellent"
        elif annual_energy_per_sqm <= benchmarks["moderate"]:
            level = EfficiencyLevel.MODERATELY_EFFICIENT
            score = "average"
        else:
            level = EfficiencyLevel.INEFFICIENT
            score = "poor"
        
        # Calculate potential savings
        if level == EfficiencyLevel.INEFFICIENT:
            target_energy = benchmarks["moderate"]
            potential_savings_percent = ((annual_energy_per_sqm - target_energy) / annual_energy_per_sqm) * 100
        elif level == EfficiencyLevel.MODERATELY_EFFICIENT:
            target_energy = benchmarks["efficient"]
            potential_savings_percent = ((annual_energy_per_sqm - target_energy) / annual_energy_per_sqm) * 100
        else:
            potential_savings_percent = 0
        
        return {
            "efficiency_level": level.value,
            "efficiency_score": score,
            "annual_energy_per_sqm": annual_energy_per_sqm,
            "building_type": building_type_lower,
            "benchmarks": benchmarks,
            "potential_savings_percent": round(potential_savings_percent, 2),
            "comparison": {
                "efficient_threshold": benchmarks["efficient"],
                "moderate_threshold": benchmarks["moderate"],
                "inefficient_threshold": benchmarks["inefficient"],
            }
        }
    
    def get_benchmark_info(self, building_type: str) -> Dict[str, float]:
        """Get benchmark values for a building type."""
        building_type_lower = building_type.lower()
        return self.BENCHMARKS.get(
            building_type_lower,
            self.BENCHMARKS["office"]  # Default
        )

