"""Shared fixtures for capsize-memory tests."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from capsize_memory.models import Base


@pytest.fixture
def session(tmp_path: Path) -> Iterator[Session]:
    """Yield a real SQLite-file-backed session, tables created fresh."""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as sess:
        yield sess
