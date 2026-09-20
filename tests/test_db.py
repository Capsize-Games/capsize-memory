"""Compatibility tests for the shared database primitives."""

import datetime

import pytest
from sqlalchemy.orm import Session

from capsize_memory.db import Base, UtcDateTime
from capsize_memory.models import ConversationTurn, Room, RoomParticipant


def test_models_attach_to_the_shared_metadata() -> None:
    """Domain models keep using the package's public metadata object."""
    assert Room.metadata is Base.metadata
    assert RoomParticipant.metadata is Base.metadata
    assert ConversationTurn.metadata is Base.metadata


def test_utc_datetime_round_trips_through_sqlite(session: Session) -> None:
    """An aware value remains UTC-aware after SQLite storage."""
    instant = datetime.datetime(
        2026,
        9,
        20,
        12,
        30,
        tzinfo=datetime.timezone(datetime.timedelta(hours=2)),
    )
    room = Room(
        platform="test",
        room_type="channel",
        external_key="utc",
        created_at=instant,
    )
    session.add(room)
    session.commit()
    session.refresh(room)

    assert room.created_at == instant.astimezone(datetime.UTC)
    assert room.created_at.tzinfo is datetime.UTC


def test_utc_datetime_rejects_naive_values_and_preserves_none() -> None:
    """The shared type retains its input validation and null behavior."""
    column = UtcDateTime()
    with pytest.raises(ValueError, match="timezone-aware"):
        column.process_bind_param(datetime.datetime(2026, 1, 1), None)
    assert column.process_bind_param(None, None) is None
    assert column.process_result_value(None, None) is None
