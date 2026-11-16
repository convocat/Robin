/**
 * Mai Montferland Dashboard — Data Contract
 * ==========================================
 *
 * Dit bestand beschrijft het dataformaat dat dashboard.html verwacht.
 * De dashboard laadt `dashboard-data.json` en verwacht exact deze structuur.
 *
 * Om het dashboard te koppelen aan een andere databron (bijv. traces),
 * hoef je alleen een script te schrijven dat dit formaat produceert.
 *
 *
 * SHADCN/UI COMPONENT MAPPING
 * ============================
 * De CSS in dashboard.html volgt shadcn/ui design tokens.
 * Bij migratie naar React + shadcn/ui:
 *
 *   .kpi-card            → shadcn Card
 *   .tab / .tab-bar      → shadcn Tabs
 *   .section-nav         → shadcn NavigationMenu (vertical)
 *   .preset-btn          → shadcn ToggleGroup
 *   .log-table           → shadcn DataTable (TanStack Table)
 *   .log-controls input  → shadcn Input
 *   .log-controls select → shadcn Select
 *   .badge               → shadcn Badge
 *   .modal-overlay       → shadcn Dialog / Sheet
 *   .info-box            → shadcn Alert
 *   .pagination          → shadcn Pagination
 *   input[type=date]     → shadcn DatePickerWithRange
 *   input[type=checkbox] → shadcn Checkbox
 *   .chart-card          → shadcn Card + Recharts
 *   .topic-table         → shadcn Table
 *   .feedback-table      → shadcn Table
 */

// ============================================================
// TOP-LEVEL STRUCTURE
// ============================================================
// dashboard-data.json = { metrics, convLog }
//
// `metrics` — pre-computed global stats (optional, used for initial load)
// `convLog` — array of conversation objects (the real data)

/**
 * @typedef {Object} ConvLogEntry
 * @property {string}  id        — Unique conversation ID (UUID)
 * @property {string}  time      — ISO 8601 timestamp of first message (e.g. "2024-10-09T13:58:34.186Z")
 * @property {string}  source    — Channel (e.g. "API/Embed", "web", "whatsapp")
 * @property {string}  topic     — Auto-classified topic (e.g. "Paspoort / ID", "Overig")
 * @property {number}  turns     — Number of user messages in this conversation
 * @property {boolean} hasError  — True if any bot response was empty/broken
 * @property {boolean} isTester  — True if this is an internal test conversation
 * @property {string[]} feedbacks — Array of text feedback strings (can be empty)
 * @property {?Thumbs} thumbs    — Thumbs rating from Flowise (null if no rating)
 * @property {string}  preview   — First 120 chars of first user message
 * @property {Message[]} messages — Full conversation messages
 */

/**
 * @typedef {Object} Thumbs
 * @property {boolean} positive — User gave thumbs up
 * @property {boolean} negative — User gave thumbs down
 * Note: both can be true if user rated multiple messages differently
 */

/**
 * @typedef {Object} Message
 * @property {string}  role     — "user" or "bot"
 * @property {string}  content  — Message text
 * @property {string}  time     — ISO 8601 timestamp
 * @property {?string} feedback — Text feedback on this message (null if none)
 */

// ============================================================
// EXAMPLE ENTRY
// ============================================================
const exampleConvLogEntry = {
  id: "32a1994c-e2b6-4e55-ab71-49f297c704bd",
  time: "2024-10-09T13:58:34.186Z",
  source: "API/Embed",
  topic: "Openbare ruimte",
  turns: 2,
  hasError: false,
  isTester: false,
  feedbacks: ["Goed antwoord!"],
  thumbs: { positive: true, negative: false },
  preview: "Ik zag een losse stoeptegel. Waar kan ik dat melden?",
  messages: [
    { role: "user", content: "Ik zag een losse stoeptegel. Waar kan ik dat melden?", time: "2024-10-09T13:58:34.186Z", feedback: null },
    { role: "bot", content: "U kunt een melding maken via...", time: "2024-10-09T13:58:36.653Z", feedback: "Goed antwoord!" },
    { role: "user", content: "Bedankt!", time: "2024-10-09T13:59:01.000Z", feedback: null },
  ]
};

// ============================================================
// HOW TO ADAPT FOR TRACES
// ============================================================
//
// When migrating from flat JSON logging to graph-based traces:
//
// 1. Each trace = 1 conversation. Map trace_id → id.
// 2. Flatten trace spans into messages[] array:
//    - User input spans → role: "user"
//    - LLM output spans → role: "bot"
//    - Keep original timestamps
// 3. Extract feedback from your feedback system → thumbs + feedbacks
// 4. Run topic classification on user messages → topic
// 5. Detect errors from trace status/error spans → hasError
// 6. Detect testers from metadata/tags → isTester
//
// Optional enrichments from traces (for Tech dashboard):
// - Add `latencyMs` to each message (from span duration)
// - Add `tokenUsage` { prompt, completion } to bot messages
// - Add `retrievalScore` to bot messages (from retrieval spans)
// - Add `toolsUsed` array to bot messages (from tool spans)
//
// The dashboard's computeMetrics() function handles all aggregation
// client-side, so you only need to produce the convLog array.

module.exports = { exampleConvLogEntry };
