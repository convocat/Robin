"""Robin's brain: one customer message in, one answer out, with guardrails and a readable Langfuse trace.

Every customer message becomes ONE trace in Langfuse, with these steps inside it:

    Robin – chat turn                                    (the whole turn: customer message in, answer out)
    ├── 1. Input guardrail – bank account numbers       (no LLM: a pattern check)
    ├── 2. Input guardrail – prompt injection            (small model)
    │   └── Injection check (small model)
    ├── 3. Robin writes the answer                      (the LLM call with the system prompt)
    ├── 4. Output guardrail – facts check                (small model)
    │   └── Facts check (small model)
    └── 5. and 6.: only if the facts check blocked the first answer (a rewrite, then a second check)

All turns of one chat share a session ID, so the Sessions view in Langfuse shows the whole conversation.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field

from langfuse import get_client, propagate_attributes
from langfuse.api import NotFoundError

import prompts

APP_VERSION = "robin-v1"

# Model names come from environment variables, so you can change them without editing code.
ROBIN_MODELS = {
    "GPT-6 Sol": os.getenv("ROBIN_MODEL", "gpt-6-sol"),
    "GPT-4.1 mini": os.getenv("COMPARE_MODEL", "gpt-4.1-mini"),
}
REASONING_MODELS = {os.getenv("ROBIN_MODEL", "gpt-6-sol")}  # models that accept reasoning_effort
GUARDRAIL_MODEL = os.getenv("GUARDRAIL_MODEL", "gpt-6-luna")
GUARDRAIL_EFFORT = os.getenv("GUARDRAIL_EFFORT", "low")


# ---------------------------------------------------------------------------
# Guardrail 1: bank account numbers (deterministic, no LLM)
# ---------------------------------------------------------------------------

# Two letters, two check digits, then blocks of up to four letters/digits (with or without spaces).
IBAN_PATTERN = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){2,7}(?:\s?[A-Z0-9]{1,4})?\b", re.IGNORECASE)


def _is_valid_iban(candidate: str) -> bool:
    """Check the IBAN checksum (mod 97), so ordinary words and order numbers aren't masked."""
    iban = re.sub(r"\s", "", candidate).upper()
    if not 15 <= len(iban) <= 34:
        return False
    rearranged = iban[4:] + iban[:4]
    digits = "".join(str(int(ch, 36)) for ch in rearranged)
    return int(digits) % 97 == 1


def mask_bank_accounts(text: str) -> tuple[str, int]:
    """Replace valid IBANs with a placeholder. Returns the masked text and how many were found."""
    found = 0

    def _replace(match: re.Match) -> str:
        nonlocal found
        if _is_valid_iban(match.group(0)):
            found += 1
            return prompts.MASK_TEXT
        return match.group(0)

    return IBAN_PATTERN.sub(_replace, text), found


# ---------------------------------------------------------------------------
# Prompts from Langfuse (Prompt Management), with the texts in prompts.py as a fallback
# ---------------------------------------------------------------------------

log = logging.getLogger("robin")
_prompts_seeded = False


def seed_prompts() -> None:
    """The first time Robin runs, copy any prompt that's missing in Langfuse from prompts.py.

    Existing prompts are never overwritten, so edits you make in Langfuse are kept.
    """
    global _prompts_seeded
    if _prompts_seeded:
        return
    _prompts_seeded = True
    if not os.getenv("LANGFUSE_PUBLIC_KEY"):
        return
    langfuse = get_client()
    for name, text in prompts.LANGFUSE_PROMPTS.items():
        try:
            langfuse.get_prompt(name, label="production", cache_ttl_seconds=0, max_retries=0, fetch_timeout_seconds=5)
        except NotFoundError:
            try:
                langfuse.create_prompt(name=name, prompt=text, labels=["production"], tags=["robin"],
                                       commit_message="Robin's starting version, from prompts.py")
            except Exception:
                log.exception("could not create prompt %s in Langfuse", name)
        except Exception:
            log.exception("could not check prompt %s in Langfuse", name)


def _prompt(name: str):
    """Get the 'production' version of a prompt from Langfuse, or the local text if that fails."""
    try:
        return get_client().get_prompt(name, label="production", fallback=prompts.LANGFUSE_PROMPTS[name],
                                       cache_ttl_seconds=60, max_retries=1, fetch_timeout_seconds=5)
    except Exception:
        log.exception("could not load prompt %s; using the local text", name)
        return None


