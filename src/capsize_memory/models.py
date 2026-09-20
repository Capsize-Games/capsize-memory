"""ORM models for rooms, participants, and conversation turns."""

import datetime

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from capsize_memory.db import Base, UtcDateTime

__all__ = ["ConversationTurn", "Room", "RoomParticipant"]


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


class Room(Base):
    """A place a bot has a conversation or a presence.

    A Discord channel, a Discord DM thread, a Bluesky account's own
    post stream - platform-agnostic on purpose, so "who is the bot
    talking to, and where" is always one query away instead of
    scattered per-platform ad hoc keys.
    """

    __tablename__ = "rooms"
    __table_args__ = (
        UniqueConstraint("platform", "room_type", "external_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[str] = mapped_column(String(32))
    room_type: Mapped[str] = mapped_column(String(32))
    external_key: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(255), default=None)
    created_at: Mapped[datetime.datetime] = mapped_column(
        UtcDateTime, default=_utcnow
    )
    last_active_at: Mapped[datetime.datetime | None] = mapped_column(
        UtcDateTime, default=None
    )


class RoomParticipant(Base):
    """One identity seen in a room.

    A Discord user, a Bluesky handle, or (for an account-type room)
    the account itself. Structural, not just a display-name string on
    a turn, so a room's audience can be queried and reconstructed
    later, not just read as a flat transcript.
    """

    __tablename__ = "room_participants"
    __table_args__ = (UniqueConstraint("room_id", "external_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(255))
    first_seen_at: Mapped[datetime.datetime] = mapped_column(
        UtcDateTime, default=_utcnow
    )
    last_seen_at: Mapped[datetime.datetime] = mapped_column(
        UtcDateTime, default=_utcnow
    )


class ConversationTurn(Base):
    """One raw utterance in a room's short-term turn log.

    Distinct from a durable, LLM-extracted fact (that concern belongs
    to the host, e.g. capsize-persona's own MemoryFact): a turn is
    exactly what was said, kept to give the next reply immediate
    continuity and, over time, a reconstructable log of the room.
    `speaker` is a denormalized display name alongside `participant_id`
    so transcript formatting never needs a join.
    """

    __tablename__ = "conversation_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), index=True)
    # Null for the bot's own turns - a participant is always someone
    # else the bot is talking to, never the bot itself.
    participant_id: Mapped[int | None] = mapped_column(
        ForeignKey("room_participants.id"), default=None
    )
    speaker: Mapped[str] = mapped_column(String(120))
    text: Mapped[str] = mapped_column(Text)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        UtcDateTime, default=_utcnow
    )
