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
    search_weather_locations,
    _get_json,
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


def test_weather_city_search_is_filtered_by_selected_country():
    async def exercise() -> None:
        captured_params = {}

        def handle_request(request: httpx.Request) -> httpx.Response:
            captured_params.update(request.url.params)
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "name": "Mangalore",
                            "admin1": "Karnataka",
                            "country": "India",
                            "country_code": "IN",
                            "latitude": 12.87,
                            "longitude": 74.88,
                        }
                    ]
                },
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handle_request)
        ) as client:
            matches = await search_weather_locations("Mangalore", "in", client)

        assert captured_params["countryCode"] == "IN"
        assert captured_params["count"] == "8"
        assert matches == [
            {
                "name": "Mangalore",
                "admin1": "Karnataka",
                "country": "India",
                "country_code": "IN",
                "latitude": 12.87,
                "longitude": 74.88,
            }
        ]

    asyncio.run(exercise())


def test_weather_endpoint_returns_provider_limitations(monkeypatch):
    async def unavailable(location: str, country_code: str | None = None) -> dict:
        assert country_code == "IN"
        raise WeatherProviderError("Weather provider is temporarily unavailable.")

    monkeypatch.setattr(weather_routes, "get_weather_forecast", unavailable)

    async def exercise() -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/api/v1/weather/forecast",
                params={"location": "Mangaluru", "country_code": "IN"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "unavailable"
        assert response.json()["hours"] == []
        assert "temporarily unavailable" in response.json()["notice"]

    asyncio.run(exercise())


def test_weather_location_endpoint_validates_country_code(monkeypatch):
    async def search(query: str, country_code: str) -> list[dict]:
        assert query == "Mang"
        assert country_code == "IN"
        return [{"name": "Mangaluru", "country": "India"}]

    monkeypatch.setattr(weather_routes, "search_weather_locations", search)

    async def exercise() -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/api/v1/weather/locations",
                params={"query": "Mang", "country_code": "IN"},
            )
            invalid = await client.get(
                "/api/v1/weather/locations",
                params={"query": "M", "country_code": "India"},
            )

        assert response.status_code == 200
        assert response.json()["results"][0]["name"] == "Mangaluru"
        assert invalid.status_code == 422

    asyncio.run(exercise())


def test_weather_provider_errors_and_bounded_retries():
    async def exercise() -> None:
        async def request_with(handler):
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                return await _get_json(client, "https://weather.example/test", {})

        rate_limit_calls = 0

        def rate_limited(request: httpx.Request) -> httpx.Response:
            nonlocal rate_limit_calls
            rate_limit_calls += 1
            return httpx.Response(429, json={"message": "too many requests"})

        try:
            await request_with(rate_limited)
        except WeatherProviderError as exc:
            assert "rate limit" in str(exc)
        else:
            raise AssertionError("Expected provider rate-limit handling")
        assert rate_limit_calls == 1

        auth_calls = 0

        def unauthorized(request: httpx.Request) -> httpx.Response:
            nonlocal auth_calls
            auth_calls += 1
            return httpx.Response(401, json={"message": "unauthorized"})

        try:
            await request_with(unauthorized)
        except WeatherProviderError as exc:
            assert str(exc) == "Weather provider returned an error."
        else:
            raise AssertionError("Expected provider authentication failure handling")
        assert auth_calls == 1

        def malformed(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=b"{")

        try:
            await request_with(malformed)
        except WeatherProviderError as exc:
            assert "invalid response" in str(exc)
        else:
            raise AssertionError("Expected malformed provider response handling")

        transient_calls = 0

        def transient(request: httpx.Request) -> httpx.Response:
            nonlocal transient_calls
            transient_calls += 1
            if transient_calls == 1:
                return httpx.Response(503)
            return httpx.Response(200, json={"status": "recovered"})

        assert await request_with(transient) == {"status": "recovered"}
        assert transient_calls == 2

        timeout_calls = 0

        def timeout_then_success(request: httpx.Request) -> httpx.Response:
            nonlocal timeout_calls
            timeout_calls += 1
            if timeout_calls == 1:
                raise httpx.ConnectTimeout("simulated timeout", request=request)
            return httpx.Response(200, json={"status": "recovered"})

        assert await request_with(timeout_then_success) == {"status": "recovered"}
        assert timeout_calls == 2

    asyncio.run(exercise())
