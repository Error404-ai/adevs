"""Forecast-vs-actual analysis for GB wind generation (Elexon WINDFOR vs FUELHH).

Conventions
-----------
* error = forecast - actual (MW). Positive error = forecast too high (over-forecast).
* All timestamps are UTC. In January UTC == UK local time, so delivery days line up.
* A purchase decision for delivery day D is made on D-1 at `cutoff_hour_utc`.
  Only forecasts published at or before that moment may be used (no look-ahead).
"""
import pandas as pd

FIRST_DELIVERY = "2026-01-02"  # decided 1 Jan
LAST_DELIVERY = "2026-02-01"   # decided 31 Jan
DEFAULT_CUTOFF_HOUR = 9

HORIZON_BINS = [0, 6, 12, 18, 24, 36, 48, 72, 1000]
HORIZON_LABELS = ["0-6h", "6-12h", "12-18h", "18-24h", "24-36h", "36-48h", "48-72h", "72h+"]
LEVEL_LABELS = ["low", "mid-low", "mid-high", "high"]


# --------------------------------------------------------------------------- loading
def to_half_hourly(forecasts):
    """WINDFOR is hourly, FUELHH is half-hourly: hold each hourly forecast
    across both half-hours so every actual slot has a forecast to compare with."""
    second = forecasts.copy()
    second["startTime"] = second["startTime"] + pd.Timedelta(minutes=30)
    return pd.concat([forecasts, second], ignore_index=True)


def load_frames(actuals_rows, forecast_rows):
    actuals = pd.DataFrame(actuals_rows)
    forecasts = pd.DataFrame(forecast_rows)
    for df, cols in ((actuals, ["startTime"]), (forecasts, ["startTime", "publishTime"])):
        for c in cols:
            df[c] = pd.to_datetime(df[c], utc=True)
    actuals = actuals[["startTime", "generation"]].drop_duplicates("startTime")
    forecasts = to_half_hourly(forecasts[["startTime", "publishTime", "generation"]])
    return actuals, forecasts


# --------------------------------------------------------------------------- decision
def decision_cutoff(delivery_date, cutoff_hour_utc=DEFAULT_CUTOFF_HOUR):
    """The moment the buyer decides: day before delivery, at cutoff_hour (UTC)."""
    day = pd.Timestamp(delivery_date, tz="UTC")
    return day - pd.Timedelta(days=1) + pd.Timedelta(hours=cutoff_hour_utc)


def forecast_at_decision(forecasts, delivery_date, cutoff_hour_utc=DEFAULT_CUTOFF_HOUR):
    """For each half-hour of the delivery day, the latest forecast
    published at or before the decision cutoff (no look-ahead)."""
    cutoff = decision_cutoff(delivery_date, cutoff_hour_utc)
    day = pd.Timestamp(delivery_date, tz="UTC")
    in_day = forecasts[(forecasts.startTime >= day) &
                       (forecasts.startTime < day + pd.Timedelta(days=1))]
    known = in_day[in_day.publishTime <= cutoff]
    latest = (known.sort_values("publishTime")
                   .groupby("startTime", as_index=False).last())
    return latest.sort_values("startTime")


def comparison(forecasts, actuals, delivery_date, cutoff_hour_utc=DEFAULT_CUTOFF_HOUR):
    fc = forecast_at_decision(forecasts, delivery_date, cutoff_hour_utc)
    m = fc.merge(actuals, on="startTime", how="left", suffixes=("_forecast", "_actual"))
    return m.rename(columns={"generation_forecast": "forecast",
                             "generation_actual": "actual"})


def all_decisions(forecasts, cutoff_hour_utc=DEFAULT_CUTOFF_HOUR):
    days = pd.date_range(FIRST_DELIVERY, LAST_DELIVERY, freq="D")
    frames = [forecast_at_decision(forecasts, d.date().isoformat(), cutoff_hour_utc)
              for d in days]
    return pd.concat(frames, ignore_index=True)


def decision_table(forecasts, actuals, cutoff_hour_utc=DEFAULT_CUTOFF_HOUR):
    """Every decision-time forecast joined to its actual, with error columns."""
    d = all_decisions(forecasts, cutoff_hour_utc)
    m = d.merge(actuals, on="startTime", suffixes=("_fc", "_act"))
    m = m.rename(columns={"generation_fc": "forecast", "generation_act": "actual"})
    m["error"] = m.forecast - m.actual
    m["delivery_date"] = m.startTime.dt.floor("D")
    m["hour"] = m.startTime.dt.hour
    m["horizon_h"] = (m.startTime - m.publishTime).dt.total_seconds() / 3600
    return m


