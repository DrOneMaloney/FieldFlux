# FieldFlux

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
