from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from decouple import config
from dotenv import load_dotenv
import os

# --- Load environment variables from .env ---
load_dotenv()

# Import your Base (contains model metadata)
from database import Base  

# Load the Alembic Config object
config_obj = context.config

# --- Load DATABASE_URL dynamically ---
# Priority: Environment variable → .env fallback
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# Convert postgres:// → postgresql:// if needed (DigitalOcean, Render, etc.)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Inject into Alembic config
config_obj.set_main_option("sqlalchemy.url", DATABASE_URL)

# Configure logging
if config_obj.config_file_name is not None:
    fileConfig(config_obj.config_file_name)

import models

# Set metadata (autogenerate needs this)
target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config_obj.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config_obj.get_section(config_obj.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


# Run migrations depending on mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
