"""
FarmTwin Decision Engine
Central orchestrator combining all 4 AI agents
Generates Farm Health Score, Today's Actions, Risk Alerts, and more
"""
from typing import Dict, Any, List
from backend.agents.crop_agent import get_crop_advice
from backend.agents.weather_agent import get_weather_analysis
from backend.agents.pest_agent import get_pest_risk_score
from backend.agents.market_agent import get_market_insights
from backend.integrations.granite import granite_text_inference
from backend.integrations.langflow import query_rag
import asyncio


async def compute_farm_health_score(sensor_data: Dict, pest_risk: Dict, weather: Dict) -> int:
    """Compute overall farm health score 0-100"""
    score = 100

    # Soil moisture penalty
    moisture = sensor_data.get("soil_moisture", 61)
    if moisture < 40:
        score -= 20
    elif moisture < 50:
        score -= 10
    elif moisture > 85:
        score -= 8

    # Temperature penalty
    temp = sensor_data.get("temperature", 29)
    if temp > 38 or temp < 15:
        score -= 15
    elif temp > 34:
        score -= 8

    # Pest risk penalty
    pest_score = pest_risk.get("risk_score", 34)
    score -= int(pest_score * 0.25)

    # pH penalty
    ph = sensor_data.get("ph_level", 6.8)
    if ph < 5.5 or ph > 7.5:
        score -= 10
    elif ph < 6.0 or ph > 7.2:
        score -= 5

    # NPK penalty
    n = sensor_data.get("nitrogen", 42)
    if n < 30:
        score -= 8

    return max(min(score, 100), 0)


async def compute_sustainability_score(farm_data: Dict, sensor_data: Dict, irrigation_saved: float = 0) -> int:
    """Compute sustainability score"""
    score = 50

    # Drip irrigation bonus
    if farm_data.get("irrigation_type", "").lower() in ("drip", "drip irrigation"):
        score += 20

    # Water saving bonus
    if irrigation_saved > 0:
        score += min(15, int(irrigation_saved / 100))

    # Soil health
    ph = sensor_data.get("ph_level", 6.8)
    if 6.0 <= ph <= 7.0:
        score += 10

    return min(score, 100)


async def generate_todays_actions(
    sensor_data: Dict, pest_risk: Dict, weather: Dict, crop_advice: Dict
) -> List[Dict]:
    """Generate prioritized today's action list"""
    actions = []

    rain_prob = sensor_data.get("rain_probability", 72)
    soil_moisture = sensor_data.get("soil_moisture", 61)
    pest_score = pest_risk.get("risk_score", 34)
    temp = sensor_data.get("temperature", 29)

    # Irrigation action
    if rain_prob > 60:
        actions.append({
            "priority": "medium",
            "category": "Irrigation",
            "icon": "💧",
            "action": "Skip irrigation today",
            "reason": f"Rain probability is {rain_prob}% — save water",
            "impact": f"Save ~480L water"
        })
    elif soil_moisture < 50:
        actions.append({
            "priority": "high",
            "category": "Irrigation",
            "icon": "💧",
            "action": "Irrigate immediately",
            "reason": f"Soil moisture critically low at {soil_moisture}%",
            "impact": "Prevent crop stress"
        })
    else:
        actions.append({
            "priority": "low",
            "category": "Irrigation",
            "icon": "💧",
            "action": "Monitor soil moisture",
            "reason": f"Adequate moisture at {soil_moisture}%",
            "impact": "Maintain optimal growing conditions"
        })

    # Pest action
    if pest_score > 60:
        actions.append({
            "priority": "high",
            "category": "Pest Management",
            "icon": "🐛",
            "action": "Apply preventive fungicide spray",
            "reason": f"High disease risk ({pest_score}%) due to humidity + temperature",
            "impact": "Prevent Early Blight outbreak"
        })
    elif pest_score > 35:
        actions.append({
            "priority": "medium",
            "category": "Pest Management",
            "icon": "🐛",
            "action": "Scout for pests and diseases",
            "reason": f"Moderate pest risk ({pest_score}%) — monitor closely",
            "impact": "Early detection saves 30% crop loss"
        })

    # Fertilizer action
    n = sensor_data.get("nitrogen", 42)
    if n < 40:
        actions.append({
            "priority": "medium",
            "category": "Fertilizer",
            "icon": "🌱",
            "action": "Apply NPK 0:0:50 + Calcium Nitrate via fertigation",
            "reason": "Flowering stage needs Potassium boost for fruit set",
            "impact": "Improve fruit quality and yield by 15%"
        })

    # Temperature action
    if temp > 34:
        actions.append({
            "priority": "high",
            "category": "Heat Management",
            "icon": "🌡️",
            "action": "Apply shade net and increase irrigation frequency",
            "reason": f"Temperature at {temp}°C — heat stress risk",
            "impact": "Prevent flower drop and yield loss"
        })

    # Market action
    actions.append({
        "priority": "low",
        "category": "Market",
        "icon": "📊",
        "action": "Register on eNAM (Online Agriculture Market)",
        "reason": "Online prices (₹38/kg) are ₹10 higher than local market",
        "impact": "Extra ₹42,000 profit on 2-acre yield"
    })

    return sorted(actions, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["priority"]])


