import json
from pathlib import Path
import pandas as pd

D = Path(__file__).resolve().parent.parent / "data"
f = pd.DataFrame(json.loads((D / "forecasts.json").read_text()))
for c in ("startTime", "publishTime"):
    f[c] = pd.to_datetime(f[c], utc=True)

print("publish hours (UTC):", sorted(f.publishTime.dt.hour.unique()))

for cutoff in (6, 9, 12):
    counts = []
    for d in pd.date_range("2026-01-02", "2026-02-01", freq="D", tz="UTC"):
        cut = d - pd.Timedelta(days=1) + pd.Timedelta(hours=cutoff)
        day = f[(f.startTime >= d) & (f.startTime < d + pd.Timedelta(days=1))]
        counts.append(day[day.publishTime <= cut].startTime.nunique())
    print(f"cutoff {cutoff:02d}:00 -> hours covered per day: min {min(counts)}, max {max(counts)}")