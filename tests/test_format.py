"""Unit tests for capsize_memory.format."""

from __future__ import annotations

from capsize_memory.format import format_transcript
from capsize_memory.repository import Turn


def test_format_transcript_empty() -> None:
    assert format_transcript([]) == "(none yet)"


def test_format_transcript_single_turn() -> None:
    result = format_transcript([Turn(speaker="alice", text="hi")])
    assert result == "- alice: hi"


def test_format_transcript_preserves_order() -> None:
    turns = [
        Turn(speaker="alice", text="first"),
        Turn(speaker="capsize", text="second"),
        Turn(speaker="bob", text="third"),
    ]
    result = format_transcript(turns)
    assert result == (
        "- alice: first\n- capsize: second\n- bob: third"
    )


def test_format_transcript_multi_speaker() -> None:
    turns = [
        Turn(speaker="alice", text="hey everyone"),
        Turn(speaker="bob", text="hi alice"),
    ]
    result = format_transcript(turns)
    assert "alice" in result
    assert "bob" in result
