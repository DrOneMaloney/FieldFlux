# FieldFlux

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
