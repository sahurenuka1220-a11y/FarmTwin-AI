from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./farmtwin.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Farm(Base):
    __tablename__ = "farms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="My Farm")
    farmer_name = Column(String, default="Demo Farmer")
    location = Column(String, default="Maharashtra, India")
    area_acres = Column(Float, default=2.0)
    crop_type = Column(String, default="Tomato")
    soil_type = Column(String, default="Loamy")
    irrigation_type = Column(String, default="Drip Irrigation")
    crop_stage = Column(String, default="Flowering")
    sowing_date = Column(String, default="2024-01-15")
    expected_harvest = Column(String, default="2024-04-15")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, default=1)
    soil_moisture = Column(Float, default=61.0)
    temperature = Column(Float, default=29.0)
    humidity = Column(Float, default=68.0)
    rain_probability = Column(Float, default=72.0)
    wind_speed = Column(Float, default=12.0)
    ph_level = Column(Float, default=6.8)
    nitrogen = Column(Float, default=42.0)
    phosphorus = Column(Float, default=38.0)
    potassium = Column(Float, default=55.0)
    timestamp = Column(DateTime, default=datetime.utcnow)


class PestDetection(Base):
    __tablename__ = "pest_detections"
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, default=1)
    image_path = Column(String)
    disease_name = Column(String)
    confidence = Column(Float)
    severity = Column(String)
    symptoms = Column(Text)
    recommended_actions = Column(Text)
    detected_at = Column(DateTime, default=datetime.utcnow)


class MarketPrice(Base):
    __tablename__ = "market_prices"
    id = Column(Integer, primary_key=True, index=True)
    crop_type = Column(String)
    market_name = Column(String)
    price_per_kg = Column(Float)
    date = Column(String)
    trend = Column(String, default="stable")


class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, default=1)
    user_message = Column(Text)
    ai_response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


class WhatIfScenario(Base):
    __tablename__ = "whatif_scenarios"
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, default=1)
    irrigation_pct = Column(Float, default=100.0)
    fertilizer_amount = Column(Float, default=100.0)
    harvest_days_offset = Column(Integer, default=0)
    selling_market = Column(String, default="Local Market")
    water_saved = Column(Float)
    yield_change = Column(Float)
    total_cost = Column(Float)
    total_revenue = Column(Float)
    profit = Column(Float)
    sustainability_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed demo data if empty
        if not db.query(Farm).first():
            farm = Farm(
                name="Green Valley Farm",
                farmer_name="Rajesh Kumar",
                location="Nashik, Maharashtra",
                area_acres=2.0,
                crop_type="Tomato",
                soil_type="Loamy",
                irrigation_type="Drip Irrigation",
                crop_stage="Flowering",
                sowing_date="2024-01-15",
                expected_harvest="2024-04-15"
            )
            db.add(farm)

        if not db.query(SensorReading).first():
            reading = SensorReading(
                farm_id=1, soil_moisture=61.0, temperature=29.0,
                humidity=68.0, rain_probability=72.0, wind_speed=12.0,
                ph_level=6.8, nitrogen=42.0, phosphorus=38.0, potassium=55.0
            )
            db.add(reading)

        markets = [
            ("Tomato", "Nashik APMC", 32.0, "2024-03-15", "rising"),
            ("Tomato", "Mumbai Wholesale", 35.0, "2024-03-15", "rising"),
            ("Tomato", "Local Market", 28.0, "2024-03-15", "stable"),
            ("Tomato", "Pune APMC", 30.0, "2024-03-15", "stable"),
            ("Tomato", "Online (Direct)", 38.0, "2024-03-15", "rising"),
        ]
        if not db.query(MarketPrice).first():
            for m in markets:
                db.add(MarketPrice(
                    crop_type=m[0], market_name=m[1], price_per_kg=m[2],
                    date=m[3], trend=m[4]
                ))

        db.commit()
    finally:
        db.close()
