import json
from pathlib import Path
import pandas as pd

D = Path(__file__).resolve().parent.parent / "backend" / "data"
a = pd.DataFrame(json.loads((D / "actuals.json").read_text()))
f = pd.DataFrame(json.loads((D / "forecasts.json").read_text()))
for c in ("startTime", "publishTime"):
    f[c] = pd.to_datetime(f[c], utc=True)
a["startTime"] = pd.to_datetime(a["startTime"], utc=True)

f["horizon_h"] = (f.startTime - f.publishTime).dt.total_seconds() / 3600
print("forecast start minutes:", sorted(f.startTime.dt.minute.unique()))
print("forecast publish minutes:", sorted(f.publishTime.dt.minute.unique()))
print("publishes per day (distinct publishTime):")
print(f.groupby(f.publishTime.dt.date).publishTime.nunique().describe())
print("horizon_h min/median/max:", f.horizon_h.min(), f.horizon_h.median(), f.horizon_h.max())
print("negative-horizon rows:", int((f.horizon_h < 0).sum()), "of", len(f))
print("duplicate (startTime, publishTime):", int(f.duplicated(["startTime", "publishTime"]).sum()))
print("forecast startTime range:", f.startTime.min(), "->", f.startTime.max())
print("actual rows matching a forecast startTime:",
      int(a.startTime.isin(f.startTime).sum()), "of", len(a))