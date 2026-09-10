"""
Ask FarmTwin - AI Chatbot
Answers farmer questions using RAG knowledge + farm context
"""
from typing import Dict, Any, List
from backend.integrations.granite import granite_text_inference
from backend.integrations.langflow import query_rag


DEMO_RESPONSES = {
    "irrigate": {
        "keywords": ["irrigate", "water", "irrigation", "moisture", "watering"],
        "response": """**Today's Irrigation Recommendation: SKIP**

Based on your farm data:
- 🌧️ Rain probability is **72%** — high chance of natural rainfall
- 💧 Current soil moisture: **61%** (adequate for Tomato at flowering stage)
- 🌡️ Temperature: 29°C (moderate evapotranspiration)

**Recommendation:** Skip irrigation today and tomorrow. Resume Thursday if soil moisture drops below 55%.

**Water Saved:** ~480 liters per irrigation session (~₹48 savings)

**Pro Tip:** Your drip irrigation system already saves 40% water vs flood irrigation. Install a soil moisture sensor for automated precision irrigation! 🎯"""
    },
    "yellow_leaves": {
        "keywords": ["yellow", "yellowing", "leaves turning", "leaf color", "pale"],
        "response": """**Diagnosis: Yellow Leaves on Tomato**

Based on your flowering-stage tomato farm, yellowing leaves can indicate:

**Most Likely Cause (80% probability):** 
🍃 **Nitrogen Deficiency** — Your N level is 42 (borderline low). Lower leaves yellow first when N is deficient.

**Other Possibilities:**
- Early Blight (*Alternaria solani*) — brown spots + yellow halo
- Magnesium deficiency — interveinal chlorosis
- Overwatering or root rot

**Recommended Actions:**
1. Apply **Urea 2% foliar spray** (20g in 1L water) on yellowing leaves immediately
2. Check for brown spots — if present, apply Mancozeb 2g/L
3. Ensure proper drainage — waterlogged roots cause yellowing
4. Add Magnesium Sulphate 5g/L if interveinal pattern

**Upload a photo** to get AI-powered diagnosis with exact confidence! 📸"""
    },
    "harvest": {
        "keywords": ["harvest", "when to harvest", "harvesting", "ready", "pick"],
        "response": """**Harvest Planning for Your Tomato Farm**

📅 **Expected Harvest Date:** April 15, 2024 (**42 days remaining**)

**Harvest Readiness Signs:**
- Fruit color turns red-orange (75% red coloration)
- Slight softness when pressed gently
- Brix (sugar content) > 4.5 (use refractometer)
- Fruit detaches easily from vine

**Harvest Strategy:**
- Pick in 2-3 batches over 10-14 days for maximum marketability
- Harvest early morning (5-8 AM) to reduce field heat damage
- Grade A (firm, 80-100g) for direct market/export
- Grade B for local markets or processing

**Expected Yield:** 4.2 tons (Grade A: 3.15 tons, Grade B: 1.05 tons)

**💰 Market Timing:** March-May is peak tomato season. Your harvest timing is EXCELLENT for maximum prices! Current price: ₹30/kg, expected at harvest: ₹32-38/kg"""
    },
    "market": {
        "keywords": ["market", "price", "profit", "sell", "selling", "revenue", "income"],
        "response": """**Market Intelligence for Your Tomato Crop**

**Best Markets (Highest to Lowest Price):**

| Market | Price/kg | Net Profit |
|--------|----------|-----------|
| 🥇 Online (eNAM) | ₹38 | ₹1,36,400 |
| 🥈 Mumbai Wholesale | ₹35 | ₹1,23,800 |
| 🥉 Nashik APMC | ₹32 | ₹1,11,200 |
| Local Market | ₹28 | ₹94,400 |

**My Recommendation: Sell via eNAM (Online National Agriculture Market)**
- Register at enam.gov.in (free registration)
- Upload produce listing with photos
- Buyers bid directly — best price discovery
- Payment within 24 hours

**Expected Profit at Best Price:** ₹1,36,400 (488% ROI!)

**Tip:** Grade your tomatoes before selling — Grade A commands ₹5-8/kg premium!"""
    },
    "fertilizer": {
        "keywords": ["fertiliz", "npk", "nutrient", "urea", "potassium", "nitrogen", "feed"],
        "response": """**Fertilizer Recommendation for Flowering Tomato**

Your crop is at **Flowering Stage** — this is the most critical nutrition window!

**Current NPK Status:**
- Nitrogen (N): 42 ⚠️ (slightly low — target 50+)
- Phosphorus (P): 38 ✅ (adequate)
- Potassium (K): 55 ✅ (good)

**Recommended Fertigation (This Week):**
1. **NPK 0:52:34** @ 5g/L — 2x per week via drip
2. **Calcium Nitrate** @ 2g/L — weekly spray on leaves
3. **Boron** @ 1g/L — once for better fruit set

**Why Potassium Now?**
Flowering and fruit set demand high K for:
- Cell division in fruits
- Sugar transport (better Brix)
- Disease resistance

**Avoid:** High Nitrogen now — causes leafy growth, reduces fruit set!

**Cost:** ~₹800 for 1 week fertigation schedule"""
    },
    "default": {
        "response": """**FarmTwin AI Assistant** 🌾

I'm here to help with your 2-acre tomato farm in Nashik, Maharashtra!

**You can ask me about:**
- 💧 "Should I irrigate today?"
- 🍃 "Why are my leaves turning yellow?"
- 📅 "When should I harvest?"
- 💰 "Which market gives me highest profit?"
- 🌱 "What fertilizer should I apply?"
- 🐛 "How to control Early Blight?"
- 🌤️ "What's the weather forecast?"
- 📊 "What's my expected profit?"

**Current Farm Status:**
- Crop: Tomato | Stage: Flowering | Health: 78/100
- Soil Moisture: 61% | Temperature: 29°C
- Pest Risk: 34% (Moderate) | Rain: 72% chance

*Ask me anything about your farm!* 🌿"""
    }
}


