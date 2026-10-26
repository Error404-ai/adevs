import json
from datetime import date, timedelta
from pathlib import Path

import requests

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
# Keep snapshots inside the independently deployed backend service.
OUT = Path(__file__).resolve().parent.parent / "backend" / "data"
OUT.mkdir(exist_ok=True)


def get(path, params):
    r = requests.get(f"{BASE}/{path}", params=params, timeout=60)
    if not r.ok:
        raise SystemExit(f"HTTP {r.status_code} for {r.url}\n{r.text[:500]}")
    return r.json()


def fetch_actuals(start, end):
    rows, d = [], start
    while d <= end:
        chunk_end = min(d + timedelta(days=6), end)
        print(f"actuals {d} -> {chunk_end}", flush=True)
        rows += get("FUELHH/stream", {
            "settlementDateFrom": d.isoformat(),
            "settlementDateTo": chunk_end.isoformat(),
            "fuelType": "WIND",
        })
        d = chunk_end + timedelta(days=1)
    return rows


def fetch_forecasts(start, end):
    rows, d = [], start
    while d <= end:
        nxt = d + timedelta(days=1)
        print(f"forecasts published {d}", flush=True)
        rows += get("WINDFOR/stream", {
            "publishDateTimeFrom": f"{d.isoformat()}T00:00:00Z",
            "publishDateTimeTo": f"{nxt.isoformat()}T00:00:00Z",
        })
        d = nxt
    return rows


if __name__ == "__main__":
    actuals = fetch_actuals(date(2026, 1, 1), date(2026, 2, 1))
    forecasts = fetch_forecasts(date(2026, 1, 1), date(2026, 1, 31))
    (OUT / "actuals.json").write_text(json.dumps(actuals))
    (OUT / "forecasts.json").write_text(json.dumps(forecasts))
    print(len(actuals), "actual rows;", len(forecasts), "forecast rows")
    print(actuals[:2])
    print(forecasts[:2])