# Recording outline (maximum 10 minutes)

Record the screen and narration in one take if possible. Keep Part 1 and Part 2
to about four minutes each, which leaves a buffer under the 10-minute limit.

Use the live deployment for the demo:

```
https://adevs-nu.vercel.app
```

Keep `docker compose up --build` (http://localhost:8000) ready as a fallback.
Before recording, run `cd backend && pytest` and `cd frontend && npm run build`
once so you can quote the real results. After recording, upload the video to
YouTube as **Unlisted**, test the link in an incognito window, and add the URL
to the submission form. The recording itself is not stored in this repository.

## Part 1 — Customer pitch (about 4 minutes)

**0:00–0:30 — The decision**

"A day-ahead buyer has to commit before delivery, while wind output is still
uncertain. This pilot answers two practical questions. First: what national wind
forecast was actually available at the order cutoff? Second: how accurate have
those forecasts been?"

**0:30–2:30 — Decision view**

- Open the app on the Decision view. Point out the delivery day and the
  **Order placed at** control (default 09:00 UTC). Explain that the app only
  uses forecasts published on or before the previous-day cutoff, and that the
  cutoff can be changed to match a team's own process.
- Select **15 January 2026**. The forecast available at 09:00 on 14 January
  averages about **11,610 MW**. The likely range of actual output averages about
  **7,042 to 12,579 MW**.
- Explain the shaded range: it is the forecast adjusted by the middle 80% of
  forecast errors the buyer had already seen (completed days only, up to D−2).
  Over the 12 completed days before this decision, the forecast had run about
  1,750 MW too high.
- Point to the black actual line. Explain that actuals are shown for evaluation
  only; they were not known at purchase time. On this day actual output
  averaged about **10,568 MW**, so the forecast was about **1,042 MW too high**.
- Open **Half-hourly values (48 rows)** to show the numbers behind the chart.

**2:30–4:00 — Accuracy view**

- Switch to **Forecast accuracy**. Explain the measures in plain language:
  MAE (typical miss), RMSE (big misses count more), bias (direction of error)
  and P90 (nine in ten half-hours miss by less than this).
- At the 09:00 UTC cutoff, 1,488 half-hour points give: MAE about **2,042 MW**,
  RMSE about **2,509 MW**, bias **+1,748 MW** (15.5% of actual output) and P90
  about **4,140 MW**. Positive means the forecast was too high.
- Key message: the forecast was too high on **27 of 31 days**. If the average
  bias were removed, the typical miss would fall from about 2,042 to 1,381 MW,
  so roughly a third of the miss is a steady bias that a buyer can plan for.
- Briefly show the other charts: largest over-forecast around 05:00
  (+2,358 MW), over-forecast largest in mid-high wind (+2,334 MW), and average
  miss growing from about 1,760 MW for forecasts published 0–6 hours ahead to
  about 2,308 MW at 48–72 hours ahead.
- Close by saying these figures help a buyer account for forecast uncertainty.
  They are retrospective pilot results, not a dispatch or trading
  recommendation.

## Part 2 — Technical review and handover (about 4 minutes)

**0:00–0:45 — Architecture**

"The frontend is React with Vite and Recharts. FastAPI exposes read-only
analysis endpoints. In production on Vercel these are two services on one
domain: `/api/*` is routed to the FastAPI backend and everything else to the
static frontend. The checked-in JSON files are a reproducible January snapshot,
so the demo does not depend on a live Elexon call."

- Show `vercel.json` (services plus rewrites) and open
  `https://adevs-nu.vercel.app/api/health` in the browser. It returns 1,536
  actual rows and 36,208 forecast rows.

**0:45–2:15 — Data and analysis**

- Show `scripts/fetch_data.py`: the only sources are Elexon `FUELHH` filtered
  to `WIND`, and `WINDFOR`.
- Show `backend/app/analysis.py`:
  - Timestamps are UTC, which matches UK local time in January.
  - Hourly `WINDFOR` values are held across two half-hours to compare with
    half-hourly `FUELHH`.
  - `forecast_at_decision` keeps only forecasts published at or before the
    cutoff and takes the latest per slot, so there is no look-ahead.
- Explain the sign convention (error = forecast − actual) and the aggregate
  metrics.
- Explain why the historical error range stops at D−2: the actual errors for
  day D−1 are not yet observable when the buyer decides for day D.
- State the scope limits: national wind only, January 2026 only, and a
  configurable cutoff defaulting to 09:00 UTC.

**2:15–3:15 — Code and quality**

- Point to `backend/app/main.py` for the API routes and the optional static
  serving used in Docker, `frontend/src/views/` for the two workflows, and
  `backend/tests/test_analysis.py` for the no-lookahead, half-hourly alignment,
  error-sign, empty-data, horizon and error-band tests.
- Report only the checks you actually ran just before recording, for example:
  the backend tests pass (seven tests), `npm run build` succeeds, the Vercel
  deployment is healthy, and (if you ran it) `docker compose up --build`
  serves the API and UI on port 8000.

**3:15–4:00 — Operations and next steps**

- Show `Dockerfile` and `docker-compose.yml`: a multi-stage build that compiles
  the UI and serves the API and UI on one port.
- State that the app is deployed on Vercel at https://adevs-nu.vercel.app. The
  Vercel project framework is set to **Services**, and `requirements.txt` must
  be UTF-8 or the Python build fails.
- Close with next pilot steps: validate the buyer's real decision cutoff,
  confirm the interpretation of the error band with the trading team, and extend
  beyond January 2026 before any operational use.