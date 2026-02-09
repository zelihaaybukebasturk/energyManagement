"""
Simple test script to verify the system works correctly.
Run this after starting the server to test the API.
"""

import requests
import json

API_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_benchmarks():
    """Test benchmarks endpoint."""
    print("Testing benchmarks endpoint...")
    response = requests.get(f"{API_URL}/benchmarks/school")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

def test_analysis():
    """Test building analysis endpoint."""
    print("Testing building analysis endpoint...")
    
    test_data = {
        "total_energy_kwh": 50000,
        "building_area_m2": 2000,
        "building_type": "school",
        "occupancy": 200,
        "period_months": 12.0
    }
    
    response = requests.post(
        f"{API_URL}/analyze",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Efficiency Level: {result['efficiency_evaluation']['efficiency_level']}")
        print(f"Energy per m²: {result['kpis']['energy_per_sqm_kwh']:.2f} kWh/m²")
        print(f"Annual Energy per m²: {result['efficiency_evaluation']['annual_energy_per_sqm']:.2f} kWh/m²/year")
        print(f"\nExplanation preview:")
        print(result['ai_explanation']['explanation'][:200] + "...")
    else:
        print(f"Error: {response.text}\n")

if __name__ == "__main__":
    print("=" * 60)
    print("AI-Driven Building Energy Efficiency System - Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_health()
        test_benchmarks()
        test_analysis()
        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the server.")
        print("Make sure the server is running on http://localhost:8000")
        print("Start it with: python start_server.py")
    except Exception as e:
        print(f"ERROR: {e}")

