import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
CACHE_TTL_SECONDS = 15 * 60
MAX_CACHE_ITEMS = 128

_forecast_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_cache_lock = asyncio.Lock()


class WeatherProviderError(Exception):
    pass


class WeatherLocationNotFound(Exception):
    pass


async def get_weather_forecast(
    location: str,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    cache_key = location.strip().casefold()
    now = time.monotonic()

    async with _cache_lock:
        cached = _forecast_cache.get(cache_key)
        if cached is not None and cached[0] > now:
            response = cached[1].copy()
            response["data_freshness"] = "Cached forecast"
            return response

    try:
        if client is None:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(8.0, connect=3.0),
                follow_redirects=False,
            ) as provider_client:
                result = await _fetch_forecast(location, provider_client)
        else:
            result = await _fetch_forecast(location, client)
    except WeatherLocationNotFound:
        raise
    except WeatherProviderError:
        async with _cache_lock:
            cached = _forecast_cache.get(cache_key)
        if cached is None:
            raise
        stale_response = cached[1].copy()
        stale_response["data_freshness"] = "Stale cached forecast"
        stale_response["notice"] = (
            "Open-Meteo could not be reached; this forecast may be outdated."
        )
        return stale_response

    async with _cache_lock:
        if len(_forecast_cache) >= MAX_CACHE_ITEMS:
            oldest_key = min(
                _forecast_cache,
                key=lambda key: _forecast_cache[key][0],
            )
            del _forecast_cache[oldest_key]
        _forecast_cache[cache_key] = (
            time.monotonic() + CACHE_TTL_SECONDS,
            result,
        )
    return result


async def clear_weather_cache() -> None:
    async with _cache_lock:
        _forecast_cache.clear()


async def _fetch_forecast(
    location: str,
    client: httpx.AsyncClient,
) -> dict[str, Any]:
    geocoding = await _get_json(
        client,
        GEOCODING_URL,
        {"name": location, "count": 1, "language": "en", "format": "json"},
    )
    locations = geocoding.get("results")
    if not isinstance(locations, list) or not locations:
        raise WeatherLocationNotFound("No weather location matched that search.")
    match = locations[0]
    try:
        latitude = float(match["latitude"])
        longitude = float(match["longitude"])
        place_name = str(match["name"])
    except (KeyError, TypeError, ValueError) as exc:
        raise WeatherProviderError("Open-Meteo returned an invalid location.") from exc

    forecast = await _get_json(
        client,
        FORECAST_URL,
        {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": (
                "precipitation_probability,precipitation,wind_speed_10m,weather_code"
            ),
            "forecast_days": 2,
            "timezone": "UTC",
        },
    )
    hourly = forecast.get("hourly")
    if not isinstance(hourly, dict):
        raise WeatherProviderError("Open-Meteo returned no hourly forecast.")

    points = _extract_next_hours(hourly, count=6)
    if not points:
        raise WeatherProviderError("Open-Meteo returned no usable forecast hours.")

    risk = _estimate_risk(points)
    fetched_at = datetime.now(timezone.utc).isoformat()
    return {
        "status": "available",
        "location": {
            "name": place_name,
            "country": match.get("country"),
            "latitude": latitude,
            "longitude": longitude,
            "timezone": forecast.get("timezone", "UTC"),
        },
        "source": "Open-Meteo",
        "data_freshness": "Forecast fetched",
        "fetched_at": fetched_at,
        "risk": risk,
        "hours": points,
        "notice": (
            "Weather-related risk is an estimate only and does not confirm "
            "a transport delay or cancellation."
        ),
    }


async def _get_json(
    client: httpx.AsyncClient,
    url: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            logger.warning("Open-Meteo rate limit reached")
            raise WeatherProviderError(
                "Weather provider rate limit reached; please try again later."
            ) from exc
        logger.warning("Open-Meteo request failed with status %s", exc.response.status_code)
        raise WeatherProviderError("Weather provider returned an error.") from exc
    except (httpx.RequestError, ValueError) as exc:
        logger.warning("Open-Meteo request or response parsing failed: %s", exc)
        raise WeatherProviderError("Weather provider is temporarily unavailable.") from exc

    if not isinstance(payload, dict):
        raise WeatherProviderError("Weather provider returned an invalid response.")
    return payload


def _extract_next_hours(hourly: dict[str, Any], count: int) -> list[dict[str, Any]]:
    times = hourly.get("time")
    if not isinstance(times, list):
        return []

    fields = {
        "precipitation_probability_percent": hourly.get("precipitation_probability"),
        "precipitation_mm": hourly.get("precipitation"),
        "wind_speed_kmh": hourly.get("wind_speed_10m"),
        "weather_code": hourly.get("weather_code"),
    }
    if any(not isinstance(values, list) for values in fields.values()):
        return []

    current_hour = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    points = []
    for index, timestamp in enumerate(times):
        try:
            parsed_time = datetime.fromisoformat(str(timestamp)).replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            continue
        if parsed_time < current_hour:
            continue
        try:
            values = {name: field[index] for name, field in fields.items()}
            point = {
                "time": parsed_time.isoformat(),
                "precipitation_probability_percent": int(
                    values["precipitation_probability_percent"]
                ),
                "precipitation_mm": float(values["precipitation_mm"]),
                "wind_speed_kmh": float(values["wind_speed_kmh"]),
                "weather_code": int(values["weather_code"]),
                "condition": _weather_description(int(values["weather_code"])),
            }
        except (IndexError, TypeError, ValueError):
            continue
        points.append(point)
        if len(points) == count:
            break
    return points


def _estimate_risk(points: list[dict[str, Any]]) -> dict[str, Any]:
    drivers: set[str] = set()
    high_risk = False

    for point in points:
        code = point["weather_code"]
        precipitation = point["precipitation_mm"]
        probability = point["precipitation_probability_percent"]
        wind = point["wind_speed_kmh"]

        if code in {65, 67, 75, 82, 86} or code >= 95:
            drivers.add("Severe precipitation or thunderstorm is forecast")
            high_risk = True
        if precipitation >= 10:
            drivers.add("Hourly precipitation is forecast at 10 mm or more")
            high_risk = True
        if wind >= 50:
            drivers.add("Wind speed is forecast at 50 km/h or more")
            high_risk = True
        if probability >= 50 or precipitation >= 1:
            drivers.add("Rain is forecast during the next six hours")
        if 30 <= wind < 50:
            drivers.add("Wind speed is forecast at 30 km/h or more")

    if high_risk:
        level = "high"
    elif drivers:
        level = "moderate"
    else:
        level = "low"

    return {
        "level": level,
        "window_hours": len(points),
        "drivers": sorted(drivers),
        "method": (
            "High: any forecast hour has a severe weather code, precipitation "
            "of at least 10 mm, or wind of at least 50 km/h. Moderate: rain "
            "probability is at least 50%, precipitation is at least 1 mm, or "
            "wind is at least 30 km/h. Otherwise low."
        ),
    }


def _weather_description(code: int) -> str:
    descriptions = {
        0: "Clear",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with heavy hail",
    }
    return descriptions.get(code, "Mixed or unknown conditions")
