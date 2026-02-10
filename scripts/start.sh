#!/bin/sh
set -e

echo "Starting deployment scripts..."

# Run database migrations
echo "Running alembic migrations..."
alembic upgrade head

# Start background worker in the background
echo "Starting background worker..."
python -m app.workers.run_all &

# Start the web server
echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