async def chat_with_farmtwin(
    message: str,
    farm_data: Dict,
    sensor_data: Dict,
    chat_history: List[Dict] = None
) -> Dict[str, Any]:
    """Process farmer's question and return AI response"""

    message_lower = message.lower()

    # Build context from farm data
    farm_context = f"""
Farm: {farm_data.get('name', 'Green Valley Farm')}
Farmer: {farm_data.get('farmer_name', 'Rajesh Kumar')}
Crop: {farm_data.get('crop_type', 'Tomato')}, {farm_data.get('area_acres', 2)} acres
Stage: {farm_data.get('crop_stage', 'Flowering')}
Soil: {farm_data.get('soil_type', 'Loamy')}
Irrigation: {farm_data.get('irrigation_type', 'Drip')}
Location: {farm_data.get('location', 'Nashik, Maharashtra')}
Temperature: {sensor_data.get('temperature', 29)}°C
Soil Moisture: {sensor_data.get('soil_moisture', 61)}%
Humidity: {sensor_data.get('humidity', 68)}%
Rain Probability: {sensor_data.get('rain_probability', 72)}%
NPK: N={sensor_data.get('nitrogen', 42)}, P={sensor_data.get('phosphorus', 38)}, K={sensor_data.get('potassium', 55)}
"""

    # Get RAG knowledge
    rag_knowledge = await query_rag(message, farm_context)

    # Build prompt for Granite
    prompt = f"""
You are FarmTwin AI — an expert agricultural advisor for Indian farmers.
Be specific, practical, and use the farmer's actual data in your response.

{farm_context}

Agricultural Knowledge:
{rag_knowledge}

Farmer's Question: {message}

Provide a helpful, specific answer using the farm data above. Use bullet points and be concise.
"""

    # Try IBM Granite first
    ai_response = await granite_text_inference(prompt, max_tokens=400)

    if ai_response:
        return {
            "response": ai_response,
            "source": "IBM Granite AI + RAG",
            "farm_context_used": True
        }

    # Demo mode: use pre-built responses
    for key, data in DEMO_RESPONSES.items():
        if key == "default":
            continue
        keywords = data.get("keywords", [])
        if any(kw in message_lower for kw in keywords):
            return {
                "response": data["response"],
                "source": "Demo Mode (FarmTwin AI)",
                "farm_context_used": True
            }

    return {
        "response": DEMO_RESPONSES["default"]["response"],
        "source": "Demo Mode (FarmTwin AI)",
        "farm_context_used": True
    }
