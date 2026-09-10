"""
IBM Langflow RAG Integration
Agricultural knowledge base retrieval with Demo Mode fallback
"""
import os
import httpx
from typing import Optional, List, Dict

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
LANGFLOW_API_URL = os.getenv("LANGFLOW_API_URL", "")
LANGFLOW_API_KEY = os.getenv("LANGFLOW_API_KEY", "")
LANGFLOW_FLOW_ID = os.getenv("LANGFLOW_FLOW_ID", "")

# Agricultural RAG Knowledge Base (in-memory for demo)
RAG_KNOWLEDGE = {
    "tomato_cultivation": """
Tomato Cultivation Guidelines:
- Soil: Well-drained loamy or sandy loam, pH 6.0-7.0
- Temperature: 20-30°C optimal; below 10°C causes chilling injury
- Watering: 25-35mm per week; drip irrigation reduces disease
- Fertilizer: NPK 120:60:60 kg/ha; apply in 3 splits
- Spacing: 60x45 cm for indeterminate varieties
- Flowering stage needs consistent moisture; avoid water stress
- Days to harvest: 60-80 days from transplanting
""",
    "irrigation_practices": """
Irrigation Best Practices:
- Drip irrigation saves 30-50% water vs flood irrigation
- Irrigate when soil moisture drops below 50-60%
- Morning irrigation preferred to reduce evaporation
- Skip irrigation if rain probability > 70%
- Flowering/fruiting stages are most critical for water
- Deficit irrigation during vegetative stage acceptable
- Tensiometer reading: 20-40 cb = adequate moisture
""",
    "pest_management": """
Tomato Pest & Disease Management:
- Early Blight (Alternaria): Brown spots with rings; use Mancozeb/Chlorothalonil
- Late Blight (Phytophthora): Water-soaked lesions; use Metalaxyl
- Leaf Curl Virus: Upward curling, yellow margins; control whiteflies
- Fusarium Wilt: Yellowing, wilting; use resistant varieties
- Tomato Fruitworm: Bore holes; use Spinosad/NPV
- Spider Mites: Stippling on leaves; use Abamectin
- Prevention: Crop rotation, clean seeds, proper spacing
""",
    "fertilizer_guidelines": """
Fertilizer Application Guidelines for Tomato:
- Basal: FYM 25t/ha + SSP 375kg/ha + MOP 100kg/ha
- 15 DAT: Urea 50kg/ha
- 30 DAT: Urea 50kg/ha + MOP 50kg/ha
- 45 DAT: Urea 50kg/ha
- Micronutrients: Boron 1g/L at flowering; Calcium at fruit set
- Fertigation via drip: Soluble NPK 19:19:19 at 5g/L weekly
- Excess nitrogen causes leafy growth, reduces fruit set
""",
    "government_advisories": """
Government Agricultural Advisories (India):
- PM-KISAN: ₹6000/year direct income support
- Pradhan Mantri Fasal Bima Yojana: Crop insurance available
- Minimum Support Price (MSP): Check local APMC for tomato
- eNAM: Online national agriculture market platform
- Kisan Credit Card: Short-term credit at 4% interest
- Soil Health Card: Free soil testing available at KVK
- PMKSY: Drip irrigation subsidy up to 55% for small farmers
""",
    "market_intelligence": """
Tomato Market Intelligence:
- Peak prices: March-May and October-November
- APMC markets offer better prices than local mandis
- Direct selling to supermarkets: 15-20% premium
- Cold storage: Extends shelf life by 2-3 weeks
- Grading increases price by 20-30%
- Online platforms (eNAM): Price discovery + wider market
- Export quality commands 40-50% premium
"""
}


async def query_rag(question: str, context: str = "") -> str:
    """Query the RAG knowledge base via IBM Langflow"""
    if DEMO_MODE or not LANGFLOW_API_KEY or LANGFLOW_API_KEY in ("demo_langflow_key", "your_langflow_api_key_here"):
        return await demo_rag_query(question, context)

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            payload = {
                "input_value": question,
                "output_type": "chat",
                "input_type": "chat",
                "tweaks": {
                    "context": context
                }
            }
            resp = await client.post(
                f"{LANGFLOW_API_URL}/api/v1/run/{LANGFLOW_FLOW_ID}",
                json=payload,
                headers={
                    "Authorization": f"Bearer {LANGFLOW_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("outputs", [{}])[0].get("outputs", [{}])[0].get("results", {}).get("message", {}).get("text", "")
    except Exception as e:
        print(f"Langflow RAG error: {e}")

    return await demo_rag_query(question, context)


async def demo_rag_query(question: str, context: str = "") -> str:
    """Demo RAG using in-memory knowledge base"""
    question_lower = question.lower()

    # Find relevant knowledge
    relevant = []
    if any(w in question_lower for w in ["irrigat", "water", "moisture", "rain"]):
        relevant.append(RAG_KNOWLEDGE["irrigation_practices"])
    if any(w in question_lower for w in ["pest", "disease", "yellow", "blight", "curl", "wilt", "mite", "insect"]):
        relevant.append(RAG_KNOWLEDGE["pest_management"])
    if any(w in question_lower for w in ["fertiliz", "npk", "nitrogen", "phosphor", "potassium", "nutrient"]):
        relevant.append(RAG_KNOWLEDGE["fertilizer_guidelines"])
    if any(w in question_lower for w in ["market", "price", "sell", "profit", "harvest", "revenue"]):
        relevant.append(RAG_KNOWLEDGE["market_intelligence"])
    if any(w in question_lower for w in ["scheme", "subsidy", "insurance", "government", "pmkisan"]):
        relevant.append(RAG_KNOWLEDGE["government_advisories"])
    if any(w in question_lower for w in ["tomato", "cultivat", "grow", "sow", "plant", "stage"]):
        relevant.append(RAG_KNOWLEDGE["tomato_cultivation"])

    if not relevant:
        relevant = list(RAG_KNOWLEDGE.values())[:2]

    return "\n".join(relevant[:2])


def get_knowledge_articles() -> List[Dict]:
    """Return all knowledge base articles"""
    return [
        {
            "title": "Tomato Cultivation Guide",
            "category": "Crop Management",
            "content": RAG_KNOWLEDGE["tomato_cultivation"],
            "icon": "🍅"
        },
        {
            "title": "Irrigation Best Practices",
            "category": "Water Management",
            "content": RAG_KNOWLEDGE["irrigation_practices"],
            "icon": "💧"
        },
        {
            "title": "Pest & Disease Management",
            "category": "Protection",
            "content": RAG_KNOWLEDGE["pest_management"],
            "icon": "🐛"
        },
        {
            "title": "Fertilizer Application Guide",
            "category": "Nutrition",
            "content": RAG_KNOWLEDGE["fertilizer_guidelines"],
            "icon": "🌱"
        },
        {
            "title": "Government Schemes & Subsidies",
            "category": "Finance",
            "content": RAG_KNOWLEDGE["government_advisories"],
            "icon": "🏛️"
        },
        {
            "title": "Market Intelligence",
            "category": "Marketing",
            "content": RAG_KNOWLEDGE["market_intelligence"],
            "icon": "📊"
        }
    ]
