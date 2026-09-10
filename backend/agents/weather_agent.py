"""
Weather & Irrigation Agent
Analyzes weather, schedules irrigation, and saves water
"""
from typing import Dict, Any, List
from backend.integrations.granite import granite_text_inference
from backend.integrations.langflow import query_rag
from datetime import datetime, timedelta
import random


DEMO_WEATHER = {
    "current": {
        "temperature": 29,
        "humidity": 68,
        "wind_speed": 12,
        "rain_probability": 72,
        "condition": "Partly Cloudy",
        "uv_index": 7,
        "feels_like": 32
    },
    "forecast_7day": [
        {"day": "Today", "high": 29, "low": 22, "rain_prob": 72, "condition": "Partly Cloudy", "icon": "⛅"},
        {"day": "Tomorrow", "high": 27, "low": 20, "rain_prob": 85, "condition": "Rain", "icon": "🌧️"},
        {"day": "Wed", "high": 25, "low": 19, "rain_prob": 60, "condition": "Drizzle", "icon": "🌦️"},
        {"day": "Thu", "high": 28, "low": 21, "rain_prob": 30, "condition": "Sunny", "icon": "☀️"},
        {"day": "Fri", "high": 31, "low": 23, "rain_prob": 15, "condition": "Sunny", "icon": "☀️"},
        {"day": "Sat", "high": 30, "low": 22, "rain_prob": 20, "condition": "Partly Cloudy", "icon": "⛅"},
        {"day": "Sun", "high": 32, "low": 24, "rain_prob": 10, "condition": "Sunny", "icon": "☀️"},
    ]
}

DEMO_IRRIGATION = {
    "recommendation": "SKIP TODAY",
    "reason": "Rain probability is 72% — natural irrigation expected. Resume irrigation Thursday if no rain.",
    "next_irrigation": "Thursday, if no rain Wednesday",
    "water_needed_liters": 0,
    "water_saved_liters": 480,
    "schedule": [
        {"day": "Today (Mon)", "action": "SKIP", "reason": "72% rain probability", "liters": 0},
        {"day": "Tuesday", "action": "SKIP", "reason": "85% rain — definite rain", "liters": 0},
        {"day": "Wednesday", "action": "MONITOR", "reason": "Check soil moisture post rain", "liters": 0},
        {"day": "Thursday", "action": "IRRIGATE", "reason": "Soil likely dry after rain", "liters": 480},
        {"day": "Friday", "action": "IRRIGATE", "reason": "Hot & sunny forecast", "liters": 480},
        {"day": "Saturday", "action": "HALF", "reason": "Moderate conditions", "liters": 240},
        {"day": "Sunday", "action": "IRRIGATE", "reason": "High temperature expected", "liters": 480},
    ],
    "tips": [
        "Drip irrigation reduces water use by 40% vs flood irrigation",
        "Early morning irrigation (5-7 AM) minimizes evaporation loss",
        "Use mulching to reduce soil evaporation by 30%",
        "Install tensiometer to automate irrigation decisions"
    ],
    "weekly_water_budget": {
        "baseline_liters": 3360,
        "optimized_liters": 1680,
        "savings_pct": 50,
        "cost_saved": 168
    }
}


async def get_weather_analysis(sensor_data: Dict) -> Dict[str, Any]:
    """Get weather analysis and irrigation schedule"""
    rain_prob = sensor_data.get("rain_probability", 72)
    soil_moisture = sensor_data.get("soil_moisture", 61)
    temp = sensor_data.get("temperature", 29)

    # Smart irrigation logic
    irrigate_today = rain_prob < 40 and soil_moisture < 55

    prompt = f"""
You are a precision irrigation expert for Indian farmers.
Current soil moisture: {soil_moisture}%
Rain probability today: {rain_prob}%
Temperature: {temp}°C
Crop: Tomato at Flowering stage
Irrigation type: Drip

Should the farmer irrigate today? Give specific recommendation with water amount and timing.
"""
    ai_response = await granite_text_inference(prompt)

    result = {"source": "Demo Mode", **DEMO_WEATHER, "irrigation": DEMO_IRRIGATION}

    if rain_prob > 60:
        result["irrigation"]["recommendation"] = "SKIP TODAY"
        result["irrigation"]["reason"] = f"Rain probability is {rain_prob}% — skip irrigation to save water"
        result["irrigation"]["water_saved_liters"] = 480
    elif soil_moisture > 65:
        result["irrigation"]["recommendation"] = "SKIP TODAY"
        result["irrigation"]["reason"] = f"Soil moisture is adequate at {soil_moisture}% — no irrigation needed"
        result["irrigation"]["water_saved_liters"] = 480
    else:
        result["irrigation"]["recommendation"] = "IRRIGATE TODAY"
        result["irrigation"]["reason"] = f"Soil moisture low ({soil_moisture}%) with only {rain_prob}% rain chance"
        result["irrigation"]["water_needed_liters"] = 480

    if ai_response:
        result["source"] = "IBM Granite AI"
        result["ai_analysis"] = ai_response

    return result
