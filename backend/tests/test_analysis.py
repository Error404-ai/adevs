import pandas as pd
import pytest

from app.analysis import (add_band, error_band, error_by_horizon, error_metrics,
                          forecast_at_decision, to_half_hourly)


def ts(*s):
    return pd.to_datetime(list(s), utc=True)


def test_no_lookahead_and_latest_wins():
    fc = pd.DataFrame({
        "startTime": ts(*["2026-01-10 12:00"] * 3),
        "publishTime": ts("2026-01-09 06:00", "2026-01-09 08:00", "2026-01-09 10:00"),
        "generation": [100, 200, 999],
    })
    out = forecast_at_decision(fc, "2026-01-10", cutoff_hour_utc=9)
    assert out.generation.iloc[0] == 200  # 10:00 publish is after the cutoff


def test_error_metrics_bias_and_sign():
    f = pd.DataFrame({"startTime": ts("2026-01-10"), "generation": [110.0]})
    a = pd.DataFrame({"startTime": ts("2026-01-10"), "generation": [100.0]})
    m = error_metrics(f, a)
    assert m["bias"] == 10.0 and m["mae"] == 10.0


def test_error_metrics_empty_is_safe():
    f = pd.DataFrame({"startTime": ts("2026-01-10"), "generation": [1.0]})
    a = pd.DataFrame({"startTime": ts("2026-01-11"), "generation": [1.0]})
    assert error_metrics(f, a) == {"n": 0}


def test_half_hourly_expansion():
    fc = pd.DataFrame({"startTime": ts("2026-01-10 12:00"),
                       "publishTime": ts("2026-01-09 06:00"), "generation": [100]})
    out = to_half_hourly(fc).sort_values("startTime")
    assert list(out.startTime.dt.minute) == [0, 30]
    assert list(out.generation) == [100, 100]


def test_error_by_horizon_excludes_negative_horizon():
    fc = pd.DataFrame({
        "startTime": ts("2026-01-10 12:00", "2026-01-10 12:00"),
        "publishTime": ts("2026-01-10 06:00", "2026-01-10 18:00"),  # 2nd is after target
        "generation": [110, 500]})
    a = pd.DataFrame({"startTime": ts("2026-01-10 12:00"), "generation": [100]})
    out = error_by_horizon(fc, a)
    assert sum(r["n"] for r in out) == 1 and out[0]["bias"] == 10


def _table(days, err):
    return pd.DataFrame({
        "delivery_date": pd.to_datetime([f"2026-01-{d:02d}" for d in days], utc=True),
        "error": err})


def test_error_band_uses_only_observable_history():
    t = _table([2, 3, 4, 5, 6], [10, 20, 30, 1000, 1000])
    # delivery 6 Jan -> history is days <= 4 Jan only (5 Jan not observable yet)
    b = error_band(t, "2026-01-06")
    assert b["history_days"] == 3 and b["bias"] == pytest.approx(20)
    assert error_band(t, "2026-01-03") is None  # not enough history


def test_add_band_offsets():
    df = pd.DataFrame({"forecast": [1000.0]})
    out = add_band(df, {"p10_error": -100.0, "p90_error": 400.0})
    assert out.band_low.iloc[0] == 600 and out.band_high.iloc[0] == 1100