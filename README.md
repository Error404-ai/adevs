# Wind forecast review

Pilot web app for a UK energy utility's day-ahead team. It shows the **national wind forecast that would have been available at purchase time**, then **quantifies how wrong those forecasts were** in January 2026.

Data is Elexon BMRS only: `FUELHH` (fuel type `WIND`) and `WINDFOR`. No other series.

- Public GitHub repo: https://github.com/Error404-ai/adevs
- **Live app: https://adevs-nu.vercel.app**
- API health check: https://adevs-nu.vercel.app/api/health

AI tools: Cursor and Copilot SDK in VS Code were used to help build, review, and package this application.

## Files and directories

```
backend/
  app/analysis.py      Decision-time join and error metrics
  app/main.py          FastAPI API routes; serves UI in local Docker mode
  data/                Elexon snapshots bundled with the backend service
  requirements.txt     Runtime dependencies (UTF-8; tests need `pip install pytest`)
  tests/               Unit tests for no-lookahead and error-band rules
frontend/              React (Vite) UI
scripts/
  fetch_data.py        Re-download the Elexon snapshot
  inspect_data.py      Sanity checks on the snapshot
  check_coverage.py    How many hours a given cutoff still covers
DEMO_SCRIPT.md         Recording outline for the customer pitch and technical review
Dockerfile             Multi-stage: build UI, run API + UI on one port
docker-compose.yml
vercel.json            Vercel backend/frontend services and public routing
```

## How the product maps to the brief

1. **Decision view** — for a delivery day, the latest `WINDFOR` published at or before the order cutoff on the previous day (default 09:00 UTC, selectable 06:00–12:00). No look-ahead. Hourly forecasts are held across both settlement half-hours so they line up with `FUELHH`.
2. **Forecast accuracy** — error = forecast − actual (MW). MAE, RMSE, bias, P90, and splits by day, hour, wind level, and forecast horizon. The shaded "likely range" on the decision chart uses only errors the buyer could already have seen (completed days up to D−2).

The cutoff is a product assumption (review in the morning before the GB day-ahead auction). In January the N2EX gate is 11:00 UTC; the control lets a buyer match their own process.

Delivery window: **2 Jan 2026 – 1 Feb 2026** (orders placed 1–31 Jan).

### Headline results (default 09:00 UTC cutoff)

The pilot compares 1,488 half-hour points.

| Measure | Value |
|---|---|
| MAE (typical miss) | about 2,042 MW |
| RMSE | about 2,509 MW |
| Mean bias | +1,748 MW (forecast too high), 15.5% of actual output |
| P90 absolute error | about 4,140 MW |
| Days over-forecast | 27 of 31 |
| MAE if the average bias were removed | about 1,381 MW |

These are retrospective pilot results, not a live trading recommendation.

## How to start

### Docker (preferred for local review)

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

### Tests

`pytest` is a development dependency and is not in `backend/requirements.txt`, so the deployed function stays small.

```bash
cd backend
pip install pytest
pytest
```

### Re-fetch Elexon data

Optional; the snapshot is already in `backend/data/`.

```bash
python scripts/fetch_data.py
```

## Deploy (Vercel)

The React frontend and FastAPI backend deploy as separate Vercel services in
one project and share one public domain. `/api/*` is routed to the backend,
while all other paths are routed to the frontend. The browser calls the
same-origin `/api` paths, so no cross-service binding is needed: the frontend
is a static Vite app, and Vercel service bindings are for server-side
service-to-service calls.

1. In Vercel, choose **Add New → Project** and import
   `Error404-ai/adevs` from GitHub.
2. Use the repository root (`.`) as the Vercel project root. The checked-in
   `vercel.json` defines the independent `backend` and `frontend` service roots,
   frameworks, entrypoint, and public rewrites.
3. In **Settings → Build and Deployment**, set the project framework to
   **Services**. Vercel only builds a project as services when this setting is
   selected and `vercel.json` has a `services` key.
4. Deploy. Vercel builds the FastAPI backend and Vite frontend separately.
5. Verify `/api/health`. The bundled snapshot returns
   `{"status":"ok","actual_rows":1536,"forecast_rows":36208}`.

Notes:

- `backend/requirements.txt` must be saved as **UTF-8**. A UTF-16 file (for
  example from PowerShell's `>` redirect) makes the Vercel build fail with a
  `PYTHON_REQUIREMENTS_PARSE_ERROR`.
- The Vite build prints a chunk-size warning (about 580 kB). It is harmless
  for this pilot.
- Vercel supports [FastAPI as a Python Function](https://vercel.com/docs/frameworks/backend/fastapi).
  This pilot's API and included January data fit the standard function bundle
  limit; Docker Compose remains available for local development and
  reproducible review.

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

## Scope and limits

- National GB wind only, January 2026 only.
- The order cutoff is an assumption and is configurable (06:00–12:00 UTC).
- The "likely range" is the forecast shifted by the 10th and 90th percentile of earlier forecast errors. It is a rough planning aid, not a calibrated prediction interval.
- Validate the buyer's real decision cutoff and the interpretation of the error band with the trading team before any operational use.