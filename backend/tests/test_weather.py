import asyncio
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import httpx
from httpx import ASGITransport, AsyncClient

from app.api.routes import weather as weather_routes
from app.main import app
from app.services.weather import (
    WeatherLocationNotFound,
    WeatherProviderError,
    clear_weather_cache,
    get_weather_forecast,
)


def test_weather_forecast_normalizes_data_and_caches():
    async def exercise() -> None:
        await clear_weather_cache()
        requests = []
        current_hour = datetime.now(timezone.utc).replace(
            minute=0,
            second=0,
            microsecond=0,
        )
        times = [
            current_hour.replace(tzinfo=None).isoformat(timespec="minutes")
        ]
        for hour in range(1, 8):
            times.append(
                (current_hour.replace(tzinfo=None) + timedelta(hours=hour)).isoformat(
                    timespec="minutes"
                )
            )

        def handle_request(request: httpx.Request) -> httpx.Response:
            requests.append(urlparse(str(request.url)).path)
            if "geocoding" in request.url.host:
                return httpx.Response(
                    200,
                    json={
                        "results": [
                            {
                                "name": "Mangaluru",
                                "country": "India",
                                "latitude": 12.87,
                                "longitude": 74.88,
                            }
                        ]
                    },
                )
            return httpx.Response(
                200,
                json={
                    "timezone": "UTC",
                    "hourly": {
                        "time": times,
                        "precipitation_probability": [70] * len(times),
                        "precipitation": [12.0] * len(times),
                        "wind_speed_10m": [54.0] * len(times),
                        "weather_code": [65] * len(times),
                    },
                },
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handle_request)
        ) as client:
            result = await get_weather_forecast("Mangaluru", client)
            cached = await get_weather_forecast("mangaluru", client)

        assert result["status"] == "available"
        assert result["source"] == "Open-Meteo"
        assert result["location"]["name"] == "Mangaluru"
        assert result["risk"]["level"] == "high"
        assert "Severe precipitation or thunderstorm is forecast" in result["risk"]["drivers"]
        assert result["hours"][0]["condition"] == "Heavy rain"
        assert len(result["hours"]) == 6
        assert "does not confirm" in result["notice"]
        assert cached["data_freshness"] == "Cached forecast"
        assert len(requests) == 2
        await clear_weather_cache()

    asyncio.run(exercise())


def test_weather_location_not_found_is_explicit():
    async def exercise() -> None:
        await clear_weather_cache()

        def handle_request(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"results": []})

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handle_request)
        ) as client:
            try:
                await get_weather_forecast("No Such Place", client)
            except WeatherLocationNotFound as exc:
                assert str(exc) == "No weather location matched that search."
            else:
                raise AssertionError("Expected an explicit location-not-found error")
        await clear_weather_cache()

    asyncio.run(exercise())


def test_weather_endpoint_returns_provider_limitations(monkeypatch):
    async def unavailable(location: str) -> dict:
        raise WeatherProviderError("Weather provider is temporarily unavailable.")

    monkeypatch.setattr(weather_routes, "get_weather_forecast", unavailable)

    async def exercise() -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/api/v1/weather/forecast",
                params={"location": "Mangaluru"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "unavailable"
        assert response.json()["hours"] == []
        assert "temporarily unavailable" in response.json()["notice"]

    asyncio.run(exercise())
