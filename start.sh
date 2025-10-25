#!/bin/bash
set -e

if ! alembic upgrade head; then
  echo "⚠️ Alembic migration failed, skipping..."
else
  echo "✅ Alembic migrations applied successfully."
fi


echo "Seeding database..."
python -c "from setup_database import seed_data; seed_data()" || echo "Seeding skipped"

echo "Starting server..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

