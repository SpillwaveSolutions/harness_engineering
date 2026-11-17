"""Tests for listing 06-08-memory-subsystem.

ProvenanceEnvelope and the audit log are file-backed. Memory calls
use the in-memory fake unless HARNESS_LIVE_API=1.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict

import pytest


def test_provenance_envelope_serializes_to_dict(load_listing) -> None:
    module = load_listing("06-08-memory-subsystem")
    env = module.ProvenanceEnvelope(
        session_id="s-1",
        timestamp="2026-05-22T20:00:00Z",
        trust_score=0.8,
        source_channel="user_input",
        entry_content="user prefers vegetarian",
    )
    dumped = asdict(env)
    assert dumped["session_id"] == "s-1"
    assert dumped["trust_score"] == 0.8
    assert dumped["entry_content"] == "user prefers vegetarian"


def test_audit_log_reads_existing_jsonl(
    load_listing, tmp_path, monkeypatch
) -> None:
    module = load_listing("06-08-memory-subsystem")
    log_path = tmp_path / "memory_audit.jsonl"
    monkeypatch.setattr(module, "AUDIT_LOG", log_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    entries = [
        {
            "op": "write",
            "session_id": "s1",
            "timestamp": "t1",
            "trust_score": 0.8,
            "source_channel": "user_input",
            "entry_content": "prefers vegan",
        },
        {
            "op": "read",
            "session_id": "s1",
            "timestamp": "t2",
            "query": "food prefs",
            "retrieved_count": 2,
        },
    ]
    with log_path.open("w") as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + "\n")
    subsystem = module.InspectableMemorySubsystem("test-user")
    log = subsystem.audit_log()
    assert len(log) == 2
    assert log[0]["op"] == "write"
    assert log[1]["op"] == "read"


def test_audit_log_returns_empty_when_no_log_file(
    load_listing, tmp_path, monkeypatch
) -> None:
    module = load_listing("06-08-memory-subsystem")
    monkeypatch.setattr(module, "AUDIT_LOG", tmp_path / "missing.jsonl")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    subsystem = module.InspectableMemorySubsystem("test-user")
    assert subsystem.audit_log() == []


def test_offline_write_read_inspect(
    load_listing, tmp_path, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    module = load_listing("06-08-memory-subsystem")
    monkeypatch.setattr(module, "AUDIT_LOG", tmp_path / "audit.jsonl")
    subsystem = module.InspectableMemorySubsystem(
        "ada", session_id="sess-1"
    )
    written = subsystem.write(
        [{"role": "user", "content": "allergic to shellfish"}],
        trust_score=0.95,
    )
    assert written == [{"memory": "allergic to shellfish"}]
    assert subsystem.read("shellfish") == ["allergic to shellfish"]
    assert subsystem.inspect() == [{"memory": "allergic to shellfish"}]
    log = subsystem.audit_log()
    assert log[0]["op"] == "write"
    assert log[0]["trust_score"] == 0.95
    assert log[1]["op"] == "read"


@pytest.mark.skipif(
    os.environ.get("HARNESS_LIVE_API") != "1",
    reason="set HARNESS_LIVE_API=1 to exercise the live API",
)
def test_live_write_records_envelope(
    load_listing, tmp_path, monkeypatch
) -> None:
    module = load_listing("06-08-memory-subsystem")
    monkeypatch.setattr(module, "AUDIT_LOG", tmp_path / "audit.jsonl")
    subsystem = module.InspectableMemorySubsystem("live-user")
    subsystem.write(
        [{"role": "user", "content": "I'm allergic to shellfish."}],
        trust_score=0.95,
        source_channel="user_input",
    )
    log = subsystem.audit_log()
    writes = [entry for entry in log if entry["op"] == "write"]
    assert writes
    assert any(entry.get("trust_score") == 0.95 for entry in writes)
