"""Builds dashboard-data.json for the dashboard-kit (originally from Mai Montferland),
adapted for Robin: pulls real course chats from Langfuse (environment "course",
"Robin - chat turn" traces), groups them into conversations by sessionId, and
classifies topics for Nest & Co instead of a municipality.

Run from the Robin project root with its .env loaded:
    python dashboard-kit/robin_adapter.py
"""
from __future__ import annotations

import base64
import collections
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

PUB = os.environ["LANGFUSE_PUBLIC_KEY"]
SEC = os.environ["LANGFUSE_SECRET_KEY"]
BASE = os.environ["LANGFUSE_BASE_URL"]
AUTH = base64.b64encode(f"{PUB}:{SEC}".encode()).decode()
FROM_TS = "2020-01-01T00:00:00Z"

TOPIC_KEYWORDS = {
    "Returns": ["return", "refund", "retour", "money back"],
    "Shipping & delivery": ["shipping", "deliver", "ship ", "delivery", "parcel", "courier"],
    "Order & payment": ["order", "payment", "pay", "invoice", "ideal", "klarna", "paypal", "voucher", "gift card"],
    "Damaged or faulty": ["damaged", "broken", "faulty", "defect"],
    "Bank account / IBAN": ["iban", "bank account", "rekeningnummer"],
    "Prompt injection attempt": ["ignore", "pretend", "dan", "jailbreak", "debug mode", "system prompt",
                                 "instructions", "pirate"],
    "Wants a human": ["human", "real person", "colleague", "human agent"],
    "Product care & styling": ["care", "clean", "vacuum", "wood", "sofa", "rug", "styling"],
    "About Robin itself": ["are you", "chatbot", "robin", "ai assistant"],
}


SECTION_HIT = re.compile(r"([^,(]+?)\s*\(([\d.]+)\)")


def load_handbook_snippets() -> dict[str, str]:
    """Section heading -> first ~160 characters of its body, for the Bronnen panel.

    Mirrors how lookup.split_into_chunks cuts content/handbook.md: one chunk per '## ' heading.
    """
    text = (ROOT / "content" / "handbook.md").read_text(encoding="utf-8")
    snippets = {}
    for heading, body in re.findall(r"^##[ \t]+([^\n]+)\n([\s\S]*?)(?=\n##[ \t]|\Z)", text, re.M):
        clean = re.sub(r"\s+", " ", body).strip()
        snippets[heading.strip()] = (clean[:160] + "…") if len(clean) > 160 else clean
    return snippets


HANDBOOK_SNIPPETS = load_handbook_snippets()


def parse_sections_found(text: str | None) -> list[dict]:
    """'Product care (0.327), Returns (0.3)' -> [{'section': ..., 'similarity': 0.327, 'snippet': ...}, ...].

    robin.py writes `sections_found` into trace metadata whenever look-up (RAG) ran.
    """
    if not text:
        return []
    return [
        {"section": m.group(1).strip(), "similarity": float(m.group(2)),
         "snippet": HANDBOOK_SNIPPETS.get(m.group(1).strip(), "")}
        for m in SECTION_HIT.finditer(text)
    ]


def classify_topic(user_text: str) -> str:
    text = user_text.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return topic
    return "Other"


def _get(path: str, **params) -> dict:
    qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    url = f"{BASE}{path}?{qs}"
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {AUTH}"})
    for attempt in range(8):
        try:
            with urllib.request.urlopen(req) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 * (attempt + 1))
                continue
            if e.code in (404, 410):
                # Langfuse marked /api/public/traces and /api/public/scores deprecated,
                # sunset 2026-11-16, in favour of /api/public/v2/observations and
                # /api/public/v3/scores. If this path is now gone, that's why.
                raise RuntimeError(
                    f"{path} returned {e.code} - Langfuse may have removed this deprecated "
                    "endpoint. It needs migrating to the v2/observations or v3/scores API."
                ) from e
            raise
    raise RuntimeError(f"gave up on {url}")


def fetch_all_traces() -> list[dict]:
    traces, page = [], 1
    while True:
        d = _get("/api/public/traces", limit=100, page=page, fromTimestamp=FROM_TS,
                  name="Robin – chat turn", environment="course")
        traces.extend(d["data"])
        if page >= d["meta"]["totalPages"]:
            break
        page += 1
        time.sleep(0.3)
    return traces


