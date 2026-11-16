# Teaching guide — Robin's dashboard & Claude Code for conversation design

Prepared for the *GenAI design for conversations and content* course. Use this as a reference
during live-coding and as a handout for students who want to try these at home.

## A. Example live-coding prompts for the dashboard

Prompts to type into Claude Code against `dashboard-kit/`, roughly easy → harder. Each one is a
real, scoped change, not a toy example.

1. "Add a language toggle (NL/EN) that switches all dashboard labels, without touching the
   underlying data."
2. "Add an Evals tab showing, per Langfuse evaluator, the pass rate across the experiment runs —
   filterable by model and guardrail setting."
3. "Show each retrieved chunk's similarity score as a small bar instead of a number, and flag
   anything below 0.3 as a weak match."
4. "Add a side-by-side view comparing the same test item's answer with guardrails on vs off."
5. "Add a filter for 'prompt label' so I can see which conversations used a student's own
   system-prompt version instead of production."

## B. Small use cases for content/conversation designers in their own Claude Code

None of these need this dashboard or even this project — they work in any Claude Code session:

- Paste a draft conversation flow, ask Claude to list every point a user could get stuck with no
  fallback.
- Ask for 10 adversarial test messages (jailbreaks, rude customers, edge cases) before a bot
  ships.
- Paste a batch of real user messages, ask Claude to cluster them into intents you hadn't
  anticipated.
- Ask Claude to shrink a system prompt to the smallest version with the same behavior, then diff
  what changed.
- Have Claude check a system prompt against Grice's maxims or Cathy Pearl's principles and flag
  violations.
- Turn a batch of real transcripts into a "model answer" dataset for evals.

## C. Small skill ideas

Packaged versions of the use cases above, so they're one slash command instead of a fresh prompt
each time:

- `robin-conversation-design-review` — paste a flow or system prompt, get a structured critique
  (clarity, repair, one-question-at-a-time, tone).
- `robin-test-case-generator` — given a system prompt + a policy doc, generate test items shaped
  like Robin's `experiments/robin-dataset.json` (regular / edge case / attack / multi-language).
- `robin-trace-to-persona` — pull real Langfuse conversations and summarize recurring user
  personas/intents for a content manager.

## What's live right now, for the demo

- `dashboard-kit/` — the Product Owner / conversation-log dashboard, reusing the
  Mai Montferland `dashboard-kit` pattern, adapted to pull real traces from Langfuse
  (`dashboard-kit/robin_adapter.py`) instead of Flowise exports.
- Conversations expand **inline** in the log table (no popup). Each expanded conversation is
  rendered by `dashboard-kit/thread-view/`, a small `@assistant-ui/react` app — the same
  primitives (`ThreadPrimitive`, `MessagePrimitive`) as Robin's own chat widget and the
  Montferland `agent-frontend`.
- Retrieved chunks show as colored chips under Robin's answer when look-up (RAG) was on — green
  ≥0.5 similarity, orange below, the same threshold convention as the Montferland debug panel's
  RAG Scores.
- Two Langfuse experiment runs exist for the full 51-item test set with look-up on: guardrails on
  and guardrails off, both on GPT-6 Sol.

