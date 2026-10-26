import pandas as pd
from app.analysis import forecast_at_decision, error_metrics


def test_no_lookahead_and_latest_wins():
    fc = pd.DataFrame({
        "startTime": pd.to_datetime(["2026-01-10 12:00"] * 3, utc=True),
        "publishTime": pd.to_datetime(
            ["2026-01-09 06:00", "2026-01-09 08:00", "2026-01-09 10:00"], utc=True),
        "generation": [100, 200, 999],
    })
    out = forecast_at_decision(fc, "2026-01-10", cutoff_hour_utc=9)
    assert out.generation.iloc[0] == 200  # 10:00 publish is after cutoff


def test_error_metrics():
    f = pd.DataFrame({"startTime": pd.to_datetime(["2026-01-10"], utc=True),
                      "generation": [110.0]})
    a = pd.DataFrame({"startTime": pd.to_datetime(["2026-01-10"], utc=True),
                      "generation": [100.0]})
    assert error_metrics(f, a)["bias"] == 10.0