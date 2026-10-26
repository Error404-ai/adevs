import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import analysis

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parents[2] / "data"))

actuals, forecasts = analysis.load_frames(
    json.loads((DATA_DIR / "actuals.json").read_text()),
    json.loads((DATA_DIR / "forecasts.json").read_text()),
)

app = FastAPI(title="Wind forecast analysis")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["GET"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"status": "ok", "actual_rows": len(actuals), "forecast_rows": len(forecasts)}


@app.get("/api/forecast-at-decision")
def forecast_at_decision(delivery_date: str = Query(..., description="YYYY-MM-DD"),
                         cutoff_hour: int = Query(9, ge=0, le=23)):
    if not (analysis.FIRST_DELIVERY <= delivery_date <= analysis.LAST_DELIVERY):
        raise HTTPException(422, f"delivery_date must be between "
                                 f"{analysis.FIRST_DELIVERY} and {analysis.LAST_DELIVERY}")
    df = analysis.comparison(forecasts, actuals, delivery_date, cutoff_hour)
    if df.empty:
        raise HTTPException(404, "No forecast available at that decision time")
    return {"delivery_date": delivery_date,
            "decision_time": analysis.decision_cutoff(delivery_date, cutoff_hour).isoformat(),
            "rows": analysis.to_records(df)}


@app.get("/api/metrics")
def metrics(cutoff_hour: int = Query(9, ge=0, le=23)):
    overall = analysis.error_metrics(analysis.all_decisions(forecasts, cutoff_hour), actuals)
    return {"cutoff_hour_utc": cutoff_hour, "overall": overall,
            "daily": analysis.daily_metrics(forecasts, actuals, cutoff_hour)}


@app.get("/api/error-by-horizon")
def error_by_horizon():
    return analysis.error_by_horizon(forecasts, actuals)