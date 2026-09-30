# TurfPulse AI ⚽🏏🎾
### Autonomous Revenue Management & Vacancy Dispatch System

[![Node.js](https://img.shields.io/badge/Runtime-Node.js%2022-339933.svg?logo=node.js&logoColor=white)](https://nodejs.org)
[![Express.js](https://img.shields.io/badge/Backend-Express.js%205.x-000000.svg?logo=express&logoColor=white)](https://expressjs.com)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.110-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/AI%20Engine-Groq%20LPU%20(Llama--3.3--70B)-F55036.svg)](https://groq.com)
[![TailwindCSS](https://img.shields.io/badge/Design-TailwindCSS%20v3-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📌 Executive Summary

Sports turf arenas suffer from predictable revenue leakage: last-minute cancellations and off-peak weekday time slots frequently go vacant, producing $0 while operational expenses (floodlights, ground staff, maintenance) continue to tick.

**TurfPulse AI** solves this autonomously:
1. **Detects** vacant slots across arena pitches in real time.
2. **Evaluates** historical fill rates, time-to-kickoff lead times, and operating margins.
3. **Invokes Groq LLM (Llama 3.3 70B)** to determine optimal dynamic discounts while strictly respecting break-even cost floors.
4. **Matches** customer cohorts from customer profile databases based on sport affinity, time band, and price sensitivity.
5. **Synthesizes & Dispatches** personalized, high-converting WhatsApp broadcasts in 1 click.

---

## 🛠️ Backend Tech Stack & Architecture

TurfPulse AI features a modern, dual-runtime backend architecture with a primary **Node.js & Express.js** server and an interoperable **Python FastAPI** service.

```
                          HTTP REQUEST (Client / Browser)
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │   Express.js Application  │
                        │        (server.js)        │
                        └─────────────┬─────────────┘
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
     ┌───────────────────┐                         ┌───────────────────┐
     │ express.json()    │                         │ Custom Logger     │
     │ Middleware        │                         │ Middleware        │
     │ (Parses req.body) │                         │ (Logs & calls     │
     └─────────┬─────────┘                         │  next())          │
               │                                   └─────────┬─────────┘
               └──────────────────────┬──────────────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │       Route Handlers      │
                        │                           │
                        │  GET  /api/slots          │
                        │  GET  /api/slots/:id      │
                        │  GET  /api/analytics      │
                        │  POST /api/broadcast      │
                        │  GET  /api/logs           │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │    CSV Data Persistence   │
                        │   (slots.csv, logs.csv)   │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                          HTTP RESPONSE (res.json())
```

### 1. Node.js & Express.js REST API (`server.js`)
* **Framework:** Express.js 5.x on Node.js v22.
* **Request Body Parsing:** `app.use(express.json())` middleware parses incoming JSON payloads directly into `req.body`.
* **Custom Middleware Pipeline:** Intercepts every incoming request, logs timestamp, HTTP method, and URL, then invokes `next()` to pass control to route handlers.
* **CORS Middleware:** `cors()` enables cross-origin resource sharing for frontend clients.
* **Static File Server:** `express.static('static')` serves the production dashboard interface.
* **Dynamic Route Parameters:** `req.params.id` in `GET /api/slots/:id` retrieves individual slot metrics and calculates real-time offers.
* **Query Parameters:** `req.query` in `GET /api/slots?status=vacant&sport=Football` provides multi-attribute filtering.
* **Standard HTTP Status Codes:** `200 OK`, `201 Created` (on broadcast), `400 Bad Request`, `404 Not Found`, `500 Internal Server Error`.

### 2. AI Decision Engine & Guardrails (`decision_engine/groq_agent.py`)
* **Groq LPU Inference:** Uses `llama-3.3-70b-versatile` to evaluate occupancy variables with ultra-low latency (<150ms).
* **Deterministic Financial Safety Guardrail:** A mathematical protection layer wraps LLM outputs:
  $$\text{Max Allowable Discount} = \max\left(0, \frac{\text{base\_price} - \text{cost\_to\_operate}}{\text{base\_price}} \times 100 - 10\%\right)$$
  The system strictly forbids discounting below the operating cost floor, maintaining at least a 10% safety margin.
* **Intelligent Heuristic Fallback Engine:** Built-in revenue management algorithms ensure 100% uptime during network dropouts or API rate limits.

### 3. Data Persistence Layer (`data_layer/`)
* **`slots.csv`:** 180 slots across 3 turfs (*Apex Arena*, *Velocity Turf*, *Champions Court*) over a 14-day schedule.
* **`customer_segments.csv`:** 7 distinct customer cohorts representing 405 active team captains.
* **`booking_log.csv`:** Append-only audit stream tracking every AI decision, discount applied, and timestamp.
* **Production Mapping:** The CSV architecture maps 1:1 to relational database tables (PostgreSQL/MySQL) or MongoDB collections without requiring local database setup for demos.

### 4. Alternative Python Backend (`server.py` & `app.py`)
* **FastAPI 0.110:** Asynchronous REST API utilizing Pydantic data schemas.
* **Streamlit (`app.py`):** Single-command UI wrapper for instant evaluations.

---

## 🚀 Key Features

- **Executive Web Dashboard**: Clean, dark-mode operations portal built with Tailwind CSS.
- **Autonomous Vacancy Matrix**: Real-time slot grid with urgency countdowns (< 3h remaining, prime peak, off-peak).
- **Groq LLM Decision Reasoning**: Analyzes vacancy risks using multi-factor prompt reasoning.
- **Financial Safety Guardrail**: Never prices below the break-even operating floor.
- **Cohort Affinity Matching**: Connects open slots with high-propensity customer segments.
- **1-Click WhatsApp Broadcast**: Synthesizes conversion-focused sports copy with countdown booking links.
- **Continuous Audit Trail**: Appends all dispatches and discount records to `booking_log.csv`.

---

## 📁 Repository Structure

```bash
Turfvacancy/
├── server.js                    # 01 // Node.js & Express.js REST API Server
├── package.json                 # Node dependencies (express, cors, dotenv)
├── static/                      # 02 // Frontend Web Dashboard
│   └── index.html               # Clean dark-mode manager operations portal
├── data_layer/                  # 03 // Data Layer
│   ├── slots.csv                # 180 slots across 3 turfs and 4 sports
│   ├── customer_segments.csv    # 7 customer segments (405 player profiles)
│   ├── booking_log.csv          # Real-time append audit stream
│   ├── data_manager.py          # CSV loaders, validation & update functions
│   ├── generate_dataset.py      # Reproducible dataset generator
│   └── validate_and_test.py     # Data validation & test harness
├── decision_engine/             # 04 // AI Decision Engine
│   ├── __init__.py
│   └── groq_agent.py            # Groq Llama-3.3-70B multi-factor reasoning
├── outreach_layer/              # 05 // Outreach Dispatch
│   ├── __init__.py
│   └── outreach.py              # Cohort matching & personalized message synthesis
├── server.py                    # Python FastAPI REST API Backend
├── app.py                       # Streamlit Application Wrapper
├── run.py                       # Convenience launcher (FastAPI / Streamlit)
├── requirements.txt             # Python dependencies
├── Procfile                     # Deployment process config
├── render.yaml                  # Render Blueprint config
├── Dockerfile                   # Production Docker container
└── README.md                    # System documentation
```

---

## ⚡ Quickstart Guide

### Option A: Node.js & Express (Recommended)

```bash
git clone https://github.com/Barbarian-king123/Turfvacancy.git
cd Turfvacancy

# Install Node dependencies
npm install

# Start Express server
npm start
# or: node server.js
```

Open **[http://localhost:3000](http://localhost:3000)** in your browser.

---

### Option B: Python & FastAPI

```bash
# Setup virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI server
python run.py
# or: uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```

Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

---

### Option C: Streamlit App

```bash
streamlit run app.py
```

Open **[http://127.0.0.1:8501](http://127.0.0.1:8501)** in your browser.

---

## 📡 REST API Reference

| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Serves the interactive operations dashboard UI | `200` |
| `GET` | `/api/health` | Returns backend telemetry, CSV row counts, and uptime | `200` |
| `GET` | `/api/slots` | Query slots with filters (`?status=vacant&sport=Football`) | `200`, `500` |
| `GET` | `/api/slots/:id` | Route param: fetches slot details & calculates dynamic offer | `200`, `404` |
| `GET` | `/api/analytics` | Returns arena occupancy rates, rescued revenue, and yields | `200` |
| `POST` | `/api/broadcast` | Dispatches WhatsApp alert, logs to CSV, marks slot booked | `201`, `400` |
| `GET` | `/api/logs` | Returns recent dispatch records from `booking_log.csv` | `200` |

### Sample Slot Analysis Request:
```bash
curl -X GET http://localhost:3000/api/slots/S1016
```

### Sample Slot Analysis Response:
```json
{
  "slot": {
    "slot_id": "S1016",
    "turf_name": "Apex Arena",
    "sport": "Football",
    "time_slot": "20:00-21:00",
    "base_price": 1600,
    "cost_to_operate": 450,
    "historical_fill_rate": 0.76,
    "status": "vacant"
  },
  "analysis": {
    "decision": "notify_small_discount",
    "discount_pct": 15,
    "discounted_price": 1360,
    "matched_segment": "Weekend Football Players",
    "captains_count": 90,
    "message": "⚽ Turf Alert: Apex Arena 20:00-21:00 tonight has opened up! 15% off at $1,360/hr. Reply to book or tap: turfpulse.ai/book/s1016"
  }
}
```

### Sample Broadcast Dispatch Request:
```bash
curl -X POST http://localhost:3000/api/broadcast \
  -H "Content-Type: application/json" \
  -d '{
    "slot_id": "S1016",
    "discount_pct": 15,
    "segment": "Weekend Football Players",
    "channel": "whatsapp"
  }'
```

### Sample Broadcast Dispatch Response:
```json
{
  "success": true,
  "message": "Broadcast successfully sent via WHATSAPP to Weekend Football Players!",
  "logged": {
    "slot_id": "S1016",
    "decision": "notify_discount",
    "discount_pct": 15,
    "segment_notified": "Weekend Football Players",
    "source": "express_whatsapp",
    "timestamp": "2026-09-30T18:14:00.000Z"
  },
  "slot_status": "booked"
}
```

---

## 🧪 Testing & Data Verification

Run the automated data validation test harness:
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
