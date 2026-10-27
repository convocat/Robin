import { useMemo, useRef } from "react";
import {
  ActionBarPrimitive,
  AssistantModalPrimitive,
  AssistantRuntimeProvider,
  AuiIf,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useLocalRuntime,
} from "@assistant-ui/react";
import { mockRobinAdapter } from "./mockAdapter.js";
import { createRobinAdapter, robinFeedbackAdapter } from "./robinAdapter.js";

// Build with VITE_MOCK=1 for a preview with scripted answers; the normal build talks to /api/chat.
export const MOCK = import.meta.env.VITE_MOCK === "1";

const WELCOME = [
  {
    role: "assistant",
    content: [
      {
        type: "text",
        text: "Hi, I'm Robin from Nest & Co customer service. I can help with orders, returns and complaints. What can I do for you?",
      },
    ],
  },
];

const SUGGESTIONS = [
  "Can I still return a vase after 5 weeks?",
  "My made-to-measure curtains arrived damaged",
  "My delivery is late again. I want a voucher!",
  "Ik wil mijn bestelling retourneren",
];

function RobinAvatar({ size }) {
  return (
    <span className={`avatar avatar--${size}`} aria-hidden="true">
      <svg viewBox="0 0 32 32">
        <path d="M6 19c3 6 17 6 20 0" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
        <path d="M8 16c2.5 3.2 13.5 3.2 16 0" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
        <circle cx="16" cy="10.5" r="3.6" fill="currentColor" />
      </svg>
    </span>
  );
}

const Icon = {
  chat: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v8a2.5 2.5 0 0 1-2.5 2.5H10l-4.5 4v-4A1.5 1.5 0 0 1 4 14.5z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
    </svg>
  ),
  close: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M6 6l12 12M18 6 6 18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),
  refresh: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M19 12a7 7 0 1 1-2.05-4.95M19 4v4h-4" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  send: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 12h12M12 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  up: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M7 11v9H4v-9zM7 11l4-7c1.6 0 2.5 1.2 2.1 2.8L12.5 10H18a2 2 0 0 1 2 2.3l-1.1 6A2 2 0 0 1 16.9 20H7" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
    </svg>
  ),
  down: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M7 13V4H4v9zM7 13l4 7c1.6 0 2.5-1.2 2.1-2.8L12.5 14H18a2 2 0 0 0 2-2.3l-1.1-6A2 2 0 0 0 16.9 4H7" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
    </svg>
  ),
  copy: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="8" y="8" width="12" height="12" rx="2" fill="none" stroke="currentColor" strokeWidth="1.7" />
      <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" fill="none" stroke="currentColor" strokeWidth="1.7" />
    </svg>
  ),
  shield: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 3l7 3v5c0 4.5-3 8.2-7 10-4-1.8-7-5.5-7-10V6z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
    </svg>
  ),
};

function UserMessage() {
  return (
    <MessagePrimitive.Root className="msg msg--user">
      <div className="bubble bubble--user">
        <MessagePrimitive.Parts />
      </div>
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="msg msg--robin">
      <RobinAvatar size="sm" />
      <div className="msg__body">
        <AuiIf condition={(s) => s.message.metadata?.custom?.masked === true}>
          <p className="guard-note">
            {Icon.shield} Your bank account number was removed before your message was sent.
          </p>
        </AuiIf>
        <div className="bubble bubble--robin">
          <MessagePrimitive.Parts />
        </div>
        <AuiIf condition={(s) => s.message.index > 0}>
          <ActionBarPrimitive.Root hideWhenRunning className="actions">
            <ActionBarPrimitive.FeedbackPositive className="action" aria-label="Helpful">
              {Icon.up}
            </ActionBarPrimitive.FeedbackPositive>
            <ActionBarPrimitive.FeedbackNegative className="action" aria-label="Not helpful">
              {Icon.down}
            </ActionBarPrimitive.FeedbackNegative>
            <ActionBarPrimitive.Copy className="action" aria-label="Copy answer">
              {Icon.copy}
            </ActionBarPrimitive.Copy>
          </ActionBarPrimitive.Root>
        </AuiIf>
      </div>
    </MessagePrimitive.Root>
  );
}

