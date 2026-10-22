"""
Declarative base for all SQLAlchemy ORM models.

All models inherit from Base. Import models here before running Alembic
so that autogenerate can detect them.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base. All ORM models extend this."""

