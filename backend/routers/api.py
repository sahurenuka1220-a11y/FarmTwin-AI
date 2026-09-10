"""
Main FastAPI API Router
All API endpoints for FarmTwin AI
"""
import os
import json
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database.models import (
    get_db, Farm, SensorReading, PestDetection,
    MarketPrice, ChatHistory, WhatIfScenario
)
from backend.agents.decision_engine import run_decision_engine
from backend.agents.chatbot_agent import chat_with_farmtwin
from backend.agents.pest_agent import analyze_crop_image
from backend.agents.whatif_simulator import calculate_whatif
from backend.integrations.langflow import get_knowledge_articles

router = APIRouter()
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"


# ─── Pydantic Models ──────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    farm_id: int = 1

class WhatIfRequest(BaseModel):
    irrigation_pct: float = 100.0
    fertilizer_amount_pct: float = 100.0
    harvest_days_offset: int = 0
    selling_market: str = "Local Market"
    area_acres: float = 2.0

class FarmUpdate(BaseModel):
    name: Optional[str] = None
    farmer_name: Optional[str] = None
    location: Optional[str] = None
    area_acres: Optional[float] = None
    crop_type: Optional[str] = None
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    crop_stage: Optional[str] = None

class SensorUpdate(BaseModel):
    soil_moisture: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    rain_probability: Optional[float] = None
    wind_speed: Optional[float] = None
    ph_level: Optional[float] = None
    nitrogen: Optional[float] = None
    phosphorus: Optional[float] = None
    potassium: Optional[float] = None


def get_farm_and_sensor(db: Session, farm_id: int = 1):
    """Helper to get farm and latest sensor data"""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        farm = Farm()
    sensor = db.query(SensorReading).filter(
        SensorReading.farm_id == farm_id
    ).order_by(SensorReading.timestamp.desc()).first()
    if not sensor:
        sensor = SensorReading()

    farm_dict = {k: v for k, v in farm.__dict__.items() if not k.startswith("_")}
    sensor_dict = {k: v for k, v in sensor.__dict__.items() if not k.startswith("_")}
    return farm_dict, sensor_dict


# ─── Dashboard & Decision Engine ──────────────────────────────────────────────

@router.get("/api/dashboard")
async def get_dashboard(farm_id: int = 1, db: Session = Depends(get_db)):
    """Get full dashboard data from FarmTwin Decision Engine"""
    farm_dict, sensor_dict = get_farm_and_sensor(db, farm_id)
    market_prices = db.query(MarketPrice).filter(
        MarketPrice.crop_type == farm_dict.get("crop_type", "Tomato")
    ).all()
    market_list = [
        {"market_name": m.market_name, "price_per_kg": m.price_per_kg, "trend": m.trend}
        for m in market_prices
    ]

    result = await run_decision_engine(farm_dict, sensor_dict, market_list)
    result["demo_mode"] = DEMO_MODE
    result["farm"] = farm_dict
    result["sensors"] = sensor_dict
    return result


# ─── Farm Management ──────────────────────────────────────────────────────────

