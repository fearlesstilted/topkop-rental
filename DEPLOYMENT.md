# Deployment Plan

Free-first setup:

1. Frontend: Vercel or Netlify free static hosting.
2. Database: Neon free PostgreSQL.
3. Backend: Render free web service for FastAPI.

Frontend environment:

```env
VITE_API_BASE_URL=https://your-backend.onrender.com/api
VITE_WS_BASE_URL=wss://your-backend.onrender.com
```

Backend environment:

```env
DATABASE_URL=postgresql+asyncpg://...
DATABASE_SYNC_URL=postgresql+psycopg2://...
APP_ENV=production
SECRET_KEY=change-me
CORS_ORIGINS=https://your-frontend.vercel.app
PIN_DEFAULT_BIURO=
PIN_DEFAULT_MECHANIK=
PIN_DEFAULT_MANAGER=
```

Operational notes:

- Render free can sleep after inactivity. For internal use by 2-3 people this is acceptable at the start.
- Neon free is enough for the current workload.
- Uploaded files are currently local storage. For real production, move uploads to S3-compatible storage before relying on inspection photos.
