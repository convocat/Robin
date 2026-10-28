"""The bank account test set (bank_account_cases.csv), run against the real guardrail.

MASKED = must be removed, PASS = must stay, KNOWN GAP = a real bank account number the
guardrail misses today. Known gaps are marked xfail: if you improve the guardrail and one
starts to pass, pytest tells you, so you can change its row to MASKED.
"""

import csv
import os
import sys
from pathlib import Path

os.environ["LANGFUSE_TRACING_ENABLED"] = "false"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

import robin  # noqa: E402

CASES = list(csv.DictReader(open(Path(__file__).with_name("bank_account_cases.csv"), encoding="utf-8")))


def _param(case):
    marks = [pytest.mark.xfail(reason=case["why"], strict=True)] if case["expected"] == "KNOWN GAP" else []
    return pytest.param(case, id=case["message"][:40], marks=marks)


@pytest.mark.parametrize("case", [_param(c) for c in CASES])
def test_bank_account_case(case):
    _, found = robin.mask_bank_accounts(case["message"])
    if case["expected"] == "PASS":
        assert found == 0, case["why"]
    else:  # MASKED, or a KNOWN GAP that should be masked one day
        assert found > 0, case["why"]
