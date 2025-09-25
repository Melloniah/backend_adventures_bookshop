from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
from decouple import config

# Import your Base from models
from models import Base  

# Alembic Config object
config_obj = context.config

# Load DATABASE_URL from .env
database_url = config("DATABASE_URL", default="sqlite:///./dev.db")
config_obj.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for logging
if config_obj.config_file_name is not None:
    fileConfig(config_obj.config_file_name)

# Add your models' metadata
target_metadata = Base.metadata

def run_migrations_offline():
    url = config_obj.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"}
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config_obj.get_section(config_obj.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