async def generate_risk_alerts(sensor_data: Dict, pest_risk: Dict, weather: Dict) -> List[Dict]:
    """Generate risk alerts"""
    alerts = []

    rain_prob = sensor_data.get("rain_probability", 72)
    pest_score = pest_risk.get("risk_score", 34)
    temp = sensor_data.get("temperature", 29)
    humidity = sensor_data.get("humidity", 68)
    moisture = sensor_data.get("soil_moisture", 61)

    if rain_prob > 70:
        alerts.append({
            "type": "weather",
            "level": "warning",
            "title": "Heavy Rain Expected",
            "message": f"{rain_prob}% rain probability tomorrow — ensure proper drainage",
            "action": "Clear drainage channels; skip irrigation"
        })

    if pest_score > 50:
        alerts.append({
            "type": "pest",
            "level": "danger",
            "title": "High Disease Risk",
            "message": f"Conditions favorable for Early Blight (temp {temp}°C, humidity {humidity}%)",
            "action": "Apply Mancozeb 2g/L spray preventively"
        })
    elif pest_score > 30:
        alerts.append({
            "type": "pest",
            "level": "warning",
            "title": "Moderate Pest Risk",
            "message": f"Scout for pests — {', '.join(pest_risk.get('high_risk_diseases', ['Early Blight']))}",
            "action": "Increase scouting frequency to daily"
        })

    if temp > 33:
        alerts.append({
            "type": "weather",
            "level": "warning",
            "title": "Heat Stress Alert",
            "message": f"Temperature {temp}°C may cause flower drop",
            "action": "Install shade net; irrigate at 6 AM"
        })

    if moisture < 45:
        alerts.append({
            "type": "irrigation",
            "level": "danger",
            "title": "Critical Water Stress",
            "message": f"Soil moisture at {moisture}% — crop stress imminent",
            "action": "Irrigate immediately with 480L"
        })

    return alerts


