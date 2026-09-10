"""
Market Insights Agent
Analyzes market prices, yield forecasts, costs, and expected profit
"""
from typing import Dict, Any, List
from backend.integrations.granite import granite_text_inference
from backend.integrations.langflow import query_rag


DEMO_MARKET_DATA = {
    "current_prices": [
        {"market": "Online (Direct)", "price": 38.0, "trend": "rising", "trend_pct": 12, "distance_km": 0, "transport_cost": 0},
        {"market": "Mumbai Wholesale", "price": 35.0, "trend": "rising", "trend_pct": 8, "distance_km": 165, "transport_cost": 4.5},
        {"market": "Nashik APMC", "price": 32.0, "trend": "rising", "trend_pct": 5, "distance_km": 18, "transport_cost": 1.2},
        {"market": "Pune APMC", "price": 30.0, "trend": "stable", "trend_pct": 0, "distance_km": 210, "transport_cost": 5.8},
        {"market": "Local Market", "price": 28.0, "trend": "stable", "trend_pct": -2, "distance_km": 5, "transport_cost": 0.5},
    ],
    "price_history_7days": {
        "dates": ["Mar 9", "Mar 10", "Mar 11", "Mar 12", "Mar 13", "Mar 14", "Mar 15"],
        "nashik_apmc": [28, 29, 30, 31, 30, 31, 32],
        "mumbai_wholesale": [30, 31, 32, 33, 34, 34, 35],
        "local_market": [24, 25, 26, 27, 27, 28, 28]
    },
    "yield_forecast": {
        "expected_yield_kg": 4200,
        "expected_yield_tons": 4.2,
        "quality_grade_a_pct": 75,
        "quality_grade_b_pct": 25,
        "grade_a_kg": 3150,
        "grade_b_kg": 1050,
        "confidence_pct": 82
    },
    "production_costs": {
        "seeds_seedlings": 3500,
        "fertilizers": 4200,
        "pesticides_fungicides": 2800,
        "irrigation_water": 1200,
        "labor": 8500,
        "land_preparation": 2000,
        "miscellaneous": 1000,
        "total": 23200
    },
    "profit_analysis": {
        "best_market": "Online (Direct)",
        "best_price": 38.0,
        "gross_revenue": 159600,
        "production_cost": 23200,
        "transport_cost": 0,
        "net_profit": 136400,
        "profit_per_acre": 68200,
        "roi_pct": 488,
        "breakeven_price": 5.52
    },
    "market_recommendation": {
        "recommended_market": "Online (Direct) via eNAM",
        "reason": "Highest price at ₹38/kg with no transport cost. Direct farmer-to-buyer connection.",
        "alternative": "Mumbai Wholesale at ₹35/kg for bulk immediate sale",
        "timing": "Sell 60% at harvest in March; hold 40% for 2 weeks when prices peak",
        "grading_benefit": "Grading Grade A separately adds ₹4-6/kg premium"
    },
    "price_prediction": {
        "next_week": 34,
        "next_month": 36,
        "trend": "Prices expected to rise as summer demand increases",
        "risk": "Supply glut possible if Pune/Nashik region has bumper harvest"
    }
}


async def get_market_insights(farm_data: Dict, sensor_data: Dict, market_prices: List[Dict] = None) -> Dict[str, Any]:
    """Get comprehensive market insights and profit analysis"""
    area = farm_data.get("area_acres", 2.0)
    crop = farm_data.get("crop_type", "Tomato")

    # Scale calculations based on actual farm size
    base_yield_per_acre = 2100  # kg per acre for tomato
    expected_yield = base_yield_per_acre * area
    total_cost_per_acre = 11600
    total_cost = total_cost_per_acre * area

    prompt = f"""
You are an agricultural market intelligence expert.
Farm: {area} acres of {crop}
Expected yield: {expected_yield}kg
Production cost: ₹{total_cost}
Current best market price: ₹38/kg (Online/eNAM)

Provide: best market recommendation, expected profit, selling strategy, and price prediction.
"""

    ai_response = await granite_text_inference(prompt)

    # Update numbers based on actual farm size
    result = {
        "source": "Demo Mode",
        **DEMO_MARKET_DATA
    }

    # Scale yield and profits
    scale_factor = area / 2.0
    result["yield_forecast"]["expected_yield_kg"] = int(expected_yield)
    result["yield_forecast"]["expected_yield_tons"] = round(expected_yield / 1000, 1)
    result["yield_forecast"]["grade_a_kg"] = int(expected_yield * 0.75)
    result["yield_forecast"]["grade_b_kg"] = int(expected_yield * 0.25)
    result["production_costs"]["total"] = int(total_cost)
    result["profit_analysis"]["gross_revenue"] = int(expected_yield * 38)
    result["profit_analysis"]["production_cost"] = int(total_cost)
    result["profit_analysis"]["net_profit"] = int(expected_yield * 38 - total_cost)
    result["profit_analysis"]["profit_per_acre"] = int((expected_yield * 38 - total_cost) / area)
    result["profit_analysis"]["breakeven_price"] = round(total_cost / expected_yield, 2)

    if market_prices:
        result["current_prices"] = [
            {
                "market": m["market_name"],
                "price": m["price_per_kg"],
                "trend": m.get("trend", "stable"),
                "trend_pct": 5 if m.get("trend") == "rising" else 0,
                "distance_km": 0,
                "transport_cost": 0
            }
            for m in market_prices
        ]

    if ai_response:
        result["source"] = "IBM Granite AI"
        result["ai_insights"] = ai_response

    return result
