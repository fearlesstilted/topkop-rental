# Deployment Plan

Free-first setup:

1. Frontend: Cloudflare Pages or Netlify free static hosting.
2. Database: Neon free PostgreSQL.
3. Backend: Render free web service for FastAPI.

## Backend: Render

The repository includes `render.yaml` for a Docker-based Render service.

Use Docker runtime because PDF generation depends on WeasyPrint system packages.

Render creates the service from:

```text
render.yaml
backend/Dockerfile
backend/scripts/render-start.sh
```

The start script runs:

```bash
alembic upgrade head
python -m app.cli seed
uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
```

Required Render environment variables:

```env
DATABASE_URL=postgresql://...
APP_ENV=production
SECRET_KEY=change-me
CORS_ORIGINS=https://your-frontend.pages.dev
PIN_DEFAULT_BIURO=
PIN_DEFAULT_MANAGER=
```

For Neon, convert the connection string like this:

```text
Neon gives:
postgresql://USER:PASSWORD@HOST/DB?sslmode=require

Use for backend:
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DB?sslmode=require
```

The app normalizes Neon/Postgres URLs to SQLAlchemy asyncpg internally.

## Frontend: Cloudflare Pages

Build settings:

```text
Root directory: frontend
Build command: npm run build
Build output directory: dist
```

Frontend environment variables:

```env
VITE_API_BASE_URL=https://your-backend.onrender.com/api
VITE_WS_BASE_URL=wss://your-backend.onrender.com
```

Operational notes:

- Render free can sleep after inactivity. For internal use by 2-3 people this is acceptable at the start.
- Neon free is enough for the current workload.
- Uploaded files are currently local storage. For real production, move uploads to S3-compatible storage before relying on inspection photos.
