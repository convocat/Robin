"""Prompt labels: a student's own version of the system prompt, chosen in the course panel."""

import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ["LANGFUSE_TRACING_ENABLED"] = "false"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import prompts  # noqa: E402
import robin  # noqa: E402
from test_robin import FakeClient  # noqa: E402


class FakePrompt:
    def __init__(self, text, version, labels):
        self.text, self.version, self.labels, self.is_fallback = text, version, labels, False

    def compile(self, **values):
        return prompts.fill(self.text, **values)


class FakeLangfuse:
    """Prompt Management with one student version: 'leela' on version 7 of robin/system-prompt."""

    def get_prompt(self, name, label="production", **kwargs):
        if name == "robin/system-prompt" and label == "leela":
            return FakePrompt("LEELA'S SYSTEM PROMPT {{return_policy}}", 7, ["leela"])
        if label != "production":
            raise LookupError(f"no label {label}")
        return FakePrompt(prompts.LANGFUSE_PROMPTS[name], 3, ["production", "latest"])


def run(monkeypatch, label):
    fake = FakeLangfuse()
    monkeypatch.setattr(robin, "get_client", lambda: SimpleNamespace(
        get_prompt=fake.get_prompt, start_as_current_observation=robin_get_client().start_as_current_observation,
        get_current_trace_id=lambda: None, flush=lambda: None))
    client = FakeClient()
    result = robin.handle_turn("Can I return a vase?", [], client=client, label=label, guardrails={
        "bank_account": False, "injection": False, "facts": False})
    return result, client.calls[0]["messages"][0]["content"]


robin_get_client = robin.get_client


def test_a_student_label_uses_their_version(monkeypatch):
    result, system = run(monkeypatch, "Leela")
    assert system.startswith("LEELA'S SYSTEM PROMPT")
    assert result.summary["system_prompt_used"] == "leela (version 7)"


def test_an_unknown_label_falls_back_to_production(monkeypatch):
    result, system = run(monkeypatch, "amar")
    assert system == prompts.SYSTEM_PROMPT
    assert result.summary["system_prompt_used"] == "amar not found, so production (version 3)"


def test_no_label_means_production(monkeypatch):
    result, _ = run(monkeypatch, "")
    assert result.summary["system_prompt_used"] == "production (version 3)"


def test_labels_are_cleaned_up():
    assert robin.prompt_label("  Leela B! ") == "leelab"
    assert robin.prompt_label("production") is None and robin.prompt_label(None) is None
