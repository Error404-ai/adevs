import pandas as pd

FIRST_DELIVERY = "2026-01-02"  # decided 1 Jan
LAST_DELIVERY = "2026-02-01"   # decided 31 Jan


def load_frames(actuals_rows, forecast_rows):
    actuals = pd.DataFrame(actuals_rows)
    forecasts = pd.DataFrame(forecast_rows)
    for df, cols in ((actuals, ["startTime"]), (forecasts, ["startTime", "publishTime"])):
        for c in cols:
            df[c] = pd.to_datetime(df[c], utc=True)
    actuals = actuals[["startTime", "generation"]].drop_duplicates("startTime")
    forecasts = forecasts[["startTime", "publishTime", "generation"]]
    return actuals, forecasts


def decision_cutoff(delivery_date, cutoff_hour_utc=9):
    """The moment the buyer decides: day before delivery, at cutoff_hour (UTC)."""
    day = pd.Timestamp(delivery_date, tz="UTC")
    return day - pd.Timedelta(days=1) + pd.Timedelta(hours=cutoff_hour_utc)


def forecast_at_decision(forecasts, delivery_date, cutoff_hour_utc=9):
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


def error_metrics(forecast_df, actuals):
    """Compare forecast with actuals; error = forecast - actual (MW)."""
    m = forecast_df.merge(actuals, on="startTime", suffixes=("_fc", "_act"))
    err = m.generation_fc - m.generation_act
    return {
        "n": int(len(m)),
        "mae": float(err.abs().mean()),
        "rmse": float((err ** 2).mean() ** 0.5),
        "bias": float(err.mean()),
        "p90_abs_error": float(err.abs().quantile(0.9)),
    }


def to_records(df):
    out = df.copy()
    for c in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[c]):
            out[c] = out[c].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return out.astype(object).where(out.notna(), None).to_dict("records")


def comparison(forecasts, actuals, delivery_date, cutoff_hour_utc=9):
    fc = forecast_at_decision(forecasts, delivery_date, cutoff_hour_utc)
    m = fc.merge(actuals, on="startTime", how="left",
                 suffixes=("_forecast", "_actual"))
    return m.rename(columns={"generation_forecast": "forecast",
                             "generation_actual": "actual"})


def all_decisions(forecasts, cutoff_hour_utc=9):
    days = pd.date_range(FIRST_DELIVERY, LAST_DELIVERY, freq="D")
    frames = [forecast_at_decision(forecasts, d.date().isoformat(), cutoff_hour_utc)
              for d in days]
    return pd.concat(frames, ignore_index=True)


def daily_metrics(forecasts, actuals, cutoff_hour_utc=9):
    rows = []
    for d in pd.date_range(FIRST_DELIVERY, LAST_DELIVERY, freq="D"):
        day = d.date().isoformat()
        fc = forecast_at_decision(forecasts, day, cutoff_hour_utc)
        if len(fc):
            rows.append({"date": day, **error_metrics(fc, actuals)})
    return rows


def error_by_horizon(forecasts, actuals):
    """Error vs how far ahead the forecast was published (all forecasts)."""
    m = forecasts.merge(actuals, on="startTime", suffixes=("_fc", "_act"))
    m["horizon_h"] = (m.startTime - m.publishTime).dt.total_seconds() / 3600
    m = m[m.horizon_h >= 0]
    m["err"] = m.generation_fc - m.generation_act
    bins = [0, 6, 12, 18, 24, 36, 48, 72, 1000]
    m["bucket"] = pd.cut(m.horizon_h, bins, right=False)
    g = m.groupby("bucket", observed=True).err
    out = pd.DataFrame({"mae": g.apply(lambda s: s.abs().mean()),
                        "bias": g.mean(), "n": g.size()}).reset_index()
    out["bucket"] = out.bucket.astype(str)
    return out.to_dict("records")