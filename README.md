# Alix

Legal tech platform for contract AST analysis and vector search. Built with React + TypeScript + Vite (frontend) and FastAPI + SQLAlchemy + pgvector (backend).

![Alix System Architecture & Workflow](./alix-workflow.jpg)

---

## Project Structure

```text
alix-assessment/
├── alix-workflow.jpg
├── docker-compose-local.yml   # db + backend + frontend
├── frontend/                  # React + TypeScript + Vite + Tiptap
│   ├── src/
│   │   ├── pages/             # Home, Editor
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
└── backend/                   # Python app root — run backend from here
    ├── main.py
    ├── alembic/
    ├── admin/
    ├── api/
    ├── core/
    │   ├── config/settings.py
    │   ├── database.py
    │   └── models/            # SQLAlchemy models (pgvector 3072-dim)
    ├── ds/                    # Data science / RAG modules
    ├── requirements/
    ├── scripts/
    ├── Dockerfile
    └── .env
```



---

## Quick Start (Docker)

From project root:

```bash
docker compose -f docker-compose-local.yml up -d
```

Copy `backend/.env.example` → `backend/.env`:
- Full Docker stack → `DB_HOST=db`
- DB container only → `DB_HOST=localhost`

Uses `pgvector/pgvector:pg16` — pgvector is included automatically in Docker.

---

## Backend (Local)

**Requirements:** Python 3.11+ (3.12 recommended)

### PostgreSQL + pgvector (without Docker)

- [PostgreSQL downloads](https://www.postgresql.org/download/)
- [pgvector installation](https://github.com/pgvector/pgvector#installation)

Enable pgvector once as superuser:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

> Your app user (e.g. `alix`) cannot run this — use the `postgres` superuser.

### Run

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements/backend.txt
copy .env.example .env         # DB_HOST=localhost

alembic upgrade head
uvicorn main:app --reload --port 8000
```

### Backend URLs

| Service | URL |
|---------|-----|
| Swagger | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Admin | http://localhost:8000/admin |
| Health | http://localhost:8000/test/ |

Admin login: `ADMIN_USERNAME` / `ADMIN_PASSWORD` in `backend/.env`.

---

## Frontend (Local)

**Requirements:** Node.js 22+

### Stack

- React 18 + TypeScript
- Vite 8
- React Router 7
- Tiptap (rich text editor on `/editor`)

### Run

```bash
cd frontend
npm install
npm run dev
```

### Frontend URLs

| Page | URL |
|------|-----|
| Home | http://localhost:5173/ |
| Editor | http://localhost:5173/editor |

### Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Dev server (port 5173) |
| `npm run build` | Type-check + production build |
| `npm run preview` | Preview production build |
| `npm run lint` | ESLint check |
| `npm run lint:fix` | ESLint auto-fix |

### Configuration

| File | Purpose |
|------|---------|
| `package.json` | Dependencies, Node `>=22` engine |
| `vite.config.ts` | Vite dev server (`0.0.0.0:5173`) |
| `tsconfig.app.json` | TypeScript app config |
| `src/index.css` | App + editor styles |

### Docker

```bash
docker compose -f docker-compose-local.yml up -d frontend

# rebuild after dependency changes:
docker compose -f docker-compose-local.yml build frontend
docker compose -f docker-compose-local.yml up -d frontend
```

Frontend container uses `node:22-alpine` and mounts `./frontend` with a separate `node_modules` volume.

---

## Migrations

From `backend/`:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

With Docker:

```bash
docker compose -f docker-compose-local.yml exec backend alembic upgrade head
```

---

## Git Hooks

From project root (not `backend/`):

```bash
pip install pre-commit ruff
pre-commit install
```

Hooks:
- **Ruff** — Python (`backend/`)
- **ESLint** — TypeScript/React (`frontend/`)

On Windows, if git fails, disable **App execution aliases** for `git.exe` / `git.cmd` in Settings, then retry.
