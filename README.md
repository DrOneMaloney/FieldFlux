# FieldFlux Billing Prototype

This repository adds a lightweight billing layer for FieldFlux with a FastAPI backend and a static HTML dashboard.

## Backend

The backend lives under `backend/app`.

* Models: Farmers, Fields, Invoices, LineItems, PaymentRecords with tax/discount handling.
* Endpoints for creating invoices, rendering HTML/PDF, updating status, recording payments, and checking farmer balance.
* SQLite storage via SQLAlchemy.

### Running the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Frontend

A lightweight dashboard lives in `frontend/` and expects the backend on `http://localhost:8000`.

Open `frontend/index.html` in your browser to:

* Create farmers and fields.
* Build invoices with line items and field application references.
* Send invoices, record payments, and open HTML/PDF previews.
# FieldFlux

FieldFlux is a simple Flask + Leaflet application for mapping farm fields, validating overlaps, and tracking acreage per farmer.

## Getting started

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:

   ```bash
   python app.py
   ```

3. Open the mapper UI at `http://localhost:5000`.

## Features

- CRUD APIs for farmers and fields under `/api`.
- GeoJSON polygon storage with acreage calculations using an equal-area projection.
- Overlap validation to prevent overlapping fields for the same farmer.
- Leaflet map with drawing/editing tools and satellite/streets base layers.
- Farmer summary table showing field counts and total acres.
FieldFlux is a web application that can be used to track fertilizer and chemical data on fields. Go back to past years and see field performance. And allow a place to export data on all fields on a farm.

## Getting started

### Backend

The API is built with FastAPI and SQLModel.

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Mutating endpoints (creating fields or events) expect an `X-Role` header of `admin` or `manager`.

### Frontend

Open `frontend/index.html` in a browser while the backend is running on `http://localhost:8000`. Use the UI to create fields, add application events, filter timelines, export data, and view seasonal summaries.
FieldFlux is a web application for tracking fertilizer and chemical data on fields, comparing historical performance, and exporting records for growers.

## Environment configuration
Use environment variables (or your secret manager of choice) to supply credentials and API keys. Copy `.env.example` to `.env` for local work, and inject the same keys through your secret manager in CI/CD:

- `DATABASE_URL` — Postgres connection string
- `REDIS_URL` — Redis instance for caching/queues
- `ANALYTICS_WRITE_KEY` — telemetry destination (e.g., Segment)
- `ERROR_MONITOR_DSN` — error monitoring endpoint (e.g., Sentry)
- `SECRET_KEY`, `ENVIRONMENT` — application bootstrap settings

These values are surfaced through the application healthcheck (`FieldFluxApp.healthcheck`) to ensure required keys are present. The mapper now uses free, open-source OpenStreetMap/Esri imagery tiles and no longer needs map API credentials.

## Development setup
1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
3. Export environment variables (or create a `.env` file) for database and API keys.
4. Run tests and lint checks:
   ```bash
   pytest
   ruff check .
   ```

## Testing and permissions
Automated tests cover authentication, CRUD flows, and role-based permissions through the in-memory `FieldFluxApp`. The app enforces:
- Admin: create/read/update/delete
- Editor: create/read/update
- Viewer: read-only

## Telemetry and error monitoring
`fieldflux.telemetry` captures feature-usage events and error traces. In production wire these sinks to your analytics platform and monitoring provider; the stubs in this repository make it easy to integrate SDKs later.

## Seeding data
Use `python scripts/seed_data.py` to load sample fields into a running environment. See `docs/staging.md` for the staging playbook and map domain setup.

## Continuous Integration
GitHub Actions (`.github/workflows/ci.yml`) runs linting (`ruff`) and tests (`pytest`) to protect mainline merges. Extend the workflow with deployment steps as environments become available.
FieldFlux is a web application that can be used to track fertilizer and chemical data on fields. Go back to past years and see field performance. And allow a place to export data on all fields on a farm.

## Authentication stack

This repository now includes a FastAPI-based authentication service with a simple HTML frontend for testing.

### Backend

* Framework: FastAPI
* Database: SQLite (`fieldflux.db`)
* Passwords: bcrypt hashing via `passlib`
* Tokens: JWT access + refresh tokens (30 minutes access, 14 days refresh by default)
* Extras: basic in-memory rate limiting, password reset & email verification token hooks, refresh token rotation.

Run the API:

```bash
pip install -r requirements.txt
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

A lightweight HTML/JS client lives in `frontend/` with forms for signup, login/logout, and password reset. Update `API_BASE` in `frontend/app.js` if your backend runs on a different host/port.

Open the file directly or serve it from a static server:

```bash
python -m http.server 3000 --directory frontend
```

Then browse to `http://localhost:3000` and test against the API.

### Running in GitHub Codespaces

1. Start the API (port 8000) and static frontend (port 3000) in separate terminals:
   ```bash
   pip install -r requirements.txt
   uvicorn server.main:app --host 0.0.0.0 --port 8000
   # in another terminal
   python -m http.server 3000 --directory frontend
   ```
2. In the Codespaces "Ports" panel, mark ports **8000** and **3000** as public. FastAPI will be reachable at `https://<codespace>-8000.app.github.dev` and the frontend at `https://<codespace>-3000.app.github.dev`.
3. Open the frontend URL; it auto-detects Codespaces hosts and calls the API through the `-8000` forwarded domain. If you host the API elsewhere, update `API_BASE` in `frontend/app.js` accordingly.
