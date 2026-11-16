# Robin — backlog

Simple backlog for this repo: Open → In progress → Done. Edit by hand or via the
`robin-backlog` skill (`/robin-backlog`).

## Open

- **Fix the handbook's free-shipping inconsistency.** `content/handbook.md` (and the matching
  `robin/handbook` prompt in Langfuse) says "Free shipping on all orders from €50!" in Ordering
  and payment, but €75 in Delivery. The changelog shows the threshold was raised in v3.2 but the
  Ordering section's teaser line was never updated.
- **Give Robin a real escalation path.** When a customer insists on a human (seen for real in the
  traces — "I need to talk with a human agent" x3), Robin has no contact info to offer: the
  default system prompt only injects `RETURN_POLICY`, not Customer Care's hours/channel.
- **Add English language to the PO/CxD dashboard** (`dashboard-kit/`, currently Dutch-only UI).
  Planned as a live-coding demo.
- **Add an evals dashboard to the PO/CxD dashboard** (`dashboard-kit/`) — per-evaluator pass rate
  across experiment runs, filterable by model and guardrail setting.
- **Migrate `dashboard-kit/robin_adapter.py` off the deprecated Langfuse endpoints**
  (`/api/public/traces`, `/api/public/scores`) to `/api/public/v2/observations` and
  `/api/public/v3/scores` before Langfuse actually removes the old ones.
- **Decide what happens to the Beoordeling (review) panel in `thread-view/`.** It's UI-only right
  now — toggles don't persist. Either wire it to something, or keep it as a teaching mockup and
  say so clearly.

## In progress

- *(nothing right now)*

## Done

- Cloned the repo locally, wired up `.env`, confirmed Langfuse tracing end to end.
- Connected the real Render Postgres for look-up (RAG); ran the ingestion pipeline.
- Ran the 51-item experiment set with look-up on, guardrails on and off.
- Built `dashboard-kit/`: Product Owner + conversation-log dashboard adapted from the Montferland
  dashboard-kit, with inline-expanding rows, an `@assistant-ui/react` thread view, and a
  Bronnen/Beoordeling panel matching the Waddinxveen reference.
- Added the `robin-dashboard` skill to launch it on demand.
