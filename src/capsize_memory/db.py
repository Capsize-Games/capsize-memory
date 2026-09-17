"""Declarative base and portable timestamp type.

Not meant to be imported by a host app directly (a host mounts
`models.Base.metadata` into its own migration tooling) - this exists
so the models in this package have somewhere to attach.
"""

import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    """Base class for every capsize_memory ORM model."""


class UtcDateTime(TypeDecorator[datetime.datetime]):
    """A `DateTime` that round-trips as timezone-aware UTC through SQLite.

    SQLite has no native timezone-aware storage, so the stock
    `DateTime` type reads back a naive value even when written from an
    aware one. This reattaches UTC on the way out. A no-op on a
    database that already preserves timezone info (e.g. Postgres).
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(
        self, value: datetime.datetime | None, dialect: object
    ) -> datetime.datetime | None:
        """Require and normalize an aware value on the way into storage."""
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("UtcDateTime requires a timezone-aware value")
        return value.astimezone(datetime.UTC)

    def process_result_value(
        self, value: datetime.datetime | None, dialect: object
    ) -> datetime.datetime | None:
        """Reattach UTC to a value read back as naive."""
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=datetime.UTC)
        return value.astimezone(datetime.UTC)
