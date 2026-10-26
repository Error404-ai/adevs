# Recording outline (maximum 10 minutes)

Record the screen and narration in one take if possible. Keep Part 1 and Part 2
to five minutes or less each. Use Docker Compose so the reviewer sees the same
single-origin app used by the container deployment:

```bash
docker compose up --build
```

Open `http://localhost:8000`. The recording is not included in this repository;
after recording, upload it as an unlisted YouTube video and add that URL to the
submission form.

## Part 1 — Customer pitch (about 4 minutes)

**0:00–0:30 — The decision**

“A day-ahead buyer has to act before delivery, while wind output is uncertain.
This pilot answers two practical questions: what national wind forecast was
actually available at the order cutoff, and how accurate have those forecasts
been?”

**0:30–2:30 — Decision view**

- Point out the selected delivery date and order cutoff. Explain that the app
  selects only forecasts published on or before the previous-day cutoff; the
  cutoff is configurable to match a team process.
- For 15 January 2026 at the default 09:00 UTC cutoff, show the forecast
  profile, the retrospective actual profile, and the shaded range derived
  from earlier observed forecast errors.
- Explain that actuals are shown for evaluation only: they were not known when
  the purchase decision was made.
- Open the half-hourly table to show the values behind the chart and the
  forecast-versus-actual error.

**2:30–4:00 — Accuracy view**

- Switch to Forecast accuracy and explain MAE (typical miss), RMSE (larger
  misses count more), bias (direction of error), and P90 absolute error.
- At the 09:00 UTC cutoff, the January snapshot has 1,488 comparison points:
  approximately 2,042 MW MAE, +1,748 MW mean bias, and 4,140 MW P90 absolute
  error. Positive bias means wind was over-forecast.
- Briefly show daily bias and the hour, horizon, and actual-output-level
  breakdowns. Close with how these measures help a buyer account for forecast
  uncertainty; do not present them as a dispatch or trading recommendation.

## Part 2 — Technical review and handover (about 4 minutes)

**0:00–0:45 — Architecture**

“The frontend is React with Vite and Recharts. FastAPI exposes read-only
analysis endpoints. The Dockerfile builds the frontend and runs the API and
static frontend together on one port. The checked-in JSON files are a
reproducible January snapshot, so the demo does not depend on a live API call.”

**0:45–2:15 — Data and analysis**

- Show `scripts/fetch_data.py`: the only sources are Elexon `FUELHH` filtered
  to `WIND` and `WINDFOR`.
- Show `backend/app/analysis.py`: timestamps are UTC; hourly WINDFOR values
  are held across two half-hours to compare with FUELHH; each delivery slot
  uses the latest publish timestamp no later than the decision cutoff.
- Explain the error sign convention (forecast minus actual), the aggregate
  metrics, and why the historical range excludes delivery day D−1: its
  actual errors are not yet observable when the buyer decides for day D.
- Mention the scope limits: national wind only, January 2026, and a
  configurable cutoff defaulting to 09:00 UTC.

**2:15–3:15 — Code and quality**

- Point to `backend/app/main.py` for the API routes and production static
  serving, `frontend/src/views/` for the two workflows, and
  `backend/tests/test_analysis.py` for no-lookahead, half-hourly alignment,
  and metric tests.
- Report the checks run: seven backend tests pass; `npm run build` succeeds;
  `docker compose build` succeeds; and a container smoke test returned a
  healthy API, the React page, and 48 half-hour forecast rows.

**3:15–4:00 — Operations and next steps**

- Show `docker-compose.yml`, `Dockerfile`, and `heroku.yml`. Explain local
  startup with `docker compose up --build`.
- State clearly that the repository is public but the app has not yet been
  deployed; a hosting account and an actual deployment are still required
  before sharing a public app URL.
- Close with next pilot steps: validate the buyer's actual decision cutoff
  and confirm the interpretation of forecast error bands with the trading
  team before operational use.
