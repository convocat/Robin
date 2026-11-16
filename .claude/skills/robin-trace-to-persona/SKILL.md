---
name: robin-trace-to-persona
description: "Pull real Robin conversations from Langfuse and summarize recurring user personas and intents for a content manager — not raw analytics, not a dashboard, a short written read of who's actually talking to Robin and what they want. Reuses dashboard-kit/dashboard-data.json when it's fresh instead of re-querying Langfuse. Triggers: '/robin-trace-to-persona', 'who's talking to Robin', 'summarize user personas', 'what are people actually asking'."
---

# robin-trace-to-persona — turn real conversations into personas a content manager can use

This is for a content manager, not a dashboard: a short written read of who's actually talking
to Robin and what they want, with real quotes — not a chart, not a trace-by-trace report.

## Step 1 — Get the data

Check whether `dashboard-kit/dashboard-data.json` exists and is recent (compare its newest
conversation's `time` against now). If it's stale or missing, run the `robin-dashboard` skill's
Step 2 (`robin_adapter.py`) to refresh it rather than writing a second Langfuse query path — this
repo already has one correct way to pull conversations; reuse it.

## Step 2 — Cluster, don't just list

Group conversations by what the person actually wanted, not just the topic label already in the
data (those are coarse — "Shipping & delivery" covers both "do you deliver to Belgium" and "where
is my order", which are different intents). Within each topic, read the actual `preview` and
`messages` text and split further where the intent genuinely differs. Look especially at:

- **Repeat patterns** — the same kind of question asked by several different `userId`s, worded
  differently each time (that's a real recurring intent, not a one-off).
  - The same `userId` asking many variations in one session is a *tester* exploring the bot
    (jailbreak attempts, "are you human" probing), not a customer persona — call it out
    separately, don't fold it into a persona.
- **Frustration signals** — "useless", repeated requests for a human, a conversation that ends
  without resolution. These are personas too ("the customer who wants out to a human"), often the
  most useful one for a content manager to know about.
- **Mismatches** — someone asking something the bot's current knowledge doesn't cover (e.g.
  shipping questions when look-up is off) — worth flagging as a content gap, not just a persona
  trait.

## Step 3 — Write personas, not statistics

For each persona/intent cluster: a short name, what they want, how they tend to phrase it (one
or two real quotes, trimmed if long), roughly how often it shows up, and anything actionable for
a content manager (a gap in the handbook, a tone mismatch, a missing escalation path). Skip
clusters with only one example unless it's a notably sharp signal (e.g. a safety concern) —
don't manufacture a persona out of a single data point.

Don't include a user's name or exact userId in the written output beyond what's needed to show a
pattern exists — this is for understanding intent, not tracking individuals.

## Output format

A short written brief: 3-6 personas/intents, each a short paragraph with 1-2 real quotes, ending
with a one-line "so what" for each. No tables, no counts-only summary — if it reads like
analytics, it hasn't done its job.
