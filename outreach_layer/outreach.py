
import sys
from typing import Dict, Any, Optional
import pandas as pd

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def _parse_hour(time_str: str) -> int:
    """Extracts starting hour from '14:00' or '14:00-15:00' format."""
    try:
        start_part = time_str.split("-")[0].strip()
        return int(start_part.split(":")[0])
    except Exception:
        return 12  # safe default


def _time_falls_in_band(slot_time: str, band_time: str) -> bool:
    """
    Checks if a slot (e.g., '14:00-15:00') starts within a band (e.g., '12:00-17:00').
    """
    try:
        slot_start = _parse_hour(slot_time)
        band_parts = band_time.split("-")
        band_start = int(band_parts[0].strip().split(":")[0])
        band_end = int(band_parts[1].strip().split(":")[0])
        return band_start <= slot_start < band_end
    except Exception:
        return True


def match_segment(
    slot: Dict[str, Any],
    segments_df: pd.DataFrame,
    discount_pct: float = 0.0
) -> Optional[Dict[str, Any]]:
    """
    Finds the optimal customer segment for a given slot.
    Prioritizes:
      1. Sport match
      2. Time band overlap
      3. Price sensitivity alignment with discount level
      4. Segment reach (size)
    """
    if segments_df is None or segments_df.empty:
        return {
            "segment_id": "SEG_DEFAULT",
            "segment_name": f"Local {slot.get('sport', 'Sports')} Community",
            "sport_pref": slot.get("sport", "General"),
            "preferred_time_band": "Any",
            "price_sensitivity": "medium",
            "size": 50
        }

    # 1. Match sport
    sport_matches = segments_df[
        segments_df["sport_pref"].astype(str).str.lower() == str(slot.get("sport", "")).lower()
    ]
    if sport_matches.empty:
        sport_matches = segments_df

    # 2. Match time band
    slot_time = str(slot.get("time_slot", ""))
    time_matches = sport_matches[
        sport_matches["preferred_time_band"].apply(lambda band: _time_falls_in_band(slot_time, band))
    ]

    candidates = time_matches if not time_matches.empty else sport_matches

    # 3. Score candidates by discount alignment
    # High discount (>=20%) -> prefer high sensitivity
    # Low/No discount (0-10%) -> prefer low/medium sensitivity
    target_sensitivity = "high" if discount_pct >= 20.0 else ("medium" if discount_pct > 0 else "low")
    
    scored_candidates = candidates.copy()
    scored_candidates["pref_score"] = scored_candidates["price_sensitivity"].apply(
        lambda s: 2 if str(s).lower() == target_sensitivity else 1
    )

    # 4. Sort by score, then audience size descending
    sorted_candidates = scored_candidates.sort_values(
        by=["pref_score", "size"], ascending=[False, False]
    )

    return sorted_candidates.iloc[0].to_dict()


