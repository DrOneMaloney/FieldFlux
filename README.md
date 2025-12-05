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