def _text(name: str, **values: str) -> tuple[str, object]:
    """Return (filled-in text, prompt to link in the trace). Fallback texts are not linked."""
    prompt = _prompt(name)
    if prompt is None:
        return prompts.fill(prompts.LANGFUSE_PROMPTS[name], **values), None
    return prompt.compile(**values), (None if getattr(prompt, "is_fallback", False) else prompt)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_json(text: str) -> dict:
    """Read the first JSON object in a model answer. Raises ValueError if there is none."""
    match = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not match:
        raise ValueError("no JSON found in the guardrail answer")
    return json.loads(match.group(0))


# Plain-language labels for every step, shown as metadata in Langfuse. Step names never contain
# the model name, so the graph and saved filters stay the same when you switch models.
STEPS = {
    "bank": {"layer": "input guardrail", "uses_llm": "no: a pattern check in code",
             "what_it_does": "Removes bank account numbers before the message goes anywhere.",
             "if_it_fails": "not applicable: it's a rule, not a model"},
    "injection": {"layer": "input guardrail", "uses_llm": "yes: the small model",
                  "what_it_does": "Checks whether the customer tries to make Robin ignore its instructions.",
                  "if_it_fails": "fail open: the message goes through to Robin"},
    "answer": {"layer": "LLM call", "uses_llm": "yes: Robin's model",
               "what_it_does": "Robin writes an answer, using the system prompt and the conversation so far."},
    "retry": {"layer": "LLM call", "uses_llm": "yes: Robin's model",
              "what_it_does": "Robin rewrites the answer, because the facts check found unsupported statements."},
    "facts": {"layer": "output guardrail", "uses_llm": "yes: the small model",
              "what_it_does": "Checks that every fact in Robin's answer is in the return policy.",
              "if_it_fails": "fail closed: the answer is not sent"},
}


def _chat(client, *, name: str, model: str, messages: list[dict], effort: str | None,
          metadata: dict | None = None, prompt=None) -> str:
    """One LLM call, recorded in Langfuse as a generation named `name`.

    We record it ourselves instead of using the automatic OpenAI integration, so the trace only shows
    the settings we actually send (the integration also lists default values such as temperature,
    which would confuse newcomers: GPT-6 doesn't use temperature when reasoning is on).
    """
    kwargs = {"model": model, "messages": messages}
    if effort:
        kwargs["reasoning_effort"] = effort
    with get_client().start_as_current_observation(
        as_type="generation", name=name, model=model, input=messages, metadata=metadata, prompt=prompt,
        model_parameters={"reasoning_effort": effort} if effort else {},
    ) as generation:
        response = client.chat.completions.create(**kwargs)
        text = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        generation.update(
            output=text,
            usage_details={"input_tokens": usage.prompt_tokens, "output_tokens": usage.completion_tokens}
            if usage else None,
        )
    return text


def _clean_history(history: list[dict]) -> list[dict]:
    """Keep only plain user/assistant text messages from the chat history."""
    clean = []
    for message in history or []:
        role, content = message.get("role"), message.get("content")
        if role in ("user", "assistant") and isinstance(content, str):
            clean.append({"role": role, "content": content})
    return clean


@dataclass
class TurnResult:
    answer: str                    # what Robin says to the customer
    customer_message: str          # the customer's message as stored (bank account numbers masked)
    trace_id: str | None = None    # to attach thumbs up/down feedback later
    outcome: str = "answered"
    details: dict = field(default_factory=dict)
    summary: dict = field(default_factory=dict)  # shown as metadata on the whole turn


# ---------------------------------------------------------------------------
# One chat turn
# ---------------------------------------------------------------------------

