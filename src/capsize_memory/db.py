"""Compatibility exports for the shared database primitives.

Not meant to be imported by a host app directly (a host mounts
`models.Base.metadata` into its own migration tooling) - this exists
so the models in this package have somewhere to attach.
"""

from capsize_commons.db import Base, UtcDateTime

__all__ = ["Base", "UtcDateTime"]