@router.get("/api/farm/{farm_id}")
async def get_farm(farm_id: int = 1, db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return {k: v for k, v in farm.__dict__.items() if not k.startswith("_")}


@router.put("/api/farm/{farm_id}")
async def update_farm(farm_id: int, update: FarmUpdate, db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    for k, v in update.dict(exclude_none=True).items():
        setattr(farm, k, v)
    farm.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(farm)
    return {"success": True, "farm": {k: v for k, v in farm.__dict__.items() if not k.startswith("_")}}


@router.get("/api/sensors/{farm_id}")
async def get_sensors(farm_id: int = 1, db: Session = Depends(get_db)):
    sensor = db.query(SensorReading).filter(
        SensorReading.farm_id == farm_id
    ).order_by(SensorReading.timestamp.desc()).first()
    if not sensor:
        return SensorReading().__dict__
    return {k: v for k, v in sensor.__dict__.items() if not k.startswith("_")}


@router.put("/api/sensors/{farm_id}")
async def update_sensors(farm_id: int, update: SensorUpdate, db: Session = Depends(get_db)):
    sensor = db.query(SensorReading).filter(
        SensorReading.farm_id == farm_id
    ).order_by(SensorReading.timestamp.desc()).first()
    if sensor:
        for k, v in update.dict(exclude_none=True).items():
            setattr(sensor, k, v)
        sensor.timestamp = datetime.utcnow()
    else:
        sensor = SensorReading(farm_id=farm_id)
        for k, v in update.dict(exclude_none=True).items():
            setattr(sensor, k, v)
        db.add(sensor)
    db.commit()
    return {"success": True}


# ─── Chatbot ──────────────────────────────────────────────────────────────────

@router.post("/api/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Ask FarmTwin AI chatbot"""
    farm_dict, sensor_dict = get_farm_and_sensor(db, request.farm_id)

    # Get chat history
    history = db.query(ChatHistory).filter(
        ChatHistory.farm_id == request.farm_id
    ).order_by(ChatHistory.timestamp.desc()).limit(5).all()
    history_list = [
        {"user": h.user_message, "ai": h.ai_response}
        for h in reversed(history)
    ]

    response = await chat_with_farmtwin(
        request.message, farm_dict, sensor_dict, history_list
    )

    # Save to history
    chat_entry = ChatHistory(
        farm_id=request.farm_id,
        user_message=request.message,
        ai_response=response["response"]
    )
    db.add(chat_entry)
    db.commit()

    return {
        "response": response["response"],
        "source": response.get("source", "FarmTwin AI"),
        "demo_mode": DEMO_MODE
    }


@router.get("/api/chat/history/{farm_id}")
async def get_chat_history(farm_id: int = 1, limit: int = 20, db: Session = Depends(get_db)):
    history = db.query(ChatHistory).filter(
        ChatHistory.farm_id == farm_id
    ).order_by(ChatHistory.timestamp.desc()).limit(limit).all()
    return [
        {
            "user": h.user_message,
            "ai": h.ai_response,
            "timestamp": h.timestamp.isoformat() if h.timestamp else None
        }
        for h in reversed(history)
    ]


# ─── Disease Detection ────────────────────────────────────────────────────────

@router.post("/api/detect-disease")
async def detect_disease(
    farm_id: int = Form(1),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload crop image and detect diseases/pests using IBM Granite Vision"""
    # Validate file type
    allowed = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
    if image.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP images accepted")

    # Save image
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{image.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(image.file, f)

    # Analyze with Granite Vision
    farm_dict, sensor_dict = get_farm_and_sensor(db, farm_id)
    result = await analyze_crop_image(filepath, farm_dict)

    # Save detection to DB
    detection = PestDetection(
        farm_id=farm_id,
        image_path=filepath,
        disease_name=result.get("disease_name", "Unknown"),
        confidence=result.get("confidence", 0),
        severity=result.get("severity", "Unknown"),
        symptoms=json.dumps(result.get("symptoms", [])),
        recommended_actions=json.dumps(result.get("recommended_actions", []))
    )
    db.add(detection)
    db.commit()

    result["detection_id"] = detection.id
    result["image_filename"] = filename
    result["demo_mode"] = DEMO_MODE
    return result


@router.get("/api/detections/{farm_id}")
async def get_detections(farm_id: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    detections = db.query(PestDetection).filter(
        PestDetection.farm_id == farm_id
    ).order_by(PestDetection.detected_at.desc()).limit(limit).all()
    return [
        {
            "id": d.id,
            "disease_name": d.disease_name,
            "confidence": d.confidence,
            "severity": d.severity,
            "detected_at": d.detected_at.isoformat() if d.detected_at else None
        }
        for d in detections
    ]


# ─── Market Intelligence ──────────────────────────────────────────────────────

@router.get("/api/market")
async def get_market(crop_type: str = "Tomato", db: Session = Depends(get_db)):
    """Get market prices and insights"""
    prices = db.query(MarketPrice).filter(
        MarketPrice.crop_type == crop_type
    ).all()

    price_list = [
        {
            "market": m.market_name,
            "price": m.price_per_kg,
            "trend": m.trend,
            "date": m.date
        }
        for m in prices
    ]

    # Demo price history
    history = {
        "dates": ["Mar 9", "Mar 10", "Mar 11", "Mar 12", "Mar 13", "Mar 14", "Mar 15"],
        "nashik_apmc": [28, 29, 30, 31, 30, 31, 32],
        "mumbai_wholesale": [30, 31, 32, 33, 34, 34, 35],
        "local_market": [24, 25, 26, 27, 27, 28, 28],
        "online_enam": [33, 34, 35, 36, 36, 37, 38]
    }

    return {
        "prices": price_list,
        "history": history,
        "best_market": max(price_list, key=lambda x: x["price"]) if price_list else {},
        "demo_mode": DEMO_MODE
    }


# ─── What-If Simulator ────────────────────────────────────────────────────────

@router.post("/api/whatif")
async def whatif_simulator(request: WhatIfRequest, db: Session = Depends(get_db)):
    """Run What-If scenario simulation"""
    result = calculate_whatif(
        irrigation_pct=request.irrigation_pct,
        fertilizer_amount_pct=request.fertilizer_amount_pct,
        harvest_days_offset=request.harvest_days_offset,
        selling_market=request.selling_market,
        area_acres=request.area_acres
    )

    # Save scenario
    scenario = WhatIfScenario(
        farm_id=1,
        irrigation_pct=request.irrigation_pct,
        fertilizer_amount=request.fertilizer_amount_pct,
        harvest_days_offset=request.harvest_days_offset,
        selling_market=request.selling_market,
        water_saved=result["water_saved_liters"],
        yield_change=result["yield_change_kg"],
        total_cost=result["total_cost"],
        total_revenue=result["gross_revenue"],
        profit=result["net_profit"],
        sustainability_score=result["sustainability_score"]
    )
    db.add(scenario)
    db.commit()

    return result


# ─── Knowledge Center ─────────────────────────────────────────────────────────

@router.get("/api/knowledge")
async def get_knowledge():
    """Get all RAG knowledge articles"""
    articles = get_knowledge_articles()
    return {"articles": articles, "total": len(articles)}


@router.post("/api/knowledge/search")
async def search_knowledge(body: dict):
    """Search RAG knowledge base"""
    from backend.integrations.langflow import query_rag
    query = body.get("query", "")
    result = await query_rag(query)
    return {"query": query, "result": result}


# ─── Irrigation Schedule ──────────────────────────────────────────────────────

@router.get("/api/irrigation/{farm_id}")
async def get_irrigation(farm_id: int = 1, db: Session = Depends(get_db)):
    """Get detailed irrigation schedule"""
    farm_dict, sensor_dict = get_farm_and_sensor(db, farm_id)
    from backend.agents.weather_agent import get_weather_analysis
    result = await get_weather_analysis(sensor_dict)
    result["demo_mode"] = DEMO_MODE
    return result


# ─── AI Agents Status ─────────────────────────────────────────────────────────

@router.get("/api/agents/status")
async def get_agents_status():
    """Get status of all AI agents"""
    return {
        "demo_mode": DEMO_MODE,
        "agents": [
            {
                "name": "Crop Advisory Agent",
                "status": "active",
                "model": "IBM Granite 13B" if not DEMO_MODE else "Demo Mode",
                "last_run": datetime.utcnow().isoformat()
            },
            {
                "name": "Weather & Irrigation Agent",
                "status": "active",
                "model": "IBM Granite 13B" if not DEMO_MODE else "Demo Mode",
                "last_run": datetime.utcnow().isoformat()
            },
            {
                "name": "Pest/Disease Agent",
                "status": "active",
                "model": "IBM Granite Vision" if not DEMO_MODE else "Demo Mode",
                "last_run": datetime.utcnow().isoformat()
            },
            {
                "name": "Market Insights Agent",
                "status": "active",
                "model": "IBM Granite 13B" if not DEMO_MODE else "Demo Mode",
                "last_run": datetime.utcnow().isoformat()
            }
        ],
        "orchestration": "IBM watsonx Orchestrate" if not DEMO_MODE else "Demo Orchestration",
        "rag": "IBM Langflow" if not DEMO_MODE else "In-Memory RAG"
    }


@router.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": "FarmTwin AI",
        "version": "1.0.0",
        "demo_mode": DEMO_MODE,
        "timestamp": datetime.utcnow().isoformat()
    }
