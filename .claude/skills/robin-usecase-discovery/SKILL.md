---
name: robin-usecase-discovery
description: "Co-design a use case with Maaike before any build starts: she calls this explicitly when she has a new idea, and it turns the conversation into a structured discovery doc (problem, current process, human/rule/GenAI split, open questions) that both of us keep refining across turns — not Claude investigating alone and firing questions back. Based on Maaike's five-step GenAI design process (Define problem -> Map current process -> Identify AI potential), run as a guided back-and-forth instead of a report. Only called deliberately: '/robin-usecase-discovery', 'let's design this', 'use case discovery', 'let's think this through before we build it'."
---

# robin-usecase-discovery — co-design a use case before building it

This is **not** a gate that fires automatically before every build request, and it is **not**
Claude going off to inspect the codebase and reporting back findings and questions. Maaike calls
this on purpose, when she has a new idea and wants to think it through together before anyone
writes code. The point is a shared, structured document that captures *her* thinking as it
develops — Claude's job is to ask the right next question and write her answers down well, not
to go research an answer on its own and present a verdict.

## The document

Every use case gets one file: `discovery/<slug>.md` (make the `discovery/` folder if it doesn't
exist yet; pick `<slug>` from what she's designing, e.g. `discovery/evals-tab.md`). This file is
the running memory of the design conversation — read it back before continuing a design that
already has a file, and keep editing the same file turn over turn rather than starting fresh or
holding the state only in your own context.

Use this structure, matching the five-step process (stop at step 3 unless she explicitly wants
to go further into workflow/prompt design in the same session):

```markdown
# <use case name>

**Status:** Draft <!-- Draft while co-designing; change to "Settled — ready to build" when done -->

## 1. Problem
What are we really solving? (not the solution — the problem underneath it)
Do we want more of this, or remove what's in the way?

## 2. Current process
Who does this today, and how? (steps, tools, decisions, what goes wrong)
| # | Step | Who | Source/tool | Decision | What can go wrong |

## 3. AI potential
Per step: Human / Rule or code / GenAI, and why.
Is what's left for the human still a coherent job?

## Open questions
Things neither of us has answered yet.

## Decisions
Things we've settled, and why — so we don't re-litigate them next time.
```

## How the conversation works

1. **Start from what she gives you.** If she opens with a few sentences, a voice-note-style
   stream of thoughts, or a half-formed idea, don't ask her to restate it formally — take what
   she said, slot it into the right section, and reflect it back briefly so she can correct it.
2. **Ask one real question at a time**, not a checklist. Pull it from whichever section is
   thinnest right now: if you don't know the real problem yet, ask about that before asking about
   process steps. If she's already told you the process, don't re-ask it to be thorough.
3. **Write to the file after each meaningful exchange**, not just at the end — this is the point
   of the document existing: it survives even if the conversation is interrupted or picked up
   later, by her or by a fresh session.
4. **Only touch the codebase when she asks you to**, or when confirming a concrete, checkable
   fact she's relying on ("is that evaluator actually already running?") — and say what you
   checked and what you found, briefly, then hand the thread back to her. Don't quietly do a
   broad investigation and return with a findings report; that's the opposite of co-design.
5. **Surface disagreement or tension as a question, not a silent choice.** If what she just said
   contradicts something earlier in the doc, point it out instead of picking one and moving on.
6. **Decide "done" together.** When the open questions are answered or explicitly accepted as
   risks, and the process + classification hold together, say so and ask if she wants to call
   discovery settled — don't declare it settled unilaterally, and don't keep going past the
   point she's satisfied either.

## What happens after

Once she says it's settled, finish the document and put it on the backlog — this is part of the
skill, not a separate request:

1. Set `**Status:** Settled — ready to build` at the top of `discovery/<slug>.md`, and read the
   whole file over once as if you'd never seen the conversation: tighten anything that only made
   sense in the moment, fill in a one- or two-line summary at the very top if the problem
   statement needs it, and make sure every section (Problem, Current process, AI potential, Open
   questions, Decisions) reads as a finished analysis, not raw notes. This is now a real design
   doc, not a scratchpad — it may get read by someone who wasn't in the conversation.
2. Add it to `BACKLOG.md` under **Open**, in the same style as the existing bullets, naming the
   doc: `**<Use case, as a build task>.** See `discovery/<slug>.md` for the settled design.` Use
   the `robin-backlog` skill's own conventions for this — don't duplicate the analysis into the
   backlog line, just point at it.
3. Tell her both are done and where: the design doc's path and the backlog line.

A build task later reads `discovery/<slug>.md` first instead of re-deriving the same decisions.

## Reference: the underlying method

`examples/nest-and-co-customer-care-interviews.md` is Maaike's own course material showing this
five-step process applied to a real business request. Useful context for the method itself, not
something this skill processes automatically.
