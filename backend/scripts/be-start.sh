#!/bin/bash
set -e

# Apply migrations
alembic upgrade head

# Start the app
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
