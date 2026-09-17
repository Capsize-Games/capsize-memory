"""Render a turn list as a flat, multi-speaker transcript block."""

from capsize_memory.repository import Turn


def format_transcript(turns: list[Turn]) -> str:
    """Return `turns` as '- speaker: text' lines, oldest first.

    Returns '(none yet)' for an empty list, so a prompt template can
    always substitute this in without a separate empty-case branch.
    """
    if not turns:
        return "(none yet)"
    return "\n".join(f"- {turn.speaker}: {turn.text}" for turn in turns)
