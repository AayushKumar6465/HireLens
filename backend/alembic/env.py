"""
Alembic environment configuration for HireLens.

Reads DATABASE_URL from app.core.config.settings so that the same environment
variable used by the application is also used for migrations.
Imports app.models so that autogenerate can detect schema changes.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from sqlalchemy.engine import make_url

from alembic import context

# ---------------------------------------------------------------------------
# Ensure the backend/ directory (which contains the `app` package) is on
# sys.path when alembic is run from the repo root or from backend/.
# ---------------------------------------------------------------------------
_here = os.path.dirname(os.path.abspath(__file__))  # backend/alembic/
_backend = os.path.dirname(_here)  # backend/
if _backend not in sys.path:
    sys.path.insert(0, _backend)

# ---------------------------------------------------------------------------
# Application imports — must come after sys.path adjustment.
# ---------------------------------------------------------------------------
import app.models  # noqa: F401 — registers all models
from app.core.config import settings
from app.db.base import Base


def get_direct_neon_url(raw_url: str) -> str:
    """
    Derive a direct (non-pooled) Neon connection URL for migrations.

    Neon connection pooler endpoints include '-pooler' in the host.
    Migrations require direct DDL access without pooler transaction wrappers.
    This parses the URL safely, strips '-pooler' from the host, and preserves
    all other parameters including sslmode.
    """
    if not raw_url:
        return ""
    url = make_url(raw_url)
    if url.host and "-pooler" in url.host:
        url = url.set(host=url.host.replace("-pooler", ""))
    return url.render_as_string(hide_password=False)


# Alembic config object, giving access to values in alembic.ini.
config = context.config

# Derive direct URL for migrations only
migration_url = get_direct_neon_url(settings.database_url)

# Override the sqlalchemy.url from settings so we never hard-code it.
config.set_main_option("sqlalchemy.url", migration_url)

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

    Creates an Engine from the direct migration URL and associates a connection
    with the migration context.
    """
    connectable = create_engine(
        migration_url,
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
