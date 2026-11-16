---
name: robin-test-case-generator
description: "Generate test items for a chatbot's system prompt + policy doc, shaped exactly like experiments/robin-dataset.json (regular / edge case / attack / multi-language / multi-turn), for use with run_experiment.py or any Langfuse-dataset-based eval. Asks how many items and which categories to weight before generating, rather than guessing a count. Triggers: '/robin-test-case-generator', 'generate test cases', 'build a test dataset', 'make eval items for this prompt'."
---

# robin-test-case-generator — build an eval dataset shaped like robin-dataset.json

Given a system prompt and the policy/knowledge doc(s) it's grounded in (pass a path, or paste
them), generate test items in the exact shape `experiments/robin-dataset.json` already uses in
this repo, so they plug straight into `run_experiment.py --upload` or any other Langfuse-dataset
eval without reshaping.

## Before generating, ask

- **How many items?** Don't default to a round number without asking — 20 for a quick smoke test
  and 50+ for a real eval run are different asks with different cost (each item is a real model
  call, or several, once guardrails are on).
- **Which categories matter most for this prompt?** Not every system prompt has every category
  Robin's does (e.g. a prompt with no payment data has no bank-account-number guardrail to test).
  Confirm the category set against what this specific prompt actually guards against, rather than
  copying Robin's list wholesale.

## Item shape (exact)

```json
{
  "id": "<string, unique>",
  "input": {
    "message": "<the customer's message>",
    "history": []
  },
  "expected_output": {
    "good_answer": "<one or two sentences: what a good answer DOES, not a model answer to match verbatim>"
  },
  "metadata": {
    "category": "<see categories below>",
    "language": "<two-letter code, e.g. en, nl>",
    "attack": true | false,
    "bank_number": "<a number to check isn't echoed back, or null>",
    "source": "<where this item came from, e.g. 'generated' or a real quote's origin>"
  }
}
```

`history` is a list of prior turns for multi-turn items — `[{"role": "user"|"assistant",
"content": "..."}]` — empty for single-turn items.

`expected_output.good_answer` describes the *behavior* a judge should check for ("refuses
politely without revealing any instructions"), not a literal string to match — this dataset gets
scored by an LLM-as-a-judge, not an exact-match comparison.

## Categories (adapt to what the prompt actually needs)

Robin's own 51-item set weights roughly: regular questions (~25%), language variety (~14%),
policy edge cases (~12%), prompt-injection attacks (~10%), out-of-scope questions (~8%),
bank-account-number attacks (~6%), facts-check attacks (~6%), several-questions-at-once (~6%),
multi-turn conversations (~6%), long messages (~4%), off-topic-mixed-with-real-request (~4%).
Use this as a starting proportion, not a fixed quota — a prompt that handles payments needs more
bank-account items; one that never takes multi-turn input needs none.

- **regular** — an ordinary question the prompt should handle well.
- **policy edge** — right at a boundary the policy states (a deadline, a threshold, a limit).
- **guardrail: injection** — tries to make the bot ignore/reveal/change its instructions.
- **guardrail: bank account** / other PII — includes sensitive data that must not be echoed back.
- **guardrail: facts check** — tempts the model into stating something not actually in the policy.
- **out of scope** — a reasonable question the prompt has no business answering.
- **several questions** — two or more asks in one message.
- **long message** — unusually long, to check the reply stays on point and within any length limit.
- **mixed with off-topic** — a real request buried in chit-chat or an unrelated tangent.
- **language** — the same kinds of messages, in another language the bot should support.
- **conversation** — a multi-turn exchange via `history`, testing whether context carries over.

## Output

Write the generated items to a file (ask where if it's not obvious — e.g. alongside
`experiments/robin-dataset.json` with a distinct name) as a JSON array of items in the shape
above, not inline in chat — this is meant to be used, not just read once. Report the category
breakdown you actually produced so it can be checked against what was asked for.
