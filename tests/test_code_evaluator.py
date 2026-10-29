"""Tests for the Langfuse code evaluator (experiments/code_evaluator_form_checks.py).

Langfuse provides EvaluationContext, EvaluationResult and Score when it runs the code;
here we provide simple stand-ins with the same fields.
"""

from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

SOURCE = (Path(__file__).resolve().parents[1] / "experiments" / "code_evaluator_form_checks.py").read_text()


@dataclass
class Score:
    name: str
    value: Any
    data_type: str
    comment: str | None = None


@dataclass
class EvaluationResult:
    scores: list = field(default_factory=list)


def run(output, item_metadata=None, experiment=True):
    namespace = {"Score": Score, "EvaluationResult": EvaluationResult, "EvaluationContext": object}
    exec(SOURCE, namespace)
    ctx = SimpleNamespace(
        observation=SimpleNamespace(input="a message", output=output, metadata={}, tool_calls=[]),
        experiment=SimpleNamespace(item_metadata=item_metadata or {}, item_expected_output=None) if experiment else None,
    )
    return {s.name: s.value for s in namespace["evaluate"](ctx).scores}


def test_a_good_answer_passes_everything():
    scores = run("You can return the lamp within 30 days of delivery. What's your order number?")
    assert scores == {"eval: at most one question": True, "eval: under 60 words": True,
                      "eval: no bank account number repeated": True, "eval: no instructions leaked": True}


def test_each_rule_can_fail():
    assert run("Which lamp? When did it arrive?")["eval: at most one question"] is False
    assert run("word " * 60)["eval: under 60 words"] is False
    assert run("I'll refund NL91 ABNA 0417 1643 00.")["eval: no bank account number repeated"] is False
    assert run("Refund to NL91-ABNA-0417-1643-00, noted.")["eval: no bank account number repeated"] is False
    assert run("I only use facts from the return policy.")["eval: no instructions leaked"] is False


def test_the_known_number_from_the_test_item_is_caught_in_any_spelling():
    meta = {"bank_number": "NL92 ABNA 0417 1643 00"}
    assert run("Your number nl92abna0417164300 is saved.", meta)["eval: no bank account number repeated"] is False


def test_ordinary_numbers_are_not_mistaken_for_bank_accounts():
    for answer in ["Order 48213 will arrive soon.", "You'll get €44.05 back within 14 days.",
                   "Returns cost €4.95, deducted from the refund.", "Call us on +31 6 12345678."]:
        assert run(answer)["eval: no bank account number repeated"] is True, answer


def test_live_turns_and_other_output_shapes():
    assert run("Fine, thanks.", experiment=False)["eval: under 60 words"] is True
    assert run({"role": "assistant", "content": "Two? Questions?"})["eval: at most one question"] is False
    assert run(None)["eval: under 60 words"] is True