def handle_turn(
    message: str,
    history: list[dict],
    *,
    client,
    robin_model_label: str = "GPT-6 Sol",
    reasoning_effort: str = "medium",
    participant: str = "anonymous",
    session_id: str = "no-session",
) -> TurnResult:
    seed_prompts()
    langfuse = get_client()
    robin_model = ROBIN_MODELS.get(robin_model_label, ROBIN_MODELS["GPT-6 Sol"])
    policy, _ = _text("robin/return-policy")
    system_prompt, system_link = _text("robin/system-prompt", return_policy=policy)
    injection_prompt, injection_link = _text("robin/injection-check")
    facts_prompt, facts_link = _text("robin/facts-check", return_policy=policy)
    checks = {"facts": (facts_prompt, facts_link)}
    effort = reasoning_effort if robin_model in REASONING_MODELS else None

    # Guardrail 1 runs BEFORE anything is traced, so bank account numbers never reach Langfuse or OpenAI.
    masked_message, bank_accounts_found = mask_bank_accounts(message)

    with propagate_attributes(
        trace_name="Robin – chat turn",
        session_id=session_id,
        user_id=participant or "anonymous",
        tags=["robin", f"model: {robin_model}"],
        version=APP_VERSION,
        metadata={
            "robin_model": robin_model,
            "reasoning_effort": effort or "not used",
            "guardrail_model": GUARDRAIL_MODEL,
        },
    ):
        with langfuse.start_as_current_observation(
            as_type="agent", name="Robin – chat turn", input=masked_message
        ) as turn:
            result = TurnResult(answer="", customer_message=masked_message,
                                trace_id=langfuse.get_current_trace_id())
            language = None

            # --- 1. Input guardrail: bank account numbers --------------------------------
            with langfuse.start_as_current_observation(
                as_type="guardrail", name="1. Input guardrail – bank account numbers",
                input=masked_message, metadata=STEPS["bank"],
            ) as guard:
                bank_result = "MASKED" if bank_accounts_found else "PASS"
                explanation = (f"Removed {bank_accounts_found} bank account number(s) before the message was sent anywhere."
                               if bank_accounts_found else "No bank account numbers found.")
                guard.update(output={"result": bank_result, "explanation": explanation},
                             metadata={"result": bank_result})
                if bank_accounts_found:
                    guard.update(level="WARNING", status_message=explanation)
            result.summary["step_1_bank_account_check"] = bank_result
            turn.score_trace(name="guardrail: bank account", value=bank_result, data_type="CATEGORICAL")

            # --- 2. Input guardrail: prompt injection --------------------------------------
            with langfuse.start_as_current_observation(
                as_type="guardrail", name="2. Input guardrail – prompt injection",
                input=masked_message, metadata=STEPS["injection"],
            ) as guard:
                try:
                    raw = _chat(client, name="Injection check (small model)", model=GUARDRAIL_MODEL,
                                effort=GUARDRAIL_EFFORT, metadata={"part_of": "2. Input guardrail – prompt injection"},
                                prompt=injection_link,
                                messages=[{"role": "system", "content": injection_prompt},
                                          {"role": "user", "content": masked_message}])
                    verdict = _parse_json(raw)
                    injection_result = "BLOCK" if str(verdict.get("result")).upper() == "BLOCK" else "PASS"
                    language = verdict.get("language")
                    explanation = verdict.get("reason", "")
                except Exception as error:  # fail open: an error in this check doesn't stop the customer
                    injection_result, explanation = "ERROR", f"The check failed, so the message was let through: {error}"
                guard.update(output={"result": injection_result, "explanation": explanation},
                             metadata={"result": injection_result})
                if injection_result != "PASS":
                    guard.update(level="WARNING", status_message=explanation)
            result.summary["step_2_injection_check"] = injection_result
            turn.score_trace(name="guardrail: prompt injection", value=injection_result, data_type="CATEGORICAL",
                             comment=explanation)

            if injection_result == "BLOCK":
                result.answer = prompts.fallback("injection_blocked", language)
                result.outcome = "blocked by input guardrail"
                return _finish(turn, result, facts_result="SKIPPED")

            # --- 3. Robin's answer -------------------------------------------------------
            messages = [{"role": "system", "content": system_prompt},
                        *_clean_history(history),
                        {"role": "user", "content": masked_message}]
            try:
                draft = _chat(client, name="3. Robin writes the answer", model=robin_model,
                              effort=effort, messages=messages, metadata=STEPS["answer"], prompt=system_link)
            except Exception as error:
                turn.update(level="ERROR", status_message=str(error))
                result.answer = prompts.fallback("error", language)
                result.outcome = "error"
                return _finish(turn, result, facts_result="SKIPPED")

            # --- 4. Output guardrail: facts check (with one retry) ------------------------
            facts_result, unsupported, language = _facts_check(client, langfuse, draft, checks["facts"],
                                                               name="4. Output guardrail – facts check")
            result.summary["rewrite_needed"] = "no"
            if facts_result == "BLOCK":
                result.summary["rewrite_needed"] = "yes"
                retry_note, _ = _text("robin/retry-note",
                                      unsupported="\n".join(f"- {item}" for item in unsupported) or "- (not specified)")
                retry_messages = messages + [
                    {"role": "assistant", "content": draft},
                    {"role": "system", "content": retry_note},
                ]
                try:
                    draft = _chat(client, name="5. Robin rewrites the answer", model=robin_model,
                                  effort=effort, messages=retry_messages, metadata=STEPS["retry"], prompt=system_link)
                    facts_result, unsupported, language = _facts_check(
                        client, langfuse, draft, checks["facts"], name="6. Output guardrail – facts check on the rewrite")
                except Exception as error:
                    turn.update(level="ERROR", status_message=str(error))
                    facts_result = "ERROR"

            if facts_result == "PASS":
                result.answer = draft
                result.outcome = "answered"
            else:  # BLOCK twice, or ERROR: fail closed with the fixed message
                result.answer = prompts.fallback("facts_blocked", language)
                result.outcome = "fallback after output guardrail"
            result.details["unsupported"] = unsupported
            return _finish(turn, result, facts_result=facts_result)


