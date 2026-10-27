// Connects the widget to Robin's API (/api/chat). The conversation lives in the browser;
// every request sends the history, and the API returns Robin's answer plus the Langfuse trace ID.

const ERRORS = {
  passcode: "Please enter the course passcode in the course panel first.",
  name: "Please enter your first name or a nickname in the course panel first.",
  limit: "This chat has reached its message limit. Start a new conversation to continue.",
  generic: "Sorry, something went wrong on my side. Could you try again in a moment?",
};

const textOf = (message) =>
  (message?.content ?? [])
    .filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("\n");

export function createRobinAdapter(getSettings) {
  return {
    async run({ messages, abortSignal }) {
      const { name, passcode, model, effort, sessionId, guardrails } = getSettings();
      const history = messages.slice(0, -1).map((m) => ({ role: m.role, content: textOf(m) }));
      const message = textOf(messages.at(-1));

      let data;
      try {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message, history, name, passcode, model, effort, guardrails, session_id: sessionId }),
          signal: abortSignal,
        });
        data = await response.json().catch(() => ({}));
        if (!response.ok) {
          return { content: [{ type: "text", text: ERRORS[data.error] ?? ERRORS.generic }] };
        }
      } catch (error) {
        if (error.name === "AbortError") throw error;
        return { content: [{ type: "text", text: ERRORS.generic }] };
      }

      return {
        content: [{ type: "text", text: data.answer }],
        metadata: {
          custom: {
            traceId: data.trace_id,
            masked: data.masked === true, // the server says whether it removed a bank account number
          },
        },
      };
    },
  };
}

export const robinFeedbackAdapter = {
  submit({ message, type }) {
    const traceId = message?.metadata?.custom?.traceId;
    if (!traceId) return;
    fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trace_id: traceId, liked: type === "positive" }),
    }).catch(() => {});
  },
};
