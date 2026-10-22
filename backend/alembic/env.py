"""
Alembic environment configuration for HireLens.

Reads DATABASE_URL from app.core.config.settings so that the same environment
variable used by the application is also used for migrations.
Imports app.models so that autogenerate can detect schema changes.
"""

import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ---------------------------------------------------------------------------
# Ensure the backend/ directory (which contains the `app` package) is on
# sys.path when alembic is run from the repo root or from backend/.
# ---------------------------------------------------------------------------
_here = os.path.dirname(os.path.abspath(__file__))          # backend/alembic/
_backend = os.path.dirname(_here)                            # backend/
if _backend not in sys.path:
    sys.path.insert(0, _backend)

# ---------------------------------------------------------------------------
# Application imports — must come after sys.path adjustment.
# ---------------------------------------------------------------------------
from app.core.config import settings  # noqa: E402
from app.db.base import Base           # noqa: E402
import app.models                      # noqa: E402, F401 — registers all models

# Alembic config object, giving access to values in alembic.ini.
config = context.config

# Override the sqlalchemy.url from settings so we never hard-code it.
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the declarative Base's metadata so autogenerate picks up all models.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with a URL (from settings) rather than an Engine.
    Useful for generating SQL scripts without a live database connection.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine from the configured URL and associates a connection
    with the migration context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