def generate_outreach(
    slot: Dict[str, Any],
    decision_result: Dict[str, Any],
    segments_df: pd.DataFrame
) -> Dict[str, str]:
    """
    Person C Function Contract:
    Takes slot details and Person B's decision, matches customer segment,
    and formats outreach message.

    Returns:
        {
            "matched_segment": str,
            "message": str
        }
    """
    decision = decision_result.get("decision", "no_action")
    discount_pct = float(decision_result.get("discount_pct", 0.0))

    # Case 1: No action needed (slot will fill naturally)
    if decision == "no_action":
        return {
            "matched_segment": "None (No Action)",
            "message": "⏸️ **No Outreach Dispatched**\n\nThe agent determined this slot has high organic demand. Preserving full margin without discounts."
        }

    # Match best audience segment
    segment = match_segment(slot, segments_df, discount_pct=discount_pct)
    segment_name = segment.get("segment_name", "Valued Players")
    segment_size = segment.get("size", 0)

    # Price math
    base_price = float(slot.get("base_price", 1000.0))
    discounted_price = round(base_price * (1.0 - discount_pct / 100.0))
    savings = round(base_price - discounted_price)

    sport = slot.get("sport", "Turf")
    turf_name = slot.get("turf_name", "Main Turf")
    day = slot.get("day_of_week", "Today")
    date = slot.get("date", "")
    time_slot = slot.get("time_slot", "")
    lead_time = slot.get("lead_time_hrs", 0)

    # Format message based on decision type without emojis
    if decision == "notify_large_discount":
        urgency_hook = f"FLASH PROMO — {int(discount_pct)}% OFF TONIGHT"
        price_line = f"Rate: ${discounted_price}/hr (Regular ${int(base_price)}/hr - Save ${savings})"
        cta = "Only 1 prime slot open for this window. Lock it in with your team before it fills."
    elif decision == "notify_small_discount":
        urgency_hook = f"Special Slot Alert — {int(discount_pct)}% Off"
        price_line = f"Rate: ${discounted_price}/hr (Regular ${int(base_price)}/hr)"
        cta = "Exclusive priority access for registered club captains."
    else:  # notify_only
        urgency_hook = "Slot Vacancy Notice"
        price_line = f"Rate: ${int(base_price)}/hr"
        cta = "Tap below to reserve before open general booking."

    message = (
        f'Hey {segment_name}! A prime {time_slot} slot just opened on {turf_name} ({sport}) tonight. '
        f'{urgency_hook}. {price_line}. {cta} turfpulse.ai/book/{slot.get("slot_id", "slot").lower()}'
    )

    return {
        "matched_segment": segment_name,
        "message": message
    }


# =====================================================================
# STANDALONE TEST HARNESS
# Run this file directly (`python outreach.py`) to test your code!
# =====================================================================
if __name__ == "__main__":
    print("--- TESTING OUTREACH LAYER STANDALONE ---\n")

    # 1. Fake segments dataframe (matching Person A's schema)
    mock_segments = pd.DataFrame([
        {
            "segment_id": "SEG_01",
            "segment_name": "Weekday Afternoon Ballers",
            "sport_pref": "Football",
            "preferred_time_band": "12:00-17:00",
            "price_sensitivity": "high",
            "size": 65
        },
        {
            "segment_id": "SEG_02",
            "segment_name": "Evening Football League",
            "sport_pref": "Football",
            "preferred_time_band": "18:00-22:00",
            "price_sensitivity": "low",
            "size": 120
        },
        {
            "segment_id": "SEG_03",
            "segment_name": "Box Cricket After-Work Club",
            "sport_pref": "Box Cricket",
            "preferred_time_band": "17:00-21:00",
            "price_sensitivity": "medium",
            "size": 80
        }
    ])

    # 2. Test Case A: Afternoon low-demand slot (large discount)
    slot_a = {
        "slot_id": "S1001",
        "turf_name": "Apex Arena",
        "sport": "Football",
        "date": "2026-09-15",
        "day_of_week": "Tuesday",
        "time_slot": "14:00-15:00",
        "lead_time_hrs": 3,
        "base_price": 1200.0,
        "cost_to_operate": 400.0,
        "historical_fill_rate": 0.22,
        "status": "vacant"
    }
    decision_a = {
        "decision": "notify_large_discount",
        "discount_pct": 25.0,
        "confidence": "high",
        "reasoning": ["Low fill rate 22%", "Short lead time 3h"],
        "source": "llm"
    }

    result_a = generate_outreach(slot_a, decision_a, mock_segments)
    print("=== TEST CASE A: Large Discount ===")
    print(f"Matched Segment: {result_a['matched_segment']}")
    print("Rendered Message:\n" + result_a["message"])
    print("\n" + "="*50 + "\n")

    # 3. Test Case B: Prime slot (no action)
    decision_b = {
        "decision": "no_action",
        "discount_pct": 0.0,
        "confidence": "high",
        "reasoning": ["High historical fill rate 85%"],
        "source": "llm"
    }
    result_b = generate_outreach(slot_a, decision_b, mock_segments)
    print("=== TEST CASE B: No Action ===")
    print(f"Matched Segment: {result_b['matched_segment']}")
    print("Rendered Message:\n" + result_b["message"])
    print("\n" + "="*50 + "\n")

    print("✅ Outreach layer test completed successfully!")