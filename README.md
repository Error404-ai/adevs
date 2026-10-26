# Wind forecast review

Pilot web app for a UK energy utility’s day-ahead team. It shows the **national wind forecast that would have been available at purchase time**, then **quantifies how wrong those forecasts were** in January 2026.

Data is Elexon BMRS only: `FUELHH` (fuel type `WIND`) and `WINDFOR`. No other series.

Public GitHub repo: https://github.com/Error404-ai/adevs

Live app: **not deployed yet**. The Vercel configuration is included below, but publishing requires linking the repository to a Vercel account. Do not treat the local Docker URL as a public deployment.

AI tools: Cursor and Copilot SDK in VS Code were used to help build, review, and package this application.

## Files and directories

```
backend/
  app/analysis.py      Decision-time join and error metrics
  app/main.py          FastAPI routes; serves the built UI in production
  requirements.txt
  tests/               Unit tests for no-lookahead and error-band rules
data/
  actuals.json         FUELHH WIND, 1 Jan–1 Feb 2026
  forecasts.json       WINDFOR published 1–31 Jan 2026
frontend/              React (Vite) UI
scripts/
  fetch_data.py        Re-download the Elexon snapshot
  inspect_data.py      Sanity checks on the snapshot
  check_coverage.py    How many hours a given cutoff still covers
DEMO_SCRIPT.md         Recording outline for the customer pitch and technical review
Dockerfile             Multi-stage: build UI, run API + UI on one port
docker-compose.yml
pyproject.toml         Vercel FastAPI entrypoint and frontend build command
requirements.txt       Root dependency entrypoint for Vercel
vercel.json            Vercel function configuration and bundled data
```

## How the product maps to the brief

1. **Decision view** — for a delivery day, the latest `WINDFOR` published at or before the order cutoff on the previous day (default 09:00 UTC, selectable 06:00–12:00). No look-ahead. Hourly forecasts are held across both settlement half-hours so they line up with `FUELHH`.
2. **Forecast accuracy** — error = forecast − actual (MW). MAE, RMSE, bias, P90, and splits by day, hour, wind level, and forecast horizon. The shaded “likely range” on the decision chart uses only errors the buyer could already have seen (completed days up to D−2).

The cutoff is a product assumption (review in the morning before the GB day-ahead auction). In January the N2EX gate is 11:00 UTC; the control lets a buyer match their own process.

Delivery window: **2 Jan 2026 – 1 Feb 2026** (orders placed 1–31 Jan).

At the default 09:00 UTC cutoff, the pilot compares 1,488 half-hour points. In this snapshot MAE is about 2,042 MW, mean bias is +1,748 MW (forecast too high), and the 90th percentile absolute error is about 4,140 MW. These are retrospective pilot results, not a live trading recommendation.

## How to start

### Docker (preferred)

```bash
docker compose up --build
```

Open http://localhost:8000

### Local (two processes)

Python 3.11+ and Node 20+.

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 (Vite proxies `/api` to port 8000).

Tests:

```bash
cd backend
pytest
```

Re-fetch Elexon data (optional; snapshot is already in `data/`):

```bash
python scripts/fetch_data.py
```

## Deploy (Vercel)

The React frontend and FastAPI backend deploy together in one Vercel project.
Vercel runs the frontend build command from `pyproject.toml`, serves the built
React files through the FastAPI static mount, and deploys the FastAPI app as a
Python Function. The root `requirements.txt` points to the backend dependencies;
`vercel.json` includes the JSON snapshot and built frontend in the function bundle.

1. In Vercel, choose **Add New → Project** and import
   `Error404-ai/adevs` from GitHub.
2. Use the repository root (`.`) as the project root and **Other** as the
   framework preset. Keep the build settings defined by the checked-in config.
3. Deploy. Vercel builds the frontend and Python API together.
4. Verify the deployment root and `/api/health`, then replace the “Live app”
   status at the top of this README with the public Vercel URL.

Vercel supports [FastAPI as a Python Function](https://vercel.com/docs/frameworks/backend/fastapi).
This pilot's API and included January data fit the standard function bundle
limit; Docker Compose remains available for local development and reproducible
review.

## API

| Path | Purpose |
|---|---|
| `GET /api/health` | Row counts |
| `GET /api/config` | Delivery window and default cutoff |
| `GET /api/forecast-at-decision?delivery_date=YYYY-MM-DD&cutoff_hour=9` | Decision-time series + error band |
| `GET /api/metrics?cutoff_hour=9` | Overall and daily accuracy |
| `GET /api/error-by-horizon` | Error vs forecast lead time |
| `GET /api/error-by-hour?cutoff_hour=9` | Error by hour of delivery day |
| `GET /api/error-by-level?cutoff_hour=9` | Error by actual wind quartile |
