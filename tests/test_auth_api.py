from pathlib import Path

from fastapi.testclient import TestClient

from server import main


def test_health_endpoint_runs_and_cleans_up_db():
    db_files = [Path("fieldflux.db"), Path("fieldflux.db-shm"), Path("fieldflux.db-wal")]

    with TestClient(main.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json().get("status") == "ok"

    for db_file in db_files:
        db_file.unlink(missing_ok=True)