async def run_decision_engine(farm_data: Dict, sensor_data: Dict, market_prices: List[Dict] = None) -> Dict[str, Any]:
    """
    Main FarmTwin Decision Engine
    Orchestrates all 4 agents and generates comprehensive farm report
    """
    # Run all agents concurrently (watsonx Orchestrate pattern)
    crop_task = get_crop_advice(farm_data, sensor_data)
    weather_task = get_weather_analysis(sensor_data)
    pest_task = get_pest_risk_score(sensor_data, farm_data)
    market_task = get_market_insights(farm_data, sensor_data, market_prices)

    crop_advice, weather_analysis, pest_risk, market_insights = await asyncio.gather(
        crop_task, weather_task, pest_task, market_task
    )

    # Compute scores
    health_score = await compute_farm_health_score(sensor_data, pest_risk, weather_analysis)
    sustainability_score = await compute_sustainability_score(
        farm_data, sensor_data,
        weather_analysis.get("irrigation", {}).get("water_saved_liters", 0)
    )

    # Generate actions and alerts
    todays_actions = await generate_todays_actions(sensor_data, pest_risk, weather_analysis, crop_advice)
    risk_alerts = await generate_risk_alerts(sensor_data, pest_risk, weather_analysis)

    # 7-day farm timeline
    timeline = generate_7day_timeline(sensor_data, crop_advice)

    return {
        "farm_health_score": health_score,
        "sustainability_score": sustainability_score,
        "crop_health": get_health_label(health_score),
        "soil_moisture": sensor_data.get("soil_moisture", 61),
        "temperature": sensor_data.get("temperature", 29),
        "rain_probability": sensor_data.get("rain_probability", 72),
        "humidity": sensor_data.get("humidity", 68),
        "pest_risk": pest_risk.get("risk_score", 34),
        "pest_risk_level": pest_risk.get("risk_level", "Medium"),
        "current_market_price": 30.0,
        "best_market_price": 38.0,
        "expected_yield_tons": market_insights.get("yield_forecast", {}).get("expected_yield_tons", 4.2),
        "expected_profit": market_insights.get("profit_analysis", {}).get("net_profit", 136400),
        "irrigation_recommendation": weather_analysis.get("irrigation", {}).get("recommendation", "SKIP TODAY"),
        "irrigation_reason": weather_analysis.get("irrigation", {}).get("reason", ""),
        "pest_disease_status": get_pest_status(pest_risk),
        "todays_actions": todays_actions,
        "risk_alerts": risk_alerts,
        "timeline_7day": timeline,
        "crop_advice": crop_advice,
        "weather_analysis": weather_analysis,
        "pest_analysis": pest_risk,
        "market_insights": market_insights,
        "agents_used": [
            "Crop Advisory Agent",
            "Weather & Irrigation Agent",
            "Pest/Disease Agent",
            "Market Insights Agent"
        ],
        "orchestration": "IBM watsonx Orchestrate (Demo Mode)"
    }


def get_health_label(score: int) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 65:
        return "Good"
    elif score >= 50:
        return "Fair"
    elif score >= 35:
        return "Poor"
    return "Critical"


def get_pest_status(pest_risk: Dict) -> str:
    level = pest_risk.get("risk_level", "Medium")
    diseases = pest_risk.get("high_risk_diseases", [])
    if level == "Low":
        return "Healthy - No active threats"
    elif level == "Medium":
        diseases_str = ", ".join(diseases[:2]) if diseases else "Early Blight"
        return f"Monitor - Risk of {diseases_str}"
    elif level == "High":
        return "Alert - Preventive spray needed"
    return "Critical - Immediate action required"


def generate_7day_timeline(sensor_data: Dict, crop_advice: Dict) -> List[Dict]:
    """Generate 7-day farm activity timeline"""
    rain_prob = sensor_data.get("rain_probability", 72)

    return [
        {
            "day": "Today (Mon)",
            "date": "Mar 15",
            "tasks": ["Skip irrigation (72% rain)", "Scout for pests", "Fertigation - Calcium Nitrate"],
            "weather": "⛅ 29°C / Rain 72%",
            "priority": "medium"
        },
        {
            "day": "Tuesday",
            "date": "Mar 16",
            "tasks": ["Heavy rain expected — no action needed", "Check for waterlogging"],
            "weather": "🌧️ 27°C / Rain 85%",
            "priority": "low"
        },
        {
            "day": "Wednesday",
            "date": "Mar 17",
            "tasks": ["Check soil moisture post rain", "Apply fungicide if humidity >80%", "Scout for blight"],
            "weather": "🌦️ 25°C / Rain 60%",
            "priority": "medium"
        },
        {
            "day": "Thursday",
            "date": "Mar 18",
            "tasks": ["Resume drip irrigation (480L)", "Staking and pruning suckers", "NPK fertigation"],
            "weather": "☀️ 28°C / Rain 30%",
            "priority": "high"
        },
        {
            "day": "Friday",
            "date": "Mar 19",
            "tasks": ["Irrigate full schedule", "Apply Mancozeb spray (preventive)", "Monitor fruit development"],
            "weather": "☀️ 31°C / Rain 15%",
            "priority": "high"
        },
        {
            "day": "Saturday",
            "date": "Mar 20",
            "tasks": ["Half irrigation", "Weekly soil moisture check", "Record pest observations"],
            "weather": "⛅ 30°C / Rain 20%",
            "priority": "medium"
        },
        {
            "day": "Sunday",
            "date": "Mar 21",
            "tasks": ["Full irrigation", "Check market prices on eNAM", "Plan week ahead"],
            "weather": "☀️ 32°C / Rain 10%",
            "priority": "medium"
        }
    ]
