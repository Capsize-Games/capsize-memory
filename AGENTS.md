# Capsize memory library

`capsize-memory` owns the room, participant, conversation-turn, and transcript
domain. It consumes the generic `capsize-commons.db` primitives but must not
move domain models, persistence policy, or host connection ownership into
commons.

The host owns its SQLAlchemy engine, session, migrations, and database URL.
`capsize_memory.models.Base.metadata` remains the compatibility surface that a
host mounts into its migration tooling. Preserve the existing PostgreSQL and
SQLite behavior and the timezone-aware UTC contract when changing models.

Use the canonical `justfile` recipes for local checks. The repository currently
does not commit a lockfile; `setup` and CI therefore resolve from
`pyproject.toml` without claiming locked reproducibility.
