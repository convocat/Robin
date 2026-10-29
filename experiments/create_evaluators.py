"""Create Robin's LLM-as-a-Judge evaluators in Langfuse, from the prompts in EVALUATORS.md.

    python experiments/create_evaluators.py            # create the evaluators and rules
    python experiments/create_evaluators.py --dry-run  # only show what would be created

Every "## eval: ..." section in EVALUATORS.md with a prompt becomes one Boolean evaluator, so the
evaluators in Langfuse always match the file. Evaluators and rules that already exist (same name)
are left alone, so running this twice is safe.

Two rules are created:
- "Robin – experiments" (on): runs the experiment evaluators on every new run of robin-experiment.
- "Robin – live chats" (off): the same evaluators for Robin's chat turns. Switch it on in Langfuse
  when you want live scoring; every judgement is a paid model call.

Uses LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY and LANGFUSE_BASE_URL from .env or the environment.
The judges run on JUDGE_MODEL (default gpt-6-luna) through the project's OpenAI LLM connection.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from langfuse import get_client  # noqa: E402
from langfuse.api.evaluation_commons.types.evaluation_rule_filter import (  # noqa: E402
    EvaluationRuleFilter_Boolean,
    EvaluationRuleFilter_StringOptions,
)
from langfuse.api.evaluation_commons.types.evaluator_output_definition import (  # noqa: E402
    EvaluatorOutputDefinition_Boolean,
)
from langfuse.api.evaluation_commons.types.prompt_variable_mapping_input import (  # noqa: E402
    PromptVariableMappingInput,
)
from langfuse.api.evaluation_rules.types.evaluation_rule_evaluator_assignment_input import (  # noqa: E402
    EvaluationRuleEvaluatorAssignmentInput,
)
from langfuse.api.evaluators.types.create_evaluator_request import CreateEvaluatorRequest_LlmAsJudge  # noqa: E402
from langfuse.api.evaluators.types.evaluator_model_config import EvaluatorModelConfig  # noqa: E402

EVALUATORS_FILE = ROOT / "EVALUATORS.md"
DATASET = "robin-experiment"
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-6-luna")

# Which evaluators each rule uses. Names as in EVALUATORS.md.
EXPERIMENT_EVALS = [
    "eval: one question at a time",
    "eval: short answer",
    "eval: no bank account number repeated",
    "eval: no instructions leaked",
    "eval: only facts from the policy",
    "eval: matches the good answer",
]
LIVE_EVALS = [
    "eval: one question at a time",
    "eval: short answer",
    "eval: no bank account number repeated",
    "eval: no instructions leaked",
    "eval: only facts from the policy",
    "eval: clear next step",
    "eval: natural language",
]
SOURCES = {"input": "input", "output": "output", "expected_output": "expected_output"}


def read_evaluators() -> dict[str, str]:
    """name -> prompt, from every '## eval: ...' section that has a ``` prompt block."""
    text = EVALUATORS_FILE.read_text(encoding="utf-8")
    found = {}
    for match in re.finditer(r"^## (eval: [^\n(]+?)\s*(?:\([^)]*\))?\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S):
        name, body = match.group(1).strip(), match.group(2)
        block = re.search(r"```\n(.*?)\n```", body, re.S)
        if block:
            found[name] = block.group(1).strip()
    return found


def variables_of(prompt: str) -> list[str]:
    seen = []
    for var in re.findall(r"\{\{\s*(\w+)\s*\}\}", prompt):
        if var not in seen:
            seen.append(var)
    return seen


def mapping_for(prompt: str) -> list[PromptVariableMappingInput]:
    unknown = [v for v in variables_of(prompt) if v not in SOURCES]
    if unknown:
        raise SystemExit(f"No data source for prompt variable(s): {', '.join(unknown)}")
    return [PromptVariableMappingInput(variable=v, source=SOURCES[v]) for v in variables_of(prompt)]


def judge_model(langfuse) -> EvaluatorModelConfig | None:
    """The project's OpenAI connection with JUDGE_MODEL, or None for the project's default evaluation model."""
    try:
        connections = langfuse.api.llm_connections.list(limit=50).data
    except Exception as error:
        print(f"Couldn't read the LLM connections ({error}); using the project's default evaluation model.")
        return None
    for connection in connections:
        if "openai" in str(getattr(connection, "provider", "")).lower() or \
           "openai" in str(getattr(connection, "adapter", "")).lower():
            return EvaluatorModelConfig(provider=connection.provider, model=JUDGE_MODEL)
    print("No OpenAI LLM connection found; using the project's default evaluation model.")
    return None


def list_all(list_page) -> list:
    items, cursor = [], None
    while True:
        page = list_page(limit=100, cursor=cursor) if cursor else list_page(limit=100)
        items.extend(page.data)
        cursor = getattr(getattr(page, "meta", None), "next_cursor", None) or getattr(page, "next_cursor", None)
        if not cursor:
            return items


def build_requests(prompts: dict[str, str], model) -> dict[str, CreateEvaluatorRequest_LlmAsJudge]:
    requests = {}
    for name, prompt in prompts.items():
        requests[name] = CreateEvaluatorRequest_LlmAsJudge(
            name=name,
            description="Robin, the Nest & Co chatbot. Prompt from EVALUATORS.md in github.com/convocat/Robin.",
            prompt=prompt,
            model_config_=model,
            variable_mapping=mapping_for(prompt),
            output_definition=EvaluatorOutputDefinition_Boolean(
                score_reasoning_instructions="One sentence explaining the decision.",
                score_value_instructions="true if the answer meets the criterion, false if it doesn't.",
            ),
        )
    return requests


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="show what would be created, change nothing")
    args = parser.parse_args()

    prompts = read_evaluators()
    missing = [n for n in set(EXPERIMENT_EVALS + LIVE_EVALS) if n not in prompts]
    if missing:
        raise SystemExit(f"Not found in EVALUATORS.md: {', '.join(missing)}")

    langfuse = get_client()
    model = None if args.dry_run else judge_model(langfuse)
    requests = build_requests(prompts, model)
    if args.dry_run:
        for name, request in requests.items():
            print(f"- {name}: variables {', '.join(variables_of(request.prompt))}")
        print(f"Rules: 'Robin – experiments' ({len(EXPERIMENT_EVALS)} evaluators, on), "
              f"'Robin – live chats' ({len(LIVE_EVALS)} evaluators, off)")
        return

    # 1. Evaluators (skip names that already exist)
    existing = {e.name: e.id for e in list_all(langfuse.api.evaluators.list)}
    ids = {}
    for name, request in requests.items():
        if name in existing:
            ids[name] = existing[name]
            print(f"Exists, left as it is: {name}")
        else:
            ids[name] = langfuse.api.evaluators.create(request=request).id
            print(f"Created evaluator: {name}")

    # 2. Rules
    rules = {r.name for r in list_all(langfuse.api.evaluation_rules.list)}
    dataset_id = langfuse.get_dataset(DATASET).id

    def assignments(names, drop_expected=False):
        result = []
        for n in names:
            mapping = None
            if drop_expected:  # live chats have no expected output
                mapping = [m for m in mapping_for(prompts[n]) if m.variable != "expected_output"]
            result.append(EvaluationRuleEvaluatorAssignmentInput(evaluator_id=ids[n], variable_mapping=mapping))
        return result

    if "Robin – experiments" in rules:
        print("Exists, left as it is: rule Robin – experiments")
    else:
        langfuse.api.evaluation_rules.create(
            name="Robin – experiments", enabled=True, sampling=1.0,
            filter=[
                EvaluationRuleFilter_Boolean(column="isExperimentItemRootSpan", operator="=", value=True),
                EvaluationRuleFilter_StringOptions(column="datasetId", operator="any of", value=[dataset_id]),
            ],
            evaluator_assignments=assignments(EXPERIMENT_EVALS),
        )
        print(f"Created rule: Robin – experiments ({len(EXPERIMENT_EVALS)} evaluators, on)")

    if "Robin – live chats" in rules:
        print("Exists, left as it is: rule Robin – live chats")
    else:
        langfuse.api.evaluation_rules.create(
            name="Robin – live chats", enabled=False, sampling=1.0,
            filter=[
                EvaluationRuleFilter_StringOptions(column="name", operator="any of", value=["Robin – chat turn"]),
                EvaluationRuleFilter_Boolean(column="isRootObservation", operator="=", value=True),
                EvaluationRuleFilter_StringOptions(column="environment", operator="any of", value=["course"]),
            ],
            evaluator_assignments=assignments(LIVE_EVALS, drop_expected=True),
        )
        print(f"Created rule: Robin – live chats ({len(LIVE_EVALS)} evaluators, off: switch it on in Langfuse)")


if __name__ == "__main__":
    main()
