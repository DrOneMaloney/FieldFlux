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
