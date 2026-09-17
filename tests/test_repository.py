"""Unit tests for capsize_memory.repository."""

from __future__ import annotations

from sqlalchemy.orm import Session

from capsize_memory.models import ConversationTurn
from capsize_memory.repository import (
    clear_turns,
    delete_turn,
    get_or_create_participant,
    get_or_create_room,
    recent_turns,
    record_turn,
    touch_room,
)


def test_get_or_create_room_creates_once(session: Session) -> None:
    room = get_or_create_room(session, "discord", "channel", "g:c")
    assert room.id is not None
    assert room.platform == "discord"
    assert room.last_active_at is None


def test_get_or_create_room_is_idempotent(session: Session) -> None:
    first = get_or_create_room(session, "discord", "channel", "g:c")
    second = get_or_create_room(session, "discord", "channel", "g:c")
    assert first.id == second.id


def test_get_or_create_room_distinguishes_platform(session: Session) -> None:
    discord_room = get_or_create_room(session, "discord", "channel", "x")
    bluesky_room = get_or_create_room(session, "bluesky", "account", "x")
    assert discord_room.id != bluesky_room.id


def test_touch_room_sets_last_active_at(session: Session) -> None:
    room = get_or_create_room(session, "discord", "dm", "g:1")
    touch_room(session, room.id)
    session.flush()
    session.refresh(room)
    assert room.last_active_at is not None


def test_get_or_create_participant_is_idempotent(session: Session) -> None:
    room = get_or_create_room(session, "discord", "channel", "g:c")
    first = get_or_create_participant(session, room.id, "u1", "alice")
    second = get_or_create_participant(session, room.id, "u1", "alice2")
    assert first.id == second.id
    assert second.display_name == "alice2"


def test_get_or_create_participant_scoped_per_room(session: Session) -> None:
    room_a = get_or_create_room(session, "discord", "channel", "a")
    room_b = get_or_create_room(session, "discord", "channel", "b")
    p_a = get_or_create_participant(session, room_a.id, "u1", "alice")
    p_b = get_or_create_participant(session, room_b.id, "u1", "alice")
    assert p_a.id != p_b.id


def test_record_turn_returns_the_new_row(session: Session) -> None:
    room = get_or_create_room(session, "discord", "channel", "g:c")

    turn = record_turn(session, room.id, "alice", "hi")

    assert turn.id is not None
    assert turn.speaker == "alice"
    assert turn.text == "hi"


def test_recent_turns_excludes_sensitive_when_asked(
    session: Session,
) -> None:
    room = get_or_create_room(session, "discord", "channel", "g:c")
    record_turn(session, room.id, "alice", "public thing")
    record_turn(session, room.id, "alice", "private thing", is_sensitive=True)
    session.flush()

    all_turns = recent_turns(session, room.id, limit=10)
    public_only = recent_turns(
        session, room.id, limit=10, include_sensitive=False
    )

    assert [t.text for t in all_turns] == ["public thing", "private thing"]
    assert [t.text for t in public_only] == ["public thing"]


def test_record_and_recall_turns_in_order(session: Session) -> None:
    room = get_or_create_room(session, "discord", "channel", "g:c")
    record_turn(session, room.id, "alice", "hi")
    record_turn(session, room.id, "capsize", "hello")
    session.flush()

    turns = recent_turns(session, room.id, limit=10)

    assert [(t.speaker, t.text) for t in turns] == [
        ("alice", "hi"),
        ("capsize", "hello"),
    ]


def test_recent_turns_respects_limit(session: Session) -> None:
    room = get_or_create_room(session, "discord", "channel", "g:c")
    for i in range(5):
        record_turn(session, room.id, "alice", f"msg{i}")
    session.flush()

    turns = recent_turns(session, room.id, limit=2)

    assert [t.text for t in turns] == ["msg3", "msg4"]


def test_recent_turns_scoped_per_room(session: Session) -> None:
    room_a = get_or_create_room(session, "discord", "channel", "a")
    room_b = get_or_create_room(session, "discord", "channel", "b")
    record_turn(session, room_a.id, "alice", "in room a")
    record_turn(session, room_b.id, "bob", "in room b")
    session.flush()

    assert [t.text for t in recent_turns(session, room_a.id, 10)] == [
        "in room a"
    ]


def test_clear_turns_empties_one_room_only(session: Session) -> None:
    room_a = get_or_create_room(session, "discord", "channel", "a")
    room_b = get_or_create_room(session, "discord", "channel", "b")
    record_turn(session, room_a.id, "alice", "hi")
    record_turn(session, room_b.id, "bob", "hey")
    session.flush()

    clear_turns(session, room_a.id)
    session.flush()

    assert recent_turns(session, room_a.id, 10) == []
    assert len(recent_turns(session, room_b.id, 10)) == 1


def test_delete_turn_removes_it(session: Session) -> None:
    room = get_or_create_room(session, "discord", "channel", "g:c")
    record_turn(session, room.id, "alice", "hi")
    session.flush()
    row = session.query(ConversationTurn).first()

    assert delete_turn(session, row.id) is True
    session.flush()
    assert recent_turns(session, room.id, 10) == []


def test_delete_turn_missing_returns_false(session: Session) -> None:
    assert delete_turn(session, 999) is False
