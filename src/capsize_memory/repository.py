"""Read/write functions for rooms, participants, and turns.

Every function takes a `Session` the caller already has open. None of
them call `session.commit()` - that's the caller's transaction
boundary to control, not this package's.
"""

import datetime
from dataclasses import dataclass

from sqlalchemy.orm import Session

from capsize_memory.models import ConversationTurn, Room, RoomParticipant


@dataclass(frozen=True)
class Turn:
    """One turn, as read back for prompt-building."""

    speaker: str
    text: str


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def get_or_create_room(
    session: Session,
    platform: str,
    room_type: str,
    external_key: str,
    display_name: str | None = None,
) -> Room:
    """Return the room for (platform, room_type, external_key).

    Creates it on first use. Safe to call on every message - the
    unique constraint on (platform, room_type, external_key) makes
    this idempotent.
    """
    room = (
        session.query(Room)
        .filter_by(
            platform=platform,
            room_type=room_type,
            external_key=external_key,
        )
        .first()
    )
    if room is not None:
        return room
    room = Room(
        platform=platform,
        room_type=room_type,
        external_key=external_key,
        display_name=display_name,
    )
    session.add(room)
    session.flush()
    return room


def touch_room(session: Session, room_id: int) -> None:
    """Bump a room's `last_active_at` to now."""
    session.query(Room).filter_by(id=room_id).update(
        {"last_active_at": _utcnow()}
    )


def get_or_create_participant(
    session: Session, room_id: int, external_id: str, display_name: str
) -> RoomParticipant:
    """Return the participant for (room_id, external_id).

    Creates it on first use; updates `display_name`/`last_seen_at` on
    every later call - a display name can change (a Discord nickname
    edit), and this keeps it current without a separate update path.
    """
    participant = (
        session.query(RoomParticipant)
        .filter_by(room_id=room_id, external_id=external_id)
        .first()
    )
    if participant is not None:
        participant.display_name = display_name
        participant.last_seen_at = _utcnow()
        return participant
    participant = RoomParticipant(
        room_id=room_id,
        external_id=external_id,
        display_name=display_name,
    )
    session.add(participant)
    session.flush()
    return participant


def record_turn(
    session: Session,
    room_id: int,
    speaker: str,
    text: str,
    participant_id: int | None = None,
    is_sensitive: bool = False,
) -> ConversationTurn:
    """Append one turn to a room's log. Returns the new row, flushed."""
    turn = ConversationTurn(
        room_id=room_id,
        participant_id=participant_id,
        speaker=speaker,
        text=text,
        is_sensitive=is_sensitive,
    )
    session.add(turn)
    session.flush()
    return turn


def recent_turns(
    session: Session,
    room_id: int,
    limit: int,
    include_sensitive: bool = True,
) -> list[Turn]:
    """Return up to `limit` most recent turns, oldest first.

    `include_sensitive=False` excludes any turn flagged `is_sensitive`
    - the caller's job to set when the destination this context feeds
    into is itself public, so a fact/turn learned somewhere private
    never gets echoed back publicly.
    """
    query = session.query(ConversationTurn).filter_by(room_id=room_id)
    if not include_sensitive:
        query = query.filter_by(is_sensitive=False)
    rows = (
        query.order_by(
            ConversationTurn.created_at.desc(), ConversationTurn.id.desc()
        )
        .limit(limit)
        .all()
    )
    return [Turn(speaker=row.speaker, text=row.text) for row in reversed(rows)]


def clear_turns(session: Session, room_id: int) -> None:
    """Delete every turn for a room."""
    session.query(ConversationTurn).filter_by(room_id=room_id).delete()


def delete_turn(session: Session, turn_id: int) -> bool:
    """Delete one turn by id. Returns False if it didn't exist."""
    row = session.get(ConversationTurn, turn_id)
    if row is None:
        return False
    session.delete(row)
    return True
