# Robin — session handover

*Written by the `robin-handover` skill. Each run replaces this file — it's a snapshot of where
things stand, not a log. For history, see `BACKLOG.md`'s Done section or `git log`.*

## Where things stand (2026-11-16)

Robin is cloned locally at this repo, connected to the real Langfuse project and the real Render
Postgres for look-up (RAG). The local Flask server and the new `dashboard-kit/` dashboard are
both runnable via their skills (`robin-dashboard`).

Langfuse tracing, the 51-item experiment set (look-up on, guardrails on/off), and the Product
Owner / conversation-log dashboard were all verified working end to end tonight.

## What's not done

See `BACKLOG.md` → Open. The two most concrete ones: the handbook's free-shipping number
contradicts itself (€50 vs €75), and Robin has no real answer when a customer asks for a human.

## Handy facts for whoever picks this up

- Local venv: `.venv/` (Python). Node deps for the dashboard's thread view:
  `dashboard-kit/thread-view/node_modules/` (run `npm install` there if missing).
- `.env` has real `OPENAI_API_KEY`, `LANGFUSE_*` and `DATABASE_URL` — never commit it.
- `dashboard-kit/dashboard-data.json` is generated from Langfuse (`robin_adapter.py`) and
  gitignored on purpose: it holds real course participants' messages.
- A throwaway local Postgres+pgvector Docker container (`robin-pgvector`) is still running from
  before the real Render database was wired in. Safe to stop; nothing depends on it anymore.
