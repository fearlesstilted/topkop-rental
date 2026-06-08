# TopKop Rental

Internal rental operations system for TopKop construction equipment.

The system replaces spreadsheet-based rental handling with one internal workflow for pricing, contracts, equipment inspections, equipment status and daily operations.

## What It Does

- Creates rental contracts for construction equipment.
- Supports daily pricing and hourly operator-based pricing.
- Adds transport as a separate contract cost.
- Generates rental contract PDFs.
- Tracks equipment, categories, registration numbers, and statuses.
- Stores pickup/return inspection reports with photos, GPS data, and signatures.
- Provides **Tablica operacyjna** for returns, service, readiness, and workshop tasks.
- Uses PIN login for a small internal team.

## Core Workflows

### Pricing And Contracts

Contracts can be priced in two modes:

- `daily`: rental without operator, calculated by rental days.
- `hourly`: rental with operator, calculated as `operator hours × hourly rate`.

Optional pricing fields:

- discount percentage;
- surcharge percentage;
- free-form transport cost;
- transport description, for example route or km rate;
- billing entity selected from the configured company profiles.

The final `total_netto` includes the rental/operator price and transport.

### Tablica Operacyjna

The board is a compact operational view for a small service team, not a general-purpose kanban product.

Columns:

- `Do ogarnięcia`;
- `W robocie`;
- `Gotowe`;
- `Zamknięte`.

Cards include equipment context, rental context, priority, due date, owner, notes, and checklist progress.

### Inspections

Inspection reports support pickup and return flows with:

- equipment reference;
- rental reference;
- meter reading;
- GPS data;
- photos;
- customer signer name;
- signature;
- PDF report generation.

## Tech Stack

- Backend: FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2.
- Frontend: Vue 3, TypeScript, Vite, Quasar, Pinia, PWA.
- PDF: Jinja2 templates and WeasyPrint.
- Realtime: WebSocket updates for Tablica.
- Local runtime: Docker Compose.

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

Local URLs:

- frontend: `http://localhost:5173`;
- backend: `http://localhost:8000`;
- health check: `http://localhost:8000/api/health`.

## Local PIN Setup

Default login PINs are not committed to Git.

Create or update `backend/.env`:

```env
PIN_DEFAULT_BIURO=1111
PIN_DEFAULT_MANAGER=3333
```

Then run:

```bash
cd backend
make seed
```

If these variables are missing, seed will skip user creation.

## Verification

Backend:

```bash
cd backend
make migrate
make check
.venv/bin/python -m compileall app tests
```

Frontend:

```bash
cd frontend
npm run build
```

## Deployment

Free-first deployment path:

- Frontend: Vercel or Netlify.
- Backend: Render free web service.
- Database: Neon free PostgreSQL.

Frontend environment for split deployment:

```env
VITE_API_BASE_URL=https://your-backend.onrender.com/api
VITE_WS_BASE_URL=wss://your-backend.onrender.com
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for the current deployment notes.

## Project Structure

```text
topkop-rental/
├── backend/           FastAPI app, models, routers, services, migrations
├── frontend/          Vue 3 PWA
├── DEPLOYMENT.md      free-first deployment notes
└── docker-compose.yml
```

## Main API Endpoints

- `GET /api/health` - backend health check.
- `POST /api/auth/login` - PIN login.
- `GET /api/equipment` - equipment list.
- `POST /api/rentals/calculate` - rental/operator pricing calculation.
- `POST /api/rentals` - create rental contract.
- `GET /api/rentals/{id}/pdf` - rental contract PDF.
- `POST /api/inspections` - create inspection report.
- `GET /api/kanban` - operational board cards.
- `WS /ws/kanban` - realtime board updates.

## Troubleshooting

If `python -m app.cli seed` fails with `ModuleNotFoundError`, the command is probably using the wrong Python interpreter, usually conda/base instead of `backend/.venv`.

Use Make targets:

```bash
cd backend
make install
make migrate
make seed
make dev
```

Or call the backend virtualenv explicitly:

```bash
cd backend
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m app.cli seed
.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

Confirm the interpreter:

```bash
.venv/bin/python -c "import sys, asyncpg; print(sys.executable); print(asyncpg.__version__)"
```

The path must point to `backend/.venv/bin/python`.

## Scope

TopKop Rental is not an ERP and not a full kanban platform. It is a focused internal system for a small team: price a rental, issue a contract, document equipment condition, track return/service work, and keep machines ready for the next customer.
