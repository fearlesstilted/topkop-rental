# TopKop Rental

Rental and workshop management system for TopKop construction equipment.

The project covers the practical rental workflow: pricing a contract, issuing documents, recording equipment condition, and handing returned machines to the workshop before the next rental.

## Features

- Rental contracts with day counting, tiered rates, discounts, surcharges, and PDF generation.
- Pickup and return inspection reports with photos, GPS location, customer signature, and offline sync.
- Workshop board for mechanics and machine preparation tasks.
- Equipment, category, status, and registration number tracking.
- PIN-based authentication.
- User roles: `biuro`, `mechanik`, and `manager`.
- WebSocket updates for the workshop board.

## Tech Stack

- Backend: FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2.
- Frontend: Vue 3, TypeScript, Vite, Quasar, Pinia, PWA.
- PDF: Jinja2 templates and WeasyPrint.
- File storage: local `uploads` directory.
- Runtime: Docker Compose.

## Quick Start

Start PostgreSQL:

```bash
docker compose up -d db
```

Run the backend:

```bash
cd backend
make install
make migrate
make seed
make dev
```

Run the frontend:

```bash
cd frontend
npm install
npm run dev
```

By default, the frontend runs on `http://localhost:5173` and the backend runs on `http://localhost:8000`.

## Docker

```bash
docker compose up --build
```

Docker Compose starts PostgreSQL, applies migrations, seeds initial data, and runs the backend.

## Local PIN Setup

The repository does not include default login PIN codes. Before running `make seed`, create `backend/.env` from `backend/.env.example` and set local values:

```env
PIN_DEFAULT_BIURO=your-local-biuro-pin
PIN_DEFAULT_MECHANIK=your-local-mechanik-pin
PIN_DEFAULT_MANAGER=your-local-manager-pin
```

If these variables are missing, seed will skip user creation.

## Backend Troubleshooting

If `python -m app.cli seed` fails with `ModuleNotFoundError: No module named 'asyncpg'` or `ModuleNotFoundError: No module named 'sqlalchemy'`, the command is using the wrong Python interpreter. This can happen when conda/base is active or zsh keeps a cached `python` path.

Use the Make targets or call the backend virtualenv explicitly:

```bash
cd backend
make install
make migrate
make seed
```

Equivalent direct commands:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m app.cli seed
```

To confirm the interpreter is correct:

```bash
.venv/bin/python -c "import sys, asyncpg; print(sys.executable); print(asyncpg.__version__)"
```

The printed path must point to `backend/.venv/bin/python`.

## Project Structure

```text
topkop-rental/
├── backend/           FastAPI app, models, routers, services, migrations
├── frontend/          Vue 3 PWA
└── docker-compose.yml
```

## Verification

Backend:

```bash
cd backend
make check
.venv/bin/python -m compileall app tests
```

Frontend:

```bash
cd frontend
npm run build
```

## Main API Endpoints

- `GET /api/health` — backend health check.
- `POST /api/auth/login` — PIN login.
- `GET /api/equipment` — equipment list.
- `POST /api/rentals/calculate` — rental price calculation.
- `POST /api/rentals` — create rental contract.
- `GET /api/rentals/{id}/pdf` — rental contract PDF.
- `POST /api/inspections` — create inspection report.
- `GET /api/kanban` — workshop board.
- `WS /ws/kanban` — realtime workshop board updates.

## Scope

TopKop Rental is not intended to be a heavy ERP or a complex kanban platform. It is a focused internal tool for equipment rental operations: create a contract, document the machine condition, and move workshop tasks forward.
