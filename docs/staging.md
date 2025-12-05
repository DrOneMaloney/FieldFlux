# Staging Environment Playbook

## Purpose
The staging environment mirrors production integrations for map rendering, domain configuration, and data access while allowing safe testing of new builds.

## Map API & Domain
1. Provision a dedicated map API key in the provider console and scope it to the staging domain.
2. Create the staging domain entry (e.g., `staging.maps.fieldflux.example.com`) and configure DNS to point to the staging load balancer.
3. Store the key and domain in the secret manager under `projects/fieldflux/staging/maps` and expose them via environment variables (`MAPS_API_KEY`, `MAP_DOMAIN`).
4. Validate map tile responses using curl against the staging domain and ensure CORS headers allow the staging web origin.

## Database & Seed Data
1. Provision a managed Postgres instance with restricted network access.
2. Run `python scripts/seed_data.py` after exporting `DATABASE_URL` to load baseline field records for testing.
3. Enable automated nightly refresh of seed data for repeatable QA.

## CI/CD
- Gate deployments on passing linting and tests (see `.github/workflows/ci.yml`).
- Promote artifacts to staging only after successful checks and manual approval.

## Observability
- Configure `ANALYTICS_WRITE_KEY` and `ERROR_MONITOR_DSN` in the secret manager for staging.
- Verify event delivery and error traces using provider dashboards before releasing to production.