def fetch_feedback_scores() -> dict[str, list[dict]]:
    scores_by_trace: dict[str, list[dict]] = collections.defaultdict(list)
    page = 1
    while True:
        d = _get("/api/public/scores", limit=100, page=page, fromTimestamp=FROM_TS,
                  name="user feedback", environment="course")
        for s in d["data"]:
            scores_by_trace[s["traceId"]].append(s)
        if page >= d["meta"]["totalPages"]:
            break
        page += 1
        time.sleep(0.3)
    return scores_by_trace


def is_tester(user_id: str | None) -> bool:
    return bool(user_id) and "gr-on" in user_id.lower().replace(" ", "-").replace("_", "-")


def build_conv_log(traces: list[dict], scores_by_trace: dict[str, list[dict]]) -> list[dict]:
    by_session: dict[str, list[dict]] = collections.defaultdict(list)
    for t in traces:
        key = t.get("sessionId") or "no-session"
        if key == "no-session":
            key = f"single-{t['id']}"  # each standalone turn is its own conversation
        by_session[key].append(t)

    conv_log = []
    for session_id, turns in by_session.items():
        turns.sort(key=lambda t: t["timestamp"])
        messages = []
        feedback_texts: list[str] = []
        positive = negative = False
        for t in turns:
            raw_input, raw_output = t.get("input"), t.get("output")
            user_text = raw_input if isinstance(raw_input, str) else ("" if raw_input is None else json.dumps(raw_input))
            bot_text = raw_output if isinstance(raw_output, str) else ("" if raw_output is None else json.dumps(raw_output))
            messages.append({"role": "user", "content": user_text, "time": t["timestamp"], "feedback": None})
            turn_scores = scores_by_trace.get(t["id"], [])
            comment = next((s.get("comment") for s in turn_scores if s.get("comment")), None)
            for s in turn_scores:
                if s.get("value") == 1:
                    positive = True
                elif s.get("value") == 0:
                    negative = True
                if s.get("comment"):
                    feedback_texts.append(s["comment"])
            sources = parse_sections_found((t.get("metadata") or {}).get("sections_found"))
            messages.append({"role": "bot", "content": bot_text or "", "time": t["timestamp"], "feedback": comment,
                             "sources": sources, "traceId": t["id"], "langfuseUrl": BASE + t.get("htmlPath", "")})

        user_texts = " ".join(m["content"] for m in messages if m["role"] == "user")
        first_user = next((m for m in messages if m["role"] == "user"), None)
        last_turn = turns[-1]
        outcomes = [((t.get("metadata") or {}).get("outcome")) for t in turns]

        conv_log.append({
            "id": session_id,
            "time": turns[0]["timestamp"],
            "source": "web widget",
            "topic": classify_topic(user_texts),
            "turns": len(turns),
            "hasError": any(not str(t.get("output") or "").strip() for t in turns),
            "isTester": is_tester(last_turn.get("userId")),
            "feedbacks": feedback_texts,
            "thumbs": {"positive": positive, "negative": negative} if (positive or negative) else None,
            "preview": (first_user["content"][:120] if first_user else ""),
            "messages": messages,
            # Extra fields beyond the base contract, for Robin's own course context.
            "userId": last_turn.get("userId"),
            "models": sorted({(t.get("metadata") or {}).get("robin_model") for t in turns if t.get("metadata")}),
            "guardrailsOff": sorted({(t.get("metadata") or {}).get("guardrails_switched_off") for t in turns
                                     if t.get("metadata")}),
            "lookUp": sorted({(t.get("metadata") or {}).get("look_up") for t in turns if t.get("metadata")}),
            "outcomes": outcomes,
        })

    conv_log.sort(key=lambda c: c["time"], reverse=True)
    return conv_log


def main() -> None:
    print("Fetching traces from Langfuse...")
    traces = fetch_all_traces()
    print(f"Found {len(traces)} chat-turn traces.")

    print("Fetching 'user feedback' scores...")
    scores_by_trace = fetch_feedback_scores()
    print(f"Found feedback on {len(scores_by_trace)} traces.")

    print("Building conversation log...")
    conv_log = build_conv_log(traces, scores_by_trace)
    print(f"Built {len(conv_log)} conversations.")

    out_path = Path(__file__).with_name("dashboard-data.json")
    out_path.write_text(json.dumps({"metrics": {}, "convLog": conv_log}, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
