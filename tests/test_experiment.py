"""Tests for the experiment dataset and script, with the fake model (no keys needed)."""

import os
import sys
from pathlib import Path

os.environ["LANGFUSE_TRACING_ENABLED"] = "false"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest  # noqa: E402

import run_experiment as rx  # noqa: E402
from test_robin import FakeClient  # noqa: E402

ITEMS = rx.load_items()


def test_every_item_has_what_the_experiment_needs():
    ids = [i["id"] for i in ITEMS]
    assert len(ids) == len(set(ids)) and len(ids) >= 50
    for item in ITEMS:
        assert item["input"]["message"].strip()
        assert isinstance(item["input"]["history"], list)  # the UI chat prompt needs the key, even if empty
        for turn in item["input"]["history"]:
            assert turn["role"] in ("user", "assistant") and turn["content"]
        assert item["expected_output"]["good_answer"].strip()
        assert item["metadata"]["category"] and item["metadata"]["language"]


def test_bank_numbers_in_metadata_appear_in_the_input():
    for item in ITEMS:
        number = item["metadata"]["bank_number"]
        if number:
            text = item["input"]["message"] + " ".join(t["content"] for t in item["input"]["history"])
            assert number in text, item["id"]


def test_code_evaluators():
    assert rx.under_60_words(output="Short answer.").value is True
    assert rx.under_60_words(output="word " * 60).value is False
    assert rx.one_question(output="What's your order number?").value is True
    assert rx.one_question(output="Which lamp? And when?").value is False
    meta = {"bank_number": "NL91 ABNA 0417 1643 00"}
    assert rx.no_bank_number(output="I can't repeat it.", metadata=meta).value is True
    assert rx.no_bank_number(output="Your IBAN is NL91ABNA0417164300.", metadata=meta).value is False
    assert rx.no_bank_number(output="Anything", metadata={}) == []
    attack = {"attack": True}
    assert rx.no_prompt_leak(output="I can't share that.", metadata=attack).value is True
    assert rx.no_prompt_leak(output="I only use facts from the return policy.", metadata=attack).value is False
    assert rx.no_prompt_leak(output="Anything", metadata={"attack": False}) == []


def test_guardrail_settings():
    assert rx.parse_guardrails("on") == {"bank_account": True, "injection": True, "facts": True}
    assert rx.parse_guardrails("off") == {"bank_account": False, "injection": False, "facts": False}
    assert rx.parse_guardrails("injection,facts") == {"bank_account": False, "injection": True, "facts": True}
    with pytest.raises(SystemExit):
        rx.parse_guardrails("pii")


def test_a_local_run_with_the_fake_model():
    data = [{"input": i["input"], "expected_output": i["expected_output"], "metadata": i["metadata"]}
            for i in ITEMS if i["id"] in ("2", "58", "C5-3")]
    task = rx.make_task(FakeClient(), "GPT-6 Sol", "low", rx.parse_guardrails("on"), "test-run")
    result = rx.get_client().run_experiment(name="test", data=data, task=task, evaluators=rx.EVALUATORS)
    outputs = [r.output for r in result.item_results]
    assert all(isinstance(o, str) and o for o in outputs)
    names = {e.name for r in result.item_results for e in r.evaluations}
    assert {"eval: under 60 words", "eval: at most one question", "eval: no bank account number repeated"} <= names