# --------------------------------------------------------------------------- metrics
def error_metrics(forecast_df, actuals):
    """Compare forecast with actuals; error = forecast - actual (MW)."""
    m = forecast_df.merge(actuals, on="startTime", suffixes=("_fc", "_act"))
    if m.empty:
        return {"n": 0}
    err = m.generation_fc - m.generation_act
    mean_actual = float(m.generation_act.mean())
    return {
        "n": int(len(m)),
        "mae": float(err.abs().mean()),
        "rmse": float((err ** 2).mean() ** 0.5),
        "bias": float(err.mean()),
        "bias_pct_of_actual": float(err.mean() / mean_actual * 100) if mean_actual else None,
        "mae_bias_removed": float((err - err.mean()).abs().mean()),
        "p90_abs_error": float(err.abs().quantile(0.9)),
        "p10_error": float(err.quantile(0.1)),
        "p90_error": float(err.quantile(0.9)),
        "mean_forecast": float(m.generation_fc.mean()),
        "mean_actual": mean_actual,
    }


def daily_metrics(forecasts, actuals, cutoff_hour_utc=DEFAULT_CUTOFF_HOUR):
    rows = []
    for d in pd.date_range(FIRST_DELIVERY, LAST_DELIVERY, freq="D"):
        day = d.date().isoformat()
        fc = forecast_at_decision(forecasts, day, cutoff_hour_utc)
        if len(fc):
            rows.append({"date": day, **error_metrics(fc, actuals)})
    return rows


def error_band(table, delivery_date, min_days=3):
    """Typical-error band for a delivery day, using ONLY errors the buyer could
    already have observed: days up to D-2 (day D-1 is still in progress at decision
    time). Returns None when there is not enough history yet."""
    d = pd.Timestamp(delivery_date, tz="UTC")
    hist = table[table.delivery_date <= d - pd.Timedelta(days=2)]
    n_days = int(hist.delivery_date.nunique())
    if n_days < min_days:
        return None
    return {"p10_error": float(hist.error.quantile(0.1)),
            "p90_error": float(hist.error.quantile(0.9)),
            "bias": float(hist.error.mean()),
            "history_days": n_days}


def add_band(df, band):
    """Add band_low/band_high columns: the range the actual is likely to fall in."""
    out = df.copy()
    if band is None:
        out["band_low"] = None
        out["band_high"] = None
    else:
        out["band_low"] = (out.forecast - band["p90_error"]).clip(lower=0)
        out["band_high"] = out.forecast - band["p10_error"]
    return out


def error_by_hour(table):
    g = table.groupby("hour").error
    out = pd.DataFrame({"mae": g.apply(lambda s: s.abs().mean()),
                        "bias": g.mean(), "n": g.size()}).reset_index()
    return out.to_dict("records")


def error_by_level(table):
    """Error split by how windy it actually was (quartiles of actual output)."""
    t = table.copy()
    t["level"], bins = pd.qcut(t.actual, 4, labels=LEVEL_LABELS, retbins=True)
    g = t.groupby("level", observed=True).error
    out = pd.DataFrame({"mae": g.apply(lambda s: s.abs().mean()),
                        "bias": g.mean(), "n": g.size()}).reset_index()
    out["range_mw"] = [f"{bins[i]:,.0f}-{bins[i + 1]:,.0f}" for i in range(len(out))]
    out["level"] = out.level.astype(str)
    return out.to_dict("records")


def error_by_horizon(forecasts, actuals):
    """Error vs how far ahead the forecast was published (all forecasts, not only
    decision-time ones). Forecasts published after their target time are excluded."""
    m = forecasts.merge(actuals, on="startTime", suffixes=("_fc", "_act"))
    m["horizon_h"] = (m.startTime - m.publishTime).dt.total_seconds() / 3600
    m = m[m.horizon_h >= 0].copy()
    m["err"] = m.generation_fc - m.generation_act
    m["bucket"] = pd.cut(m.horizon_h, HORIZON_BINS, right=False, labels=HORIZON_LABELS)
    g = m.groupby("bucket", observed=True).err
    out = pd.DataFrame({"mae": g.apply(lambda s: s.abs().mean()),
                        "bias": g.mean(), "n": g.size()}).reset_index()
    out["bucket"] = out.bucket.astype(str)
    return out.to_dict("records")


# --------------------------------------------------------------------------- output
def to_records(df):
    out = df.copy()
    for c in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[c]):
            out[c] = out[c].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return out.astype(object).where(out.notna(), None).to_dict("records")