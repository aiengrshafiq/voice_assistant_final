import requests
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

def get_current_weather(city="Dubai", units="metric"):
    try:
        if not settings.WEATHER_API_KEY:
            return "Weather service is not configured."

        url = f"https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": settings.WEATHER_API_KEY,
            "units": units
        }

        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code != 200:
            logger.error(f"Weather API error: {data}")
            return "Could not fetch weather at this time."

        desc = data['weather'][0]['description']
        temp = data['main']['temp']
        return f"The current weather in {city} is {desc} with a temperature of {round(temp)}°C."

    except Exception as e:
        logger.exception("Weather retrieval failed.")
        return "I'm unable to retrieve the weather right now."
