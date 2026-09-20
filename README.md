# capsize-memory

A room + short-term conversation-turn memory engine you mount into
your own database — not a service, not a pluggable storage backend,
just vendor-neutral SQLAlchemy models and the functions that read and
write them.

```bash
pip install capsize-memory
```

## What it does

A **Room** is any place a bot has a presence: a Discord channel, a
Discord DM thread, a Bluesky account's own post stream. A
**RoomParticipant** is one identity seen in a room — a Discord user, a
Bluesky handle, or the account itself. A **ConversationTurn** is one
raw utterance, tied to a room and (when known) a participant.

This gives multi-speaker conversations for free: a channel with three
humans talking is three distinct participants sharing one room's turn
log, not three fragmented one-on-one threads. It also gives a
reconstructable log of where a bot has been talking and to whom,
across every platform it's wired into — one query, not scattered
per-platform ad hoc keys.

```python
from capsize_memory.repository import (
    get_or_create_room,
    get_or_create_participant,
    record_turn,
    recent_turns,
)
from capsize_memory.format import format_transcript

room = get_or_create_room(session, "discord", "channel", "guild:channel")
alice = get_or_create_participant(session, room.id, "user123", "alice")
record_turn(
    session,
    room.id,
    "alice",
    "hey, just moved to Austin",
    participant_id=alice.id,
)
record_turn(session, room.id, "capsize", "nice, welcome!")

turns = recent_turns(session, room.id, limit=6)
print(format_transcript(turns))
# - alice: hey, just moved to Austin
# - capsize: nice, welcome!
```

## What it does NOT do

No engine, no connection, no migration of its own — you mount
`capsize_memory.models.Base.metadata` into your own Alembic `env.py`
(or `create_all()` for a quick start) and pass your own `Session` to
every function. This is deliberate: a second host with its own
database (Postgres, SQLite, whatever) gets the exact same behavior by
pointing its own session at these same models — nothing in this
package assumes SQLite specifically, or owns a connection string.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy src
```
