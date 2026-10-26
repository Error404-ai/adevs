import pandas as pd


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