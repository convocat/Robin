---
name: robin-backlog
description: "Maintain this repo's backlog (BACKLOG.md) and write a session handover (HANDOVER.md). Two routines in one small skill: backlog keeps Open/In progress/Done current; handover snapshots where things stand for whoever picks this up next. Triggers: '/robin-backlog', 'what's open', 'update the backlog', 'add to the backlog', 'handover', 'hand this off', 'wrap up this session'."
---

# robin-backlog — backlog and handover for this repo

Two small, related routines. Figure out which one the request wants before acting: a question
about open work, or a request to log/close/add an item, is the **backlog** routine; a request to
summarize the session for someone else (or future-you) is the **handover** routine. If genuinely
unclear, ask.

## Routine 1 — Backlog

`BACKLOG.md` has three sections: **Open**, **In progress**, **Done**. Keep edits small and
targeted — don't rewrite the whole file for a one-line change.

- **"What's open" / "what am I waiting on"** — read `BACKLOG.md` and summarize the Open and In
  progress sections in a few lines. Don't just dump the file back verbatim.
- **"Add to the backlog"** — append one bullet under Open, written the way the existing bullets
  are written (bold lead-in, then one or two sentences of why/what). Don't invent urgency or
  priority that wasn't stated.
- **A settled use case from `robin-usecase-discovery`** — one bullet, naming the build task, pointing
  at its doc: `**<task>.** See `discovery/<slug>.md` for the settled design.` Don't copy the
  analysis into the backlog line; the doc is the source of truth, the backlog line is just a
  pointer to it.
- **"Close / done" / "I finished X"** — move the matching bullet from Open (or In progress) to
  the top of Done, past tense, same level of detail.
- **"Start working on X"** — move it from Open to In progress.
- Before adding anything, skim the repo for whether it's already true (e.g. check the code, or
  `git log`) rather than trusting only what the user says — this backlog is meant to stay
  trustworthy, not just a wish list.

## Routine 2 — Handover

`HANDOVER.md` is a **snapshot**, not a log: each run replaces it, it doesn't append. History
belongs in `BACKLOG.md`'s Done section or `git log`, not here.

When asked to hand off or wrap up:

1. Check `git status` and `git log -5 --oneline` to ground the summary in what's actually
   changed, not just what was discussed.
2. Re-read `BACKLOG.md` so "What's not done" in the handover matches it (update the backlog
   first if the conversation changed anything it doesn't yet reflect).
3. Rewrite `HANDOVER.md` with the same three sections as the existing file: **Where things
   stand**, **What's not done** (can just point at `BACKLOG.md` → Open), **Handy facts for
   whoever picks this up** (anything a fresh session would otherwise have to rediscover — env
   setup, gotchas, where things live).
4. Keep it short. A handover that takes longer to read than to re-derive has failed at its job.

## Notes

- This is deliberately small — a teaching example of a repo-local workflow skill, not a
  replacement for a real project-management tool.
- Never put secrets (API keys, tokens) in either file. Point at `.env` or `.env.example`
  instead of repeating values.
