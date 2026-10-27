"""Robin's API for Vercel: the chat widget (public/index.html) sends each message here.

Vercel runs this file as a function: every request starts, runs and stops. That's why the
conversation lives in the browser, and why every request ends with flushing the traces to Langfuse.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # for local runs; on Vercel, keys come from the project's environment variables
os.environ.setdefault("LANGFUSE_TRACING_ENVIRONMENT", "course")

from flask import Flask, jsonify, request, send_file  # noqa: E402
from langfuse import get_client  # noqa: E402
from openai import OpenAI  # noqa: E402

import robin  # noqa: E402

app = Flask(__name__)
log = logging.getLogger("robin")

client = OpenAI()
COURSE_PASSCODE = os.getenv("COURSE_PASSCODE", "")
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES_PER_CHAT", "40"))
MAX_MESSAGE_LENGTH = 2000
MAX_HISTORY_ITEMS = 2 * MAX_MESSAGES + 1
INDEX_HTML = Path(__file__).parent / "public" / "index.html"


def _error(code: str, status: int):
    return jsonify({"error": code}), status


@app.post("/api/chat")
def chat():
    try:
        data = request.get_json(silent=True) or {}
        message = str(data.get("message") or "").strip()
        name = str(data.get("name") or "").strip()[:60]
        history = data.get("history") or []

        if COURSE_PASSCODE and data.get("passcode") != COURSE_PASSCODE:
            return _error("passcode", 403)
        if not name:
            return _error("name", 400)
        if not message or len(message) > MAX_MESSAGE_LENGTH:
            return _error("message", 400)
        if not isinstance(history, list) or len(history) > MAX_HISTORY_ITEMS:
            return _error("limit", 400)
        if sum(1 for item in history if isinstance(item, dict) and item.get("role") == "user") >= MAX_MESSAGES:
            return _error("limit", 400)

        result = robin.handle_turn(
            message,
            [item for item in history if isinstance(item, dict)],
            client=client,
            robin_model_label=str(data.get("model") or "GPT-6 Sol"),
            reasoning_effort=str(data.get("effort") or "medium"),
            participant=name,
            session_id=str(data.get("session_id") or "no-session")[:100],
            guardrails=data.get("guardrails"),  # e.g. {"facts": false}; anything missing stays on
        )
        return jsonify({
            "answer": result.answer,
            "customer_message": result.customer_message,
            "trace_id": result.trace_id,
            "outcome": result.outcome,
        })
    except Exception:
        log.exception("chat request failed")
        return _error("generic", 500)
    finally:
        get_client().flush()  # send the trace before Vercel stops the function


@app.post("/api/feedback")
def feedback():
    try:
        data = request.get_json(silent=True) or {}
        trace_id = str(data.get("trace_id") or "")
        if trace_id:
            robin.record_feedback(trace_id, bool(data.get("liked")))
        return jsonify({"ok": True})
    except Exception:
        log.exception("feedback request failed")
        return _error("generic", 500)
    finally:
        get_client().flush()


@app.get("/")
def index():
    # On Vercel, the CDN normally serves public/index.html itself. This route covers local runs.
    if INDEX_HTML.exists():
        return send_file(INDEX_HTML)
    return "Robin's API is running. The chat page is in public/index.html.", 200


if __name__ == "__main__":
    # On Render (and locally), `python app.py` starts a production web server.
    # On Vercel this block doesn't run: Vercel loads `app` directly.
    from waitress import serve

    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", "3000")), threads=8)
