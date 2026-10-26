import json
import os
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import analysis

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data"))
FRONTEND_DIST = Path(os.getenv("FRONTEND_DIST", ROOT / "frontend" / "dist"))

actuals, forecasts = analysis.load_frames(
    json.loads((DATA_DIR / "actuals.json").read_text(encoding="utf-8")),
    json.loads((DATA_DIR / "forecasts.json").read_text(encoding="utf-8")),
)


@lru_cache(maxsize=24)
def _table(cutoff_hour: int):
    """Decision-time forecasts joined to actuals; cached per cutoff hour."""
    return analysis.decision_table(forecasts, actuals, cutoff_hour)


app = FastAPI(title="Wind forecast analysis")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["GET"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"status": "ok", "actual_rows": len(actuals), "forecast_rows": len(forecasts)}


@app.get("/api/config")
def config():
    return {"first_delivery": analysis.FIRST_DELIVERY,
            "last_delivery": analysis.LAST_DELIVERY,
            "default_cutoff_hour_utc": analysis.DEFAULT_CUTOFF_HOUR}


@app.get("/api/forecast-at-decision")
def forecast_at_decision(delivery_date: str = Query(..., description="YYYY-MM-DD"),
                         cutoff_hour: int = Query(analysis.DEFAULT_CUTOFF_HOUR, ge=0, le=23)):
    if not (analysis.FIRST_DELIVERY <= delivery_date <= analysis.LAST_DELIVERY):
        raise HTTPException(422, f"delivery_date must be between "
                                 f"{analysis.FIRST_DELIVERY} and {analysis.LAST_DELIVERY}")
    df = analysis.comparison(forecasts, actuals, delivery_date, cutoff_hour)
    if df.empty:
        raise HTTPException(404, "No forecast available at that decision time")
    band = analysis.error_band(_table(cutoff_hour), delivery_date)
    df = analysis.add_band(df, band)
    return {"delivery_date": delivery_date,
            "decision_time": analysis.decision_cutoff(delivery_date, cutoff_hour).isoformat(),
            "error_band": band,
            "day_metrics": analysis.error_metrics(
                analysis.forecast_at_decision(forecasts, delivery_date, cutoff_hour), actuals),
            "rows": analysis.to_records(df)}


@app.get("/api/metrics")
def metrics(cutoff_hour: int = Query(analysis.DEFAULT_CUTOFF_HOUR, ge=0, le=23)):
    overall = analysis.error_metrics(analysis.all_decisions(forecasts, cutoff_hour), actuals)
    return {"cutoff_hour_utc": cutoff_hour, "overall": overall,
            "daily": analysis.daily_metrics(forecasts, actuals, cutoff_hour)}


@app.get("/api/error-by-horizon")
def error_by_horizon():
    return analysis.error_by_horizon(forecasts, actuals)


@app.get("/api/error-by-hour")
def error_by_hour(cutoff_hour: int = Query(analysis.DEFAULT_CUTOFF_HOUR, ge=0, le=23)):
    return analysis.error_by_hour(_table(cutoff_hour))


@app.get("/api/error-by-level")
def error_by_level(cutoff_hour: int = Query(analysis.DEFAULT_CUTOFF_HOUR, ge=0, le=23)):
    return analysis.error_by_level(_table(cutoff_hour))


if FRONTEND_DIST.is_dir():
    # Registered last so /api/* keeps matching the routes above.
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
