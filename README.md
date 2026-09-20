# TurfPulse AI ⚽🏏🎾
### Autonomous Revenue Management & Vacancy Dispatch System


> 🟢 **LIVE DEPLOYMENT LINK**: **[https://9a4d98a1fbb20773-59-182-157-172.serveousercontent.com](https://9a4d98a1fbb20773-59-182-157-172.serveousercontent.com)**  
> 🔗 **REST API Telemetry**: [https://9a4d98a1fbb20773-59-182-157-172.serveousercontent.com/api/health](https://9a4d98a1fbb20773-59-182-157-172.serveousercontent.com/api/health)

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.110-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/AI%20Engine-Groq%20LPU%20(Llama--3.3--70B)-F55036.svg)](https://groq.com)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io)
[![TailwindCSS](https://img.shields.io/badge/Design-TailwindCSS%20v3-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📌 Executive Summary

Turf arenas suffer from predictable revenue leakage: last-minute cancellations and low-occupancy weekday time slots frequently go vacant, producing zero revenue while operational costs continue to tick.

**TurfPulse AI** solves this autonomously:
1. Detects vacant slots across arena pitches in real-time.
2. Evaluates historical fill rates, time-to-kickoff lead times, and operating margins.
3. Invokes **Groq LLM (Llama 3.3 70B)** to determine the optimal dynamic discount that strictly respects operational cost floors.
4. Matches captain cohorts from customer profile databases based on sport and time affinity.
5. Synthesizes personalized, high-converting WhatsApp & SMS broadcasts dispatched with a single click.

---

## 🏗️ System Architecture

```
+-------------------------------------------------------------------------------+
|                             01 // DATA LAYER                                  |
|   slots.csv  •  customer_segments.csv  •  booking_log.csv  •  data_manager.py |
+-------------------------------------------------------------------------------+
                                      │
                                      ▼ (Python FastAPI Backend)
+-------------------------------------------------------------------------------+
|                         02 // GROQ LLM (API) ENGINE                           |
|   Dynamic vacancy reasoning, fill rate analysis, margin safety & discounts    |
+-------------------------------------------------------------------------------+
                                      │
                                      ▼ (Outreach Matching & Formatting)
+-------------------------------------------------------------------------------+
|                    03 // MANAGER UI & OUTREACH DISPATCH                       |
|   Real-time slot vacancy grid, 1-click WhatsApp/SMS broadcast to captains     |
+-------------------------------------------------------------------------------+
```

---

## 🚀 Key Features

- **Autonomous Vacancy Grid**: Live slot matrix across multiple pitches and sports (Football, Cricket, Padel) with urgency indicators (< 3h, < 6h, peak vs off-peak).
- **Groq LLM Decision Reasoning**: Analyzes vacancy risks using ultra-fast inference (< 150ms) to produce multi-factor operational explanations.
- **Financial Safety Guardrail**: Strictly protects operating margins (`cost_to_operate`)—never discounts below the break-even floor.
- **Cohort Affinity Matching**: Connects vacant pitches with the highest-converting customer segments from `customer_segments.csv`.
- **1-Click WhatsApp Dispatch**: Generates customized WhatsApp templates with countdown timers, team captain names, and direct booking links.
- **Dual Runtime Support**:
  - **FastAPI Native Dashboard** (Default): Full-bleed, pixel-perfect management UI with Tailwind CSS.
  - **Streamlit App**: Ready-to-go dashboard launcher for instant hackathon evaluations.
- **Continuous Audit Trail**: Appends all decisions, discount percentages, and timestamps to `booking_log.csv`.

---

## 📁 Repository Structure

```bash
Turfvacancy/
├── data_layer/                  # 01 // Data Layer
│   ├── slots.csv                # 180 slots across 3 turfs and 3 sports
│   ├── customer_segments.csv    # 7 customer segments (405 player profiles)
│   ├── booking_log.csv          # Real-time append stream of decisions
│   ├── data_manager.py          # CSV loaders, validation & update functions
│   ├── generate_dataset.py      # Reproducible realistic dataset generator
│   └── validate_and_test.py     # Automated data schema & read/write test suite
├── decision_engine/             # 02 // AI Decision Engine
│   ├── __init__.py
│   └── groq_agent.py            # Groq Llama-3.3-70B multi-factor reasoning
├── outreach_layer/              # 03 // Outreach Dispatch
│   ├── __init__.py
│   └── outreach.py              # Cohort matching & personalized message synthesis
├── static/                      # Frontend Assets & Dashboard
│   └── index.html               # Pixel-perfect Arena Ops Manager UI
├── server.py                    # FastAPI REST API Backend
├── app.py                       # Streamlit Application Wrapper
├── run.py                       # Convenience launcher (FastAPI / Streamlit)
├── requirements.txt             # Python production dependencies
├── Procfile                     # Heroku / Render / Railway deployment
├── render.yaml                  # Render Blueprint deployment config
├── Dockerfile                   # Production Docker container image
└── README.md                    # System documentation
```

---

## ⚡ Quickstart Guide

### 1. Clone & Setup Virtual Environment

```bash
git clone https://github.com/Barbarian-king123/Turfvacancy.git
cd Turfvacancy

python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Add your Groq API key:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
PORT=8000
```
*(Note: If no Groq API key is supplied, the system automatically falls back to its built-in revenue management heuristics without crashing).*

### 3. Run the Application

#### Option A: FastAPI Web Dashboard (Recommended)
```bash
python run.py
# or: uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

#### Option B: Streamlit Dashboard
```bash
python run.py streamlit
# or: streamlit run app.py
```
Open **[http://127.0.0.1:8501](http://127.0.0.1:8501)** in your browser.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the interactive manager dashboard UI |
| `GET` | `/api/health` | Returns backend telemetry, CSV row counts, and Groq status |
| `GET` | `/api/slots` | Query slots with filters (`date`, `turf_id`, `sport`, `status`) |
| `GET` | `/api/metrics` | Returns live arena KPIs (vacancies, at-risk revenue, fill rate) |
| `POST` | `/api/analyze-slot` | Runs Groq LLM inference on a specific slot |
| `POST` | `/api/send-outreach` | Dispatches outreach, logs to `booking_log.csv`, updates slot |

### Sample Slot Analysis Request:
```bash
curl -X POST http://127.0.0.1:8000/api/analyze-slot \
  -H "Content-Type: application/json" \
  -d '{"slot_id": "S1016"}'
```

### Sample Slot Analysis Response:
```json
{
  "slot": {
    "slot_id": "S1016",
    "turf_name": "Apex Arena",
    "sport": "Football",
    "time_slot": "20:00-21:00",
    "base_price": 1600.0,
    "historical_fill_rate": 0.88
  },
  "decision": {
    "decision": "notify_small_discount",
    "discount_pct": 15.0,
    "confidence": "high",
    "reasoning": [
      "Prime peak slot suddenly vacant under 3h lead time.",
      "15% flash promo protects 40% gross margin above $600 operating floor."
    ]
  },
  "outreach": {
    "segment_name": "Weekend Warriors FC",
    "channel": "whatsapp",
    "message": "Hey Liam! A prime 20:00 slot just opened on Pitch 1 tonight. Lock it in with your team at 15% OFF ($1360/hr): turfpulse.ai/book/s1016"
  }
}
```

---

## ☁️ Deployment Guide

### 🌐 Live Public Link
- **Live Web Dashboard (Instant Access)**: [https://9a4d98a1fbb20773-59-182-157-172.serveousercontent.com](https://9a4d98a1fbb20773-59-182-157-172.serveousercontent.com)
- **API Health Telemetry Endpoint**: [https://9a4d98a1fbb20773-59-182-157-172.serveousercontent.com/api/health](https://9a4d98a1fbb20773-59-182-157-172.serveousercontent.com/api/health)

### Deploy on Render (Recommended)

1. Fork or push to your GitHub repo (`Barbarian-king123/Turfvacancy`).
2. Log into [Render Dashboard](https://dashboard.render.com).
3. Click **New +** $\rightarrow$ **Web Service**.
4. Connect the `Turfvacancy` repository.
5. Render detects the `render.yaml` blueprint automatically:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
6. Under Environment Variables, add `GROQ_API_KEY`.
7. Click **Deploy Web Service**.

### Deploy on Railway

1. Log into [Railway.app](https://railway.app).
2. Click **New Project** $\rightarrow$ **Deploy from GitHub repo**.
3. Select `Barbarian-king123/Turfvacancy`.
4. Railway detects the `Procfile` and builds the service automatically.
5. Add `GROQ_API_KEY` in the project settings.

### Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io).
2. Select your repository `Barbarian-king123/Turfvacancy`, branch `main`, and main file path `app.py`.
3. In Advanced Settings, enter your secrets (`GROQ_API_KEY`).
4. Click **Deploy!**.

### Deploy with Docker

```bash
docker build -t turfpulse-ai .
docker run -p 8000:8000 -e GROQ_API_KEY="your_api_key" turfpulse-ai
```

---

## 🧪 Verification & Testing

Run the automated data layer test harness:
```bash
python data_layer/validate_and_test.py
```
Expected output:
```text
[PASS] slots.csv column schema matches exactly (180 slots).
[PASS] cost_to_operate < base_price for 100% of slots.
[PASS] customer_segments.csv schema valid (7 segments).
[PASS] Slot status successfully updated to: booked.
[PASS] booking_log.csv verified with live append.
ALL VALIDATION CHECKS & TESTS PASSED SUCCESSFULLY!
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
