"""Tests for the Vercel API (app.py), with the fake model from test_robin.py."""

import os
import sys
from pathlib import Path

os.environ["LANGFUSE_TRACING_ENABLED"] = "false"
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ["COURSE_PASSCODE"] = "nest"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest  # noqa: E402

import app as api  # noqa: E402
from test_robin import FakeClient  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    api.COURSE_PASSCODE = "nest"
    monkeypatch.setattr(api, "client", FakeClient())
    flushes = []
    monkeypatch.setattr(api, "get_client", lambda: type("C", (), {"flush": lambda self: flushes.append(1)})())
    test_client = api.app.test_client()
    test_client.flushes = flushes
    return test_client


def chat(client, **overrides):
    body = {"message": "Can I return a vase?", "history": [], "name": "Maaike", "passcode": "nest",
            "model": "GPT-6 Sol", "effort": "low", "session_id": "s1", **overrides}
    return client.post("/api/chat", json=body)


def test_normal_turn_returns_answer_and_flushes_once(client):
    response = chat(client)
    assert response.status_code == 200
    data = response.get_json()
    assert data["answer"] and "trace_id" in data and data["outcome"] == "answered"
    assert len(client.flushes) == 1


def test_wrong_passcode_is_refused(client):
    response = chat(client, passcode="wrong")
    assert response.status_code == 403 and response.get_json()["error"] == "passcode"
    assert len(client.flushes) == 1


def test_empty_message_and_missing_name_are_refused(client):
    assert chat(client, message="  ").get_json()["error"] == "message"
    assert chat(client, name="").get_json()["error"] == "name"


def test_message_limit(client):
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}] * api.MAX_MESSAGES
    assert chat(client, history=history[: 2 * api.MAX_MESSAGES]).get_json()["error"] == "limit"


def test_masked_message_is_returned(client):
    data = chat(client, message="Refund to NL91 ABNA 0417 1643 00").get_json()
    assert "0417" not in data["customer_message"]


def test_feedback_flushes(client):
    response = client.post("/api/feedback", json={"trace_id": "abc", "liked": True})
    assert response.status_code == 200 and len(client.flushes) == 1


def test_index_serves_the_widget(client):
    response = client.get("/")
    assert response.status_code == 200 and b"Nest" in response.data


def test_guardrail_switches_reach_robin(client):
    data = chat(client, message="Refund to NL91 ABNA 0417 1643 00",
                guardrails={"bank_account": False, "injection": False, "facts": False}).get_json()
    assert "0417" in data["customer_message"] and data["outcome"] == "answered"
