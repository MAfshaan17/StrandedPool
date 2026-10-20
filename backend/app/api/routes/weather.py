import logging

from fastapi import APIRouter, Query

from ...services.weather import (
    WeatherLocationNotFound,
    WeatherProviderError,
    get_weather_forecast,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/v1/weather/forecast", tags=["Weather"])
async def weather_forecast(
    location: str = Query(min_length=2, max_length=120),
):
    try:
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