function Typing() {
  return (
    <div className="msg msg--robin" aria-live="polite">
      <RobinAvatar size="sm" />
      <div className="bubble bubble--robin typing">
        <span className="sr-only">Robin is typing</span>
        <i />
        <i />
        <i />
      </div>
    </div>
  );
}

function RobinThread({ onNewConversation }) {
  return (
    <ThreadPrimitive.Root className="thread">
      <header className="thread__header">
        <RobinAvatar size="lg" />
        <div className="thread__title">
          <strong>Robin</strong>
          <span>
            <i className="online-dot" aria-hidden="true" /> Nest & Co customer service
          </span>
        </div>
        <button type="button" className="icon-btn" aria-label="New conversation" title="New conversation" onClick={onNewConversation}>
          {Icon.refresh}
        </button>
        <AssistantModalPrimitive.Trigger className="icon-btn" aria-label="Close chat">
          {Icon.close}
        </AssistantModalPrimitive.Trigger>
      </header>

      <ThreadPrimitive.Viewport className="thread__viewport">
        <p className="thread__day">Today</p>
        <ThreadPrimitive.Messages>
          {({ message }) => (message.role === "user" ? <UserMessage /> : <AssistantMessage />)}
        </ThreadPrimitive.Messages>

        <AuiIf condition={(s) => s.thread.isRunning && s.thread.messages.at(-1)?.role === "user"}>
          <Typing />
        </AuiIf>

        <AuiIf condition={(s) => s.thread.messages.length === 1}>
          <div className="chips" aria-label="Suggested questions">
            {SUGGESTIONS.map((prompt) => (
              <ThreadPrimitive.Suggestion key={prompt} prompt={prompt} send className="chip">
                {prompt}
              </ThreadPrimitive.Suggestion>
            ))}
          </div>
        </AuiIf>
      </ThreadPrimitive.Viewport>

      <ComposerPrimitive.Root className="composer">
        <ComposerPrimitive.Input className="composer__input" placeholder="Type your message…" rows={1} aria-label="Message to Robin" />
        <ComposerPrimitive.Send className="composer__send" aria-label="Send">
          {Icon.send}
        </ComposerPrimitive.Send>
      </ComposerPrimitive.Root>
      <p className="thread__note">
        Robin is an AI assistant and can make mistakes. Please don't share personal details.
        {MOCK && <span className="mock-tag">Preview · scripted answers</span>}
      </p>
    </ThreadPrimitive.Root>
  );
}

export default function RobinWidget({ open, onOpenChange, onNewConversation, settings }) {
  // Settings change while the chat is open; the adapter reads the latest values on every send.
  const settingsRef = useRef(settings);
  settingsRef.current = settings;

  const adapter = useMemo(() => (MOCK ? mockRobinAdapter : createRobinAdapter(() => settingsRef.current)), []);
  const runtime = useLocalRuntime(adapter, {
    initialMessages: WELCOME,
    adapters: { feedback: MOCK ? { submit: () => {} } : robinFeedbackAdapter },
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <AssistantModalPrimitive.Root open={open} onOpenChange={onOpenChange} unstable_openOnRunStart={false}>
        <AssistantModalPrimitive.Anchor className="launcher-anchor">
          <div className="launcher-teaser" aria-hidden="true">
            Questions about a return? <b>Ask Robin</b>
          </div>
          <AssistantModalPrimitive.Trigger className="launcher" aria-label="Chat with Robin">
            <span className="launcher__open">{Icon.chat}</span>
            <span className="launcher__close">{Icon.close}</span>
          </AssistantModalPrimitive.Trigger>
        </AssistantModalPrimitive.Anchor>
        <AssistantModalPrimitive.Content
          className="panel"
          side="top"
          align="end"
          sideOffset={14}
          onOpenAutoFocus={(event) => event.preventDefault()}
          onInteractOutside={(event) => event.preventDefault()}
        >
          <RobinThread onNewConversation={onNewConversation} />
        </AssistantModalPrimitive.Content>
      </AssistantModalPrimitive.Root>
    </AssistantRuntimeProvider>
  );
}
