#!/bin/bash
set -e

echo "Running Alembic migrations..."
alembic upgrade head

echo " Seeding database..."
python -c "from setup_database import seed_data; seed_data()"

echo " Starting server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000


