# FieldFlux

FieldFlux is a web application for tracking fertilizer and chemical data on fields, comparing historical performance, and exporting records for growers.

## Environment configuration
Use environment variables (or your secret manager of choice) to supply credentials and API keys. Copy `.env.example` to `.env` for local work, and inject the same keys through your secret manager in CI/CD:

- `DATABASE_URL` — Postgres connection string
- `REDIS_URL` — Redis instance for caching/queues
- `MAPS_API_KEY` / `MAP_DOMAIN` — map provider API key and staging domain
- `ANALYTICS_WRITE_KEY` — telemetry destination (e.g., Segment)
- `ERROR_MONITOR_DSN` — error monitoring endpoint (e.g., Sentry)
- `SECRET_KEY`, `ENVIRONMENT` — application bootstrap settings

These values are surfaced through the application healthcheck (`FieldFluxApp.healthcheck`) to ensure required keys are present.

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
