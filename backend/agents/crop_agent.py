"""
Crop Advisory Agent
Provides advice on crop care, seeds, fertilizers, and harvesting
"""
from typing import Dict, Any
from backend.integrations.granite import granite_text_inference
from backend.integrations.langflow import query_rag


DEMO_CROP_ADVICE = {
    "current_status": {
        "stage": "Flowering",
        "health_score": 78,
        "days_to_harvest": 42,
        "growth_rate": "Normal",
        "leaf_color": "Green with slight yellowing on lower leaves"
    },
    "fertilizer_recommendation": {
        "current_need": "Potassium & Calcium boost needed",
        "product": "NPK 0:0:50 + Calcium Nitrate",
        "dose": "5g/L via fertigation",
        "timing": "Apply every 7 days during flowering",
        "reason": "Flowering stage demands high K for fruit set and Ca to prevent blossom end rot"
    },
    "seed_insights": {
        "variety": "Hybrid F1 (Arka Vikas)",
        "germination_rate": "94%",
        "days_planted": 48,
        "recommendation": "No re-sowing needed; monitor for uniform growth"
    },
    "harvest_forecast": {
        "expected_date": "April 15, 2024",
        "days_remaining": 42,
        "expected_yield_tons": 4.2,
        "quality_grade": "Grade A (75%), Grade B (25%)",
        "harvest_signal": "Fruit turns red-orange; Brix > 4.5"
    },
    "actions": [
        "Apply Calcium Nitrate 2g/L spray on lower leaves to fix yellowing",
        "Continue regular drip fertigation every alternate day",
        "Remove suckers below first fruit cluster to improve airflow",
        "Stake plants properly — flowering stage weight increases",
        "Scout for fruit borers every 3 days during flowering"
    ]
}


async def get_crop_advice(farm_data: Dict, sensor_data: Dict) -> Dict[str, Any]:
    """Get comprehensive crop advisory"""
    prompt = f"""
You are an expert crop advisor for Indian farmers.
Farm: {farm_data.get('crop_type', 'Tomato')}, {farm_data.get('area_acres', 2)} acres
Stage: {farm_data.get('crop_stage', 'Flowering')}
Soil: {farm_data.get('soil_type', 'Loamy')}
Temperature: {sensor_data.get('temperature', 29)}°C
Soil Moisture: {sensor_data.get('soil_moisture', 61)}%
NPK: N={sensor_data.get('nitrogen', 42)}, P={sensor_data.get('phosphorus', 38)}, K={sensor_data.get('potassium', 55)}

Provide crop advisory with: current status, fertilizer needs, harvest forecast, and 5 specific actions.
Keep response concise and actionable for a farmer.
"""
    rag_context = await query_rag(f"crop advice for {farm_data.get('crop_type', 'tomato')} at {farm_data.get('crop_stage', 'flowering')} stage")
    
    ai_response = await granite_text_inference(prompt + f"\n\nKnowledge: {rag_context}")
    
    if ai_response:
        return {"source": "IBM Granite AI", "advice": ai_response, **DEMO_CROP_ADVICE}
    
    return {"source": "Demo Mode", **DEMO_CROP_ADVICE}
