import logging

from fastapi import APIRouter, HTTPException, Query

from ...services.weather import (
    WeatherLocationNotFound,
    WeatherProviderError,
    get_weather_forecast,
    search_weather_locations,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/v1/weather/forecast", tags=["Weather"])
async def weather_forecast(
    location: str = Query(min_length=2, max_length=120),
    country_code: str | None = Query(default=None, min_length=2, max_length=2, pattern="^[A-Za-z]{2}$"),
):
    try:
        if country_code:
            return await get_weather_forecast(location, country_code=country_code)
        return await get_weather_forecast(location)
    except WeatherLocationNotFound as exc:
        return {
            "status": "unavailable",
            "source": "Open-Meteo",
            "location_query": location,
            "data_freshness": "No forecast",
            "hours": [],
            "risk": None,
            "notice": str(exc),
        }
    except WeatherProviderError as exc:
        logger.warning("Weather forecast unavailable for query %r: %s", location, exc)
        return {
            "status": "unavailable",
            "source": "Open-Meteo",
            "location_query": location,
            "data_freshness": "No forecast",
            "hours": [],
            "risk": None,
            "notice": str(exc),
        }


@router.get("/v1/weather/locations", tags=["Weather"])
async def weather_locations(
    query: str = Query(min_length=2, max_length=80),
    country_code: str = Query(min_length=2, max_length=2, pattern="^[A-Za-z]{2}$"),
):
    try:
        results = await search_weather_locations(query, country_code)
    except WeatherProviderError as exc:
        logger.warning("Weather location search unavailable: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"source": "Open-Meteo geocoding", "results": results}
