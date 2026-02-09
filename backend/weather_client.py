"""
Weather client (Open-Meteo) for contextual energy impact.

No API key required:
- Geocoding: https://geocoding-api.open-meteo.com/
- Forecast:   https://api.open-meteo.com/
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def geocode_city(city: str, timeout_s: int = 8) -> Optional[Dict[str, Any]]:
    if not city or len(city.strip()) < 2:
        return None

    try:
        import requests
    except ImportError:
        return None

    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city.strip(), "count": 1, "language": "tr", "format": "json"}

    try:
        r = requests.get(url, params=params, timeout=timeout_s)
        r.raise_for_status()
        data = r.json() or {}
        results = data.get("results") or []
        if not results:
            return None
        top = results[0]
        return {
            "name": top.get("name"),
            "country": top.get("country"),
            "admin1": top.get("admin1"),
            "latitude": top.get("latitude"),
            "longitude": top.get("longitude"),
            "timezone": top.get("timezone"),
        }
    except Exception:
        return None


def fetch_weather(latitude: float, longitude: float, timeout_s: int = 10) -> Optional[Dict[str, Any]]:
    try:
        import requests
    except ImportError:
        return None

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": "auto",
    }

    try:
        r = requests.get(url, params=params, timeout=timeout_s)
        r.raise_for_status()
        data = r.json() or {}

        current = data.get("current") or {}
        daily = data.get("daily") or {}
        tmax = (daily.get("temperature_2m_max") or [None])[0]
        tmin = (daily.get("temperature_2m_min") or [None])[0]

        return {
            "outdoor_temp_c": current.get("temperature_2m"),
            "humidity_percent": current.get("relative_humidity_2m"),
            "wind_speed_m_s": current.get("wind_speed_10m"),
            "today_max_c": tmax,
            "today_min_c": tmin,
            "timezone": data.get("timezone"),
            "fetched_at": current.get("time"),
        }
    except Exception:
        return None


def fetch_weather_by_city(city: str) -> Optional[Dict[str, Any]]:
    geo = geocode_city(city)
    if not geo:
        return None
    w = fetch_weather(geo["latitude"], geo["longitude"])
    if not w:
        return None
    return {"location": geo, "weather": w}

