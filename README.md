# Alix - Legal Tech Document AST & Vector Analysis

Alix is a legal tech platform designed for structural contract analysis, automated document processing, and high-performance vector search. Built using FastAPI, SQLAlchemy 2.0, PostgreSQL with `pgvector`, and React, Alix converts complex legal documents into structured Abstract Syntax Trees (AST) and context-aware embeddings.

---

## 📐 Architecture & Workflow

Below is the high-level workflow architecture for document ingestion, background task processing, and vector indexing:

![Alix System Architecture & Workflow](./alix-workflow.jpg)

### Core Architectural Choices

* **FastAPI `BackgroundTasks`:** Keeps the architecture lightweight for initial development by executing asynchronous vector processing in-memory right after HTTP responses.
* **Database & Vector Engine:** PostgreSQL 16 utilizing `pgvector` for storing 1536-dimensional embeddings (compatible with OpenAI models) alongside traditional relational models.
* **Dual Database Drivers:** Asynchronous operations powered by `asyncpg` for web endpoints, with synchronous driver access reserved for migration operations via Alembic.

---

## 🛠️ Tech Stack

* **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic
* **Vector & Database:** PostgreSQL 16 (`pgvector/pgvector:pg16`), `asyncpg`
* **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Zustand, Tiptap, Radix UI
* **DevOps:** Docker, Docker Compose

---

## 📂 Project Structure

```text
alix/
├── alix-workflow.jpg          # System architecture diagram
├── alembic/                   # Database migration files & env configuration
│   ├── script.py.mako         # Migration template (pre-configured with pgvector)
│   └── env.py
├── backend/                   # FastAPI application & API endpoints
├── core/                      # Shared models, settings, and database setup
│   ├── config/
│   │   └── settings.py        # Pydantic Settings reading .env
│   ├── database.py            # Async engine & session lifecycle setup
│   └── models/
│       └── vector.py          # SQLAlchemy models with pgvector columns
├── frontend/                  # React + Vite application
├── alembic.ini                # Static Alembic configuration
├── docker-compose.yml         # Container orchestration (db, backend, frontend)
└── .env.example               # Template environment variables
```

---
## 🚀 Quick Start

### 1. Environment Setup

Create a `.env` file in the root directory:

```env
DB_HOST=db
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=contract_db

APP_NAME=alix
DEBUG=True

QUEUE_NAME=alix_queue
SECRET_KEY=your_secret_key_here

```

### 2. Launching with Docker Compose

Spin up the database, backend, and frontend containers in detached mode:

```bash
docker compose up -d

```

Services will be accessible at:

* **Frontend:** `http://localhost:5173`
* **Backend API Docs:** `http://localhost:8000/docs`
* **PostgreSQL:** `localhost:5432`

---

## 🗄️ Database Migrations

Database schemas are managed statically via Alembic.

### Generate a Migration

When creating or modifying SQLAlchemy models inside `core/models/`:

```bash
docker compose exec backend alembic revision --autogenerate -m "describe_changes"

```

### Apply Migrations

Apply pending migrations to the database:

```bash
docker compose exec backend alembic upgrade head

```

> **Note:** The `script.py.mako` template automatically imports `pgvector` into every newly generated migration script to prevent type registration errors.

---

## 🧪 Local Backend Setup (Without Docker)

If you prefer running the Python environment locally on your host machine:

1. **Install dependencies:**
```bash
pip install -r requirements.txt

```


2. **Ensure PostgreSQL with `pgvector` is running locally.**
3. **Run database migrations:**
```bash
alembic upgrade head

```


4. **Start the FastAPI server:**
```bash
uvicorn backend.main:app --reload --port 8000

```

