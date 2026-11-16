import { useEffect, useMemo, useState } from "react";
import {
  AssistantRuntimeProvider,
  MessagePrimitive,
  ThreadPrimitive,
  useExternalStoreRuntime,
} from "@assistant-ui/react";

// Read-only thread view for one conversation from dashboard-data.json, rendered with the
// same @assistant-ui/react primitives as the Robin widget and the va-dashboard agent-frontend
// (ThreadPrimitive / MessagePrimitive). Layout follows the Waddinxveen dashboard: chat on the
// left, a "Bronnen" (sources) + "Beoordeling" (review) panel on the right for the latest answer.

function useConversation() {
  const [conv, setConv] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("id");
    if (!id) {
      setError("No conversation id given.");
      return;
    }
    fetch("/dashboard-data.json")
      .then((r) => r.json())
      .then((data) => {
        const found = data.convLog.find((c) => c.id === id);
        if (!found) setError("Conversation not found: " + id);
        else setConv(found);
      })
      .catch((e) => setError(String(e)));
  }, []);

  return { conv, error };
}

function scoreColor(similarity) {
  // Same threshold/coloring convention as the va-dashboard debug panel's RAG Scores.
  return similarity >= 0.5 ? "source-card--good" : "source-card--weak";
}

function UserMessage() {
  return (
    <MessagePrimitive.Root className="msg msg--user">
      <div className="bubble bubble--user">
        <MessagePrimitive.Content />
      </div>
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="msg msg--robin">
      <div className="avatar" aria-hidden="true">
        R
      </div>
      <div className="msg__body">
        <div className="bubble bubble--robin">
          <MessagePrimitive.Content />
        </div>
      </div>
    </MessagePrimitive.Root>
  );
}

function toThreadMessages(conv) {
  return conv.messages.map((m, idx) => ({
    role: m.role === "bot" ? "assistant" : "user",
    content: m.content,
    id: String(idx),
  }));
}

const CORRECTNESS_OPTIONS = [
  "No source, but gave an answer",
  "No source, correctly said don't know",
  "Source exists, no answer given",
];
const LANGUAGE_OPTIONS = ["Too long", "Not B1", "No empathy / wrong tone"];

function ReviewPanel({ lastBotMessage }) {
  const [allOk, setAllOk] = useState(false);
  const [correctness, setCorrectness] = useState(new Set());
  const [language, setLanguage] = useState(new Set());
  const [note, setNote] = useState("");

  function toggle(set, setSet, value) {
    const next = new Set(set);
    next.has(value) ? next.delete(value) : next.add(value);
    setSet(next);
    setAllOk(false);
  }

  const sources = lastBotMessage?.sources || [];

  return (
    <aside className="review-panel">
      <div className="review-panel__header">
        {lastBotMessage?.traceId && (
          <a href={lastBotMessage.langfuseUrl} target="_blank" rel="noreferrer" className="trace-link">
            Trace-ID: {lastBotMessage.traceId.slice(0, 16)}
          </a>
        )}
        {lastBotMessage?.feedback && <span className="thumb" title={lastBotMessage.feedback}>👍</span>}
      </div>

      <h3 className="review-panel__title">BRONNEN ({sources.length})</h3>
      {sources.length === 0 ? (
        <p className="review-panel__empty">Look-up (RAG) was off for this answer — no chunks were retrieved.</p>
      ) : (
        <ul className="source-list">
          {sources.map((s, i) => (
            <li key={i} className={"source-card " + scoreColor(s.similarity)}>
              <div className="source-card__head">
                <span className="source-card__title">{s.section}</span>
                <span className="source-card__score">{Math.round(s.similarity * 100)}%</span>
              </div>
              {s.snippet && <p className="source-card__snippet">{s.snippet}</p>}
            </li>
          ))}
        </ul>
      )}

      <h3 className="review-panel__title">BEOORDELING</h3>
      <button
        type="button"
        className={"ok-button" + (allOk ? " ok-button--active" : "")}
        onClick={() => { setAllOk(!allOk); setCorrectness(new Set()); setLanguage(new Set()); }}
      >
        All OK
      </button>

      <div className="review-group">
        <h4>Correctness</h4>
        <div className="toggle-row">
          {CORRECTNESS_OPTIONS.map((opt) => (
            <button
              key={opt}
              type="button"
              className={"toggle-chip" + (correctness.has(opt) ? " toggle-chip--active" : "")}
              onClick={() => toggle(correctness, setCorrectness, opt)}
            >
              {opt}
            </button>
          ))}
        </div>
      </div>

      <div className="review-group">
        <h4>Language use</h4>
        <div className="toggle-row">
          {LANGUAGE_OPTIONS.map((opt) => (
            <button
              key={opt}
              type="button"
              className={"toggle-chip" + (language.has(opt) ? " toggle-chip--active" : "")}
              onClick={() => toggle(language, setLanguage, opt)}
            >
              {opt}
            </button>
          ))}
        </div>
      </div>

      <div className="review-group">
        <h4>Notes</h4>
        <textarea
          className="review-note"
          placeholder="Optional: explain what stands out, for the admin to review…"
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
        <p className="review-note__caveat">Not saved anywhere yet — see the trace-annotation-dashboard project for that.</p>
      </div>
    </aside>
  );
}

export default function ThreadView() {
  const { conv, error } = useConversation();
  const messages = useMemo(() => (conv ? toThreadMessages(conv) : []), [conv]);
  const lastBotMessage = useMemo(
    () => (conv ? [...conv.messages].reverse().find((m) => m.role === "bot") : null),
    [conv],
  );

  const runtime = useExternalStoreRuntime({
    messages,
    isDisabled: true,
    convertMessage: (m) => m,
    onNew: async () => {},
  });

  if (error) return <div className="state state--error">{error}</div>;
  if (!conv) return <div className="state">Loading…</div>;

  return (
    <div className="layout">
      <AssistantRuntimeProvider runtime={runtime}>
        <ThreadPrimitive.Root className="thread">
          <ThreadPrimitive.Viewport className="thread__viewport">
            <ThreadPrimitive.Messages components={{ UserMessage, AssistantMessage }} />
          </ThreadPrimitive.Viewport>
        </ThreadPrimitive.Root>
      </AssistantRuntimeProvider>
      <ReviewPanel lastBotMessage={lastBotMessage} />
    </div>
  );
}
