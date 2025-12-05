"""Seed data loader for staging and local environments."""

from __future__ import annotations

import os

from fieldflux.app import FieldFluxApp, FieldRecord


def load_seed_data() -> list[FieldRecord]:
    return [
        FieldRecord(
            id="north-40",
            name="North 40",
            crop="Corn",
            owner="admin",
            attributes={"acres": "40"},
        ),
        FieldRecord(
            id="east-80",
            name="East 80",
            crop="Soybeans",
            owner="admin",
            attributes={"acres": "80"},
        ),
    ]


def main() -> None:
    app = FieldFluxApp()
    app.seed(load_seed_data())
    print("Seed data loaded")
    print("DB configured:", bool(os.getenv("DATABASE_URL")))
    print("Map API configured:", bool(os.getenv("MAPS_API_KEY")))


if __name__ == "__main__":
    main()
