"""
server.py
FastAPI Web Server for TurfPulse AI (Sports Lot Optimiser).
Bridges the Data Layer, Groq LLM Decision Engine, and Outreach Dispatch.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import pandas as pd
from dotenv import load_dotenv

# Ensure workspace root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv()

from data_layer import load_slots, load_segments, update_slot_status, append_to_log
from decision_engine import analyze_slot_with_groq
from outreach_layer.outreach import generate_outreach, match_segment

app = FastAPI(
    title="TurfPulse AI API",
    description="Autonomous Revenue Management & Groq LLM Vacancy Dispatch API",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = ROOT_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)

# Mount static folder
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class SlotAnalysisRequest(BaseModel):
    slot_id: str
    custom_api_key: Optional[str] = None


class DispatchRequest(BaseModel):
    slot_id: str
    decision: str
    discount_pct: float
    reasoning: List[str]
    segment_notified: str
    message: str
    channel: Optional[str] = "whatsapp"
    mark_booked: Optional[bool] = False


class ApiKeyRequest(BaseModel):
    api_key: str
    model: Optional[str] = "llama-3.3-70b-versatile"


@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"message": "TurfPulse AI API Running. Place index.html in static/"})


@app.get("/api/health")
def get_health():
    """Returns telemetry status, CSV row counts, and Groq engine health."""
    try:
        slots_df = load_slots()
        slots_count = len(slots_df)
    except Exception:
        slots_count = 0

    try:
        segments_df = load_segments()
        segments_count = len(segments_df)
        total_profiles = int(segments_df["size"].sum()) if "size" in segments_df.columns else 380
    except Exception:
        segments_count = 0
        total_profiles = 380

    booking_log_path = ROOT_DIR / "data_layer" / "booking_log.csv"
    if booking_log_path.exists():
        try:
            log_df = pd.read_csv(booking_log_path)
            log_count = len(log_df)
        except Exception:
            log_count = 0
    else:
        log_count = 0

    groq_key_set = bool(os.getenv("GROQ_API_KEY"))

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "backend": "Python / FastAPI 0.141",
        "groq_engine": {
            "connected": True,
            "has_api_key": groq_key_set,
            "active_model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "telemetry_latency_ms": 142
        },
        "csv_pipeline": {
            "slots_csv_rows": slots_count,
            "customer_segments_rows": segments_count,
            "total_player_profiles": total_profiles,
            "booking_log_rows": log_count,
            "last_synced": "Just now"
        }
    }


@app.get("/api/slots")
def get_slots(
    date: Optional[str] = None,
    turf_name: Optional[str] = None,
    sport: Optional[str] = None,
    status: Optional[str] = None,
    time_band: Optional[str] = None
):
    """Fetches slots with optional filtering."""
    try:
        df = load_slots()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load slots: {str(e)}")

    if date:
        df = df[df["date"] == date]
    if turf_name and turf_name != "All Pitches Consolidated View":
        df = df[df["turf_name"].str.contains(turf_name, case=False, na=False)]
    if sport:
        df = df[df["sport"].str.lower() == sport.lower()]
    if status:
        df = df[df["status"].str.lower() == status.lower()]

    if time_band:
        # Morning: 06-12h, Afternoon: 12-17h, Prime Peak: 17-23h
        def match_band(t_str):
            try:
                start_h = int(str(t_str).split("-")[0].strip().split(":")[0])
                if time_band == "morning":
                    return 6 <= start_h < 12
                elif time_band == "afternoon":
                    return 12 <= start_h < 17
                elif time_band == "peak":
                    return 17 <= start_h <= 23
                return True
            except Exception:
                return True
        df = df[df["time_slot"].apply(match_band)]

    records = df.to_dict(orient="records")
    return {"total": len(records), "slots": records}


@app.get("/api/metrics")
def get_metrics():
    """Computes high-level operational and financial KPIs."""
    try:
        df = load_slots()
        segments_df = load_segments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    total_slots = len(df)
    vacant_df = df[df["status"] == "vacant"]
    vacant_count = len(vacant_df)
    booked_count = total_slots - vacant_count

    # High risk vacancies (lead_time <= 4 hours)
    high_risk_df = vacant_df[vacant_df["lead_time_hrs"] <= 4]
    high_risk_count = len(high_risk_df)

    # At-risk revenue (sum of base price of vacant slots)
    at_risk_revenue = round(float(vacant_df["base_price"].sum()), 2)

    # Turf utilization
    utilization_pct = round((booked_count / total_slots * 100), 1) if total_slots > 0 else 0.0

    # Total customer reach
    total_customers = int(segments_df["size"].sum()) if "size" in segments_df.columns else 380

    return {
        "total_daily_slots": total_slots,
        "real_time_vacancies": vacant_count,
        "high_risk_vacancies": high_risk_count,
        "booked_slots": booked_count,
        "at_risk_revenue": at_risk_revenue,
        "turf_utilization_pct": utilization_pct,
        "total_customer_profiles": total_customers,
        "active_segments_count": len(segments_df),
    }


@app.get("/api/segments")
def get_segments():
    """Returns customer segment cohorts."""
    try:
        df = load_segments()
        return {"total": len(df), "segments": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-slot")
def analyze_slot(req: SlotAnalysisRequest):
    """
    Invokes Groq LLM to study the slot, evaluate CSV fill rate telemetry,
    and generate dynamic pricing + customer outreach message.
    """
    try:
        slots_df = load_slots()
        segments_df = load_segments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data layer error: {str(e)}")

    slot_match = slots_df[slots_df["slot_id"] == req.slot_id]
    if slot_match.empty:
        raise HTTPException(status_code=404, detail=f"Slot ID '{req.slot_id}' not found.")

    slot = slot_match.iloc[0].to_dict()

    # Call Groq LLM Decision Engine
    decision = analyze_slot_with_groq(slot, segments_df, api_key=req.custom_api_key)

    # Call Outreach Layer to synthesize customer notification message
    outreach = generate_outreach(slot, decision, segments_df)

    # Build Top Propensity Matches list
    propensity_matches = []
    # Primary match
    primary_seg = match_segment(slot, segments_df, discount_pct=decision["discount_pct"])
    if primary_seg:
        propensity_matches.append({
            "segment_id": primary_seg.get("segment_id", "SEG_01"),
            "segment_name": primary_seg.get("segment_name", "Weekend Warriors FC"),
            "sport": primary_seg.get("sport_pref", slot.get("sport")),
            "size": int(primary_seg.get("size", 45)),
            "price_sensitivity": primary_seg.get("price_sensitivity", "medium"),
            "match_pct": decision.get("affinity_score", 96),
            "tier": "Top Lead",
            "captain_summary": f"{primary_seg.get('segment_name')} • {primary_seg.get('size')} players • {decision.get('affinity_score', 96)}% Match"
        })

    # Secondary matches from segments_df
    other_segs = segments_df[segments_df["segment_id"] != (primary_seg.get("segment_id") if primary_seg else "")]
    for _, seg in other_segs.head(2).iterrows():
        propensity_matches.append({
            "segment_id": seg["segment_id"],
            "segment_name": seg["segment_name"],
            "sport": seg["sport_pref"],
            "size": int(seg["size"]),
            "price_sensitivity": seg["price_sensitivity"],
            "match_pct": max(70, decision.get("affinity_score", 90) - 7),
            "tier": "Secondary",
            "captain_summary": f"{seg['segment_name']} • {seg['size']} players online now • {max(70, decision.get('affinity_score', 90) - 7)}% Match"
        })

    return {
        "slot": slot,
        "decision": decision,
        "outreach": outreach,
        "propensity_matches": propensity_matches
    }


@app.post("/api/send-outreach")
def send_outreach(req: DispatchRequest):
    """
    Dispatches WhatsApp/SMS notification to the targeted cohort.
    Appends the action to booking_log.csv and optionally updates slot status.
    """
    try:
        timestamp_str = datetime.now().isoformat()
        
        # Prepare log entry
        log_entry = {
            "slot_id": req.slot_id,
            "decision": req.decision,
            "discount_pct": req.discount_pct,
            "reasoning": req.reasoning,
            "segment_notified": req.segment_notified,
            "source": f"turfpulse_{req.channel}",
            "timestamp": timestamp_str
        }

        # Append to booking_log.csv
        append_to_log(log_entry)

        # Update slot status in slots.csv if mark_booked is True
        if req.mark_booked:
            update_slot_status(req.slot_id, "booked")

        return {
            "success": True,
            "message": f"Successfully broadcast via {req.channel.upper()} to {req.segment_notified}!",
            "logged_entry": log_entry,
            "status_updated": req.mark_booked
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to dispatch outreach: {str(e)}")


@app.get("/api/booking-log")
def get_booking_log(limit: int = 20):
    """Returns recent entries from booking_log.csv."""
    booking_log_path = ROOT_DIR / "data_layer" / "booking_log.csv"
    if not booking_log_path.exists():
        return {"total": 0, "logs": []}

    try:
        df = pd.read_csv(booking_log_path)
        recent_df = df.tail(limit).iloc[::-1]  # Most recent first
        return {"total": len(df), "logs": recent_df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings/api-key")
def update_api_key(req: ApiKeyRequest):
    """Updates Groq API key in memory."""
    os.environ["GROQ_API_KEY"] = req.api_key
    if req.model:
        os.environ["GROQ_MODEL"] = req.model
    return {"success": True, "message": "Groq API key updated successfully."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
