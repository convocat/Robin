---
name: robin-conversation-design-review
description: "Review a conversation flow, system prompt, or transcript against conversation-design fundamentals — clarity (Grice's maxims), repair (can the user recover when misunderstood), one-question-at-a-time, tone and empathy — and return a structured critique with concrete rewrites for the worst issues, not a generic checklist pass. Triggers: '/robin-conversation-design-review', 'review this flow', 'review this system prompt', 'critique this conversation design'."
---

# robin-conversation-design-review — structured critique against conversation-design fundamentals

Given a system prompt, a flow description, or a transcript (pasted, or a file path), review it
against four lenses. Don't just confirm each lens is "fine" — find the two or three things that
would actually change the experience if fixed, and say nothing useful about the rest.

## The four lenses

1. **Clarity — Grice's maxims.** Does each turn say exactly as much as needed (not more, not
   less — quantity), say only what's believed true (quality), stay relevant to what the user
   asked (relation), and avoid ambiguity or needless complexity (manner)? A system prompt that
   buries the one instruction that matters under ten that don't fails manner, even if every
   sentence is individually true.
2. **Repair — can the user recover?** When the bot misunderstands, or the user is unclear, rude,
   or off-topic, what actually happens? Look for: a real fallback (not just "I don't understand"
   with no next step), whether the bot asks a clarifying question or guesses, and whether
   repeated failure escalates to something real (a human, a different path) or just loops the
   same deflection. A flow with no fallback path is a bigger finding than a slightly clunky one.
3. **One question at a time.** Does a single turn ask multiple things at once, or offer so many
   options the user has to re-read it twice? Count actual question marks and decision points per
   turn, don't eyeball it.
4. **Tone and empathy.** Does the register match the situation — calm with an angry customer,
   brief for a quick lookup, more careful for anything involving money or safety? Is the persona
   consistent, or does it slip between registers turn to turn? A tone that's technically polite
   but doesn't acknowledge frustration is a real finding, not a nitpick.

## What to look for specifically

- A system prompt that instructs the bot to "ask only one question at a time" is a good sign on
  lens 3 — but check the *examples* in the prompt, not just the instruction, since those are what
  the model actually imitates.
- A flow with a guardrail that blocks input but gives no next step is a repair failure even if
  the block itself is correct.
- Robin's own `prompts.py` in this repo is a reasonable in-repo reference for what a tight,
  single-purpose system prompt looks like — useful for comparison, not something to assume is
  perfect.

## Output format

1. **Strengths** — two or three things genuinely working, named specifically (quote the line or
   describe the turn), not a generic "overall solid."
2. **Issues, ranked by how much they'd actually hurt a real user** — each with the specific
   example from the input that shows it, and which of the four lenses it falls under.
3. **Rewrites for the top two or three issues** — concrete replacement text or flow changes, not
   just "consider improving this."

Keep the whole review proportional to the input: a three-line system prompt doesn't need a
twelve-point report.
