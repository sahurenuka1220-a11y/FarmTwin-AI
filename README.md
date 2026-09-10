# 🌾 FarmTwin AI — AI Smart Farming Digital Twin

[![Demo Mode](https://img.shields.io/badge/Demo-Ready-green)](/) [![IBM Granite](https://img.shields.io/badge/IBM-Granite%20AI-blue)](/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688)](/)

> **FarmTwin AI** is a complete AI-powered Smart Farming platform that creates a **Digital Twin** of a farmer's field, combining crop, soil, weather, pest/disease, and market intelligence into one personalized farming action plan.

---

## 🚀 Quick Start

```bash
# 1. Clone and navigate
cd farmtwin

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy env file (demo works without IBM credentials)
cp .env.example .env

# 4. Start the server
uvicorn backend.main:app --reload

# 5. Open browser
# → http://localhost:8000
```

---

## 🎯 Features

### 🤖 4 AI Agents (IBM watsonx Orchestrate)
| Agent | Purpose | IBM Tech |
|-------|---------|----------|
| **Crop Advisory Agent** | Seeds, fertilizers, harvesting guidance | IBM Granite 13B |
| **Weather & Irrigation Agent** | Weather analysis, irrigation scheduling | IBM Granite 13B |
| **Pest/Disease Agent** | Image-based crop disease detection | IBM Granite Vision |
| **Market Insights Agent** | Price analysis, profit optimization | IBM Granite 13B |

### 🏗️ Architecture
- **Backend**: Python FastAPI + SQLite
- **Frontend**: HTML/CSS/JavaScript (no framework dependency)
- **AI**: IBM Granite models via watsonx API
- **RAG**: IBM Langflow with agricultural knowledge base
- **Orchestration**: IBM watsonx Orchestrate (multi-agent)

### 📱 Pages
1. **Dashboard** — Farm Health Score, metrics, today's actions, 7-day timeline
2. **My Farm** — Farm profile + sensor data management
3. **AI Advisor** — Crop care, fertilizer, harvest recommendations
4. **Disease Detection** — Upload crop image → AI diagnosis
5. **Irrigation** — Weather + 7-day irrigation schedule
6. **Market Intelligence** — Price comparison + profit analysis
7. **What-If Simulator** — Scenario planning (pure Python math)
8. **Knowledge Center** — Agricultural RAG knowledge base

### 💬 Ask FarmTwin Chatbot
Ask natural language questions like:
- *"Should I irrigate today?"*
- *"Why are my leaves turning yellow?"*
- *"When should I harvest?"*
- *"Which market gives me highest profit?"*

---

## 🔑 IBM Credentials Setup

Copy `.env.example` to `.env` and fill in:

```env
# IBM watsonx
WATSONX_API_KEY=your_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# IBM Langflow  
LANGFLOW_API_URL=https://your-langflow-instance.ibm.com
LANGFLOW_API_KEY=your_langflow_key
LANGFLOW_FLOW_ID=your_flow_id

# IBM watsonx Orchestrate
ORCHESTRATE_API_KEY=your_orchestrate_key

# Disable demo mode (use real IBM APIs)
DEMO_MODE=false
```

**Without credentials**: Set `DEMO_MODE=true` (default) — the app runs with realistic sample data.

---

## 🧪 Demo Mode

When `DEMO_MODE=true`, the app uses:
- **Farm**: 2-acre Tomato farm, Nashik, Maharashtra
- **Crop Stage**: Flowering (42 days to harvest)
- **Soil**: Loamy, pH 6.8, drip irrigation
- **Sensors**: 29°C, 72% rain probability, 61% soil moisture, 34% pest risk
- **Market**: ₹30/kg current → ₹38/kg best (Online/eNAM)
- **Expected Yield**: 4.2 tons | **Expected Profit**: ₹1,36,400

All demo data is clearly labelled with 🧪 **Demo Data** badges.

---

## 🐳 Docker Deployment

```bash
docker build -t farmtwin-ai .
docker run -p 8000:8000 -e DEMO_MODE=true farmtwin-ai
```

---

## 📁 Project Structure

```
farmtwin/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── database/
│   │   └── models.py              # SQLite models + seed data
│   ├── agents/
│   │   ├── crop_agent.py          # Crop Advisory Agent
│   │   ├── weather_agent.py       # Weather & Irrigation Agent
│   │   ├── pest_agent.py          # Pest/Disease Agent (Granite Vision)
│   │   ├── market_agent.py        # Market Insights Agent
│   │   ├── chatbot_agent.py       # Ask FarmTwin chatbot
│   │   ├── decision_engine.py     # Central FarmTwin Decision Engine
│   │   └── whatif_simulator.py    # What-If scenario calculator
│   ├── integrations/
│   │   ├── granite.py             # IBM Granite / watsonx integration
│   │   └── langflow.py            # IBM Langflow RAG integration
│   └── routers/
│       └── api.py                 # All REST API endpoints
├── frontend/
│   ├── templates/
│   │   └── index.html             # Main SPA template
│   └── static/
│       ├── css/style.css          # Complete stylesheet
│       └── js/app.js              # All frontend JavaScript
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | Full FarmTwin Decision Engine output |
| GET | `/api/farm/{id}` | Farm profile |
| PUT | `/api/farm/{id}` | Update farm profile |
| GET | `/api/sensors/{id}` | Sensor readings |
| PUT | `/api/sensors/{id}` | Update sensor data |
| POST | `/api/chat` | Ask FarmTwin chatbot |
| POST | `/api/detect-disease` | Upload image → disease detection |
| GET | `/api/market` | Market prices + history |
| POST | `/api/whatif` | What-If scenario simulation |
| GET | `/api/knowledge` | RAG knowledge articles |
| POST | `/api/knowledge/search` | Search knowledge base |
| GET | `/api/irrigation/{id}` | Irrigation schedule |
| GET | `/api/agents/status` | AI agents status |
| GET | `/api/health` | Health check |

---

## 🏆 Hackathon Demo Flow

1. **Open** `http://localhost:8000` → Dashboard loads with demo farm
2. **Dashboard** → See Farm Health Score (78/100), risk alerts, 7-day timeline
3. **Click "Ask FarmTwin"** → Chat: "Should I irrigate today?" 
4. **Disease Detection** → Upload any leaf image → See AI analysis
5. **What-If Simulator** → Move sliders → See instant profit change
6. **Market Intelligence** → Compare prices across 5 markets
7. **Irrigation** → See 7-day weather + irrigation schedule

---

Built with ❤️ for IBM Hackathon | FarmTwin AI v1.0