def _facts_check(client, langfuse, draft: str, facts: tuple, name: str) -> tuple[str, list, str | None]:
    """Output guardrail. Returns (PASS/BLOCK/ERROR, unsupported statements, language)."""
    with langfuse.start_as_current_observation(
        as_type="guardrail", name=name, input=draft, metadata=STEPS["facts"],
    ) as guard:
        try:
            raw = _chat(client, name="Facts check (small model)", model=GUARDRAIL_MODEL,
                        effort=GUARDRAIL_EFFORT, metadata={"part_of": name}, prompt=facts[1],
                        messages=[{"role": "system", "content": facts[0]},
                                  {"role": "user", "content": f"Draft answer:\n{draft}"}])
            verdict = _parse_json(raw)
            result = "BLOCK" if str(verdict.get("result")).upper() == "BLOCK" else "PASS"
            unsupported = [str(item) for item in verdict.get("unsupported") or []]
            language = verdict.get("language")
            explanation = ("All facts are in the return policy." if result == "PASS"
                           else "Not in the return policy: " + "; ".join(unsupported))
        except Exception as error:  # fail closed: if we can't check the answer, we don't send it
            result, unsupported, language = "ERROR", [], None
            explanation = f"The check failed, so the answer was not sent: {error}"
        guard.update(output={"result": result, "unsupported": unsupported, "explanation": explanation},
                     metadata={"result": result})
        if result != "PASS":
            guard.update(level="WARNING", status_message=explanation)
    return result, unsupported, language


OUTCOME_NOTES = {
    "answered": "Robin's answer passed every guardrail and was sent.",
    "blocked by input guardrail": "The message tried to manipulate Robin, so Robin never saw it. A fixed answer was sent.",
    "fallback after output guardrail": "Robin's answer contained facts that aren't in the policy, twice. A fixed, honest answer was sent instead.",
    "error": "Something went wrong while calling the model. A fixed apology was sent.",
}


def _finish(turn, result: TurnResult, facts_result: str) -> TurnResult:
    """Write the final answer, the outcome and a summary of every step onto the turn."""
    result.summary["step_4_facts_check"] = facts_result
    result.summary.setdefault("rewrite_needed", "no")
    summary = {"outcome": result.outcome, "what_happened": OUTCOME_NOTES[result.outcome], **result.summary}
    turn.score_trace(name="guardrail: facts check", value=facts_result, data_type="CATEGORICAL")
    turn.score_trace(name="outcome", value=result.outcome, data_type="CATEGORICAL")
    turn.update(output=result.answer, metadata=summary)
    if result.outcome == "error":
        turn.update(level="ERROR")
    elif result.outcome != "answered":
        turn.update(level="WARNING", status_message=OUTCOME_NOTES[result.outcome])
    return result


def record_feedback(trace_id: str, liked: bool) -> None:
    """Thumbs up/down from the chat window, stored as a score on the trace."""
    if trace_id:
        get_client().create_score(name="user feedback", value=1 if liked else 0, trace_id=trace_id,
                                  data_type="BOOLEAN", comment="thumbs up" if liked else "thumbs down")
