# Robin — reference guide to the repo

A map of this repository for conversation designers who know chatbots, prompts, guardrails, RAG
and evals, but not code. It explains where things live and what the engineering words mean.

For how to deploy and use Robin, see `README.md`. For course use, see `TEACHING_GUIDE.md`.

---

## 1. The big picture

Robin is the customer service bot of Nest & Co, an invented homeware shop, built for the course
*GenAI design for conversations and content*. The repo contains five things:

| Part | What it is | Language |
|---|---|---|
| **The bot** | Runs one chat turn: guardrails, LLM call, facts check, trace | Python |
| **The widget** | The demo shop page, the chat bubble and the course settings panel | JavaScript (React) |
| **Look-up (RAG)** | Ingestion of the handbook, and retrieval during a turn | Python |
| **Experiments and evals** | A 51-item test set, a runner script, LLM-as-a-judge prompts | Python + text |
| **PO/CxD dashboard** | A conversation-log dashboard that reads from Langfuse | JavaScript + Python |

### How they connect

```
 Visitor's browser                Robin's server (Render / Vercel / your laptop)
┌──────────────────┐   message   ┌──────────────┐        ┌──────────────┐
│ shop page        │ ──────────▶ │ app.py       │ ─────▶ │ robin.py     │
│ + chat widget    │ ◀────────── │ (receives    │        │ (runs the    │
│ (public/         │   answer    │  requests)   │        │  turn)       │
│  index.html)     │             └──────────────┘        └──┬───┬───┬───┘
└──────────────────┘                                         │   │   │
                                                             │   │   │
              ┌──────────────────────────────────────────────┘   │   │
              ▼                                                  ▼   ▼
      ┌───────────────┐        ┌──────────────────────┐   ┌────────────┐
      │ OpenAI        │        │ Langfuse             │   │ Postgres   │
      │ (models,      │        │ prompts · traces ·   │   │ (handbook  │
      │  embeddings)  │        │ scores · datasets    │   │  chunks)   │
      └───────────────┘        └──────────▲───────────┘   └─────▲──────┘
                                          │                     │
                    reads traces ─ dashboard-kit/     ingestion/ingest_handbook.py
                    runs datasets ─ experiments/      (fills the database)
```

### What happens in code when someone presses send

1. The widget sends the conversation so far to the address `/api/chat` on Robin's server.
2. `app.py` receives it, checks the passcode and the message limits, and passes it on to `robin.py`.
3. `robin.py` fetches the current prompts from Langfuse and runs the steps in order:
   bank account mask → injection check → (look-up, if on) → answer → facts check → (rewrite + second check, if blocked).
4. Each step is logged to Langfuse as part of one trace, named `Robin – chat turn`.
5. The final answer goes back to the widget.

---

## 2. "I want to change…": where to go

| I want to change… | Where | How it goes live |
|---|---|---|
| Robin's system prompt, the return policy, a guardrail prompt | **Langfuse** → Prompt Management → `robin/…` | Save a new version with the label `production`. Robin picks it up within about a minute. No code change. |
| My own test version of the system prompt | Langfuse, saved with your own label (for example `leela`) | Type the label in the course panel under **Prompt label** |
| The fixed fallback messages ("I'm not sure about that…") | `prompts.py` → `FALLBACKS` | Code change, then redeploy |
| The handbook Robin looks things up in | Langfuse prompt `robin/handbook` | Run the GitHub Action **Ingest the handbook** afterwards |
| The help-centre pages (`/help`) | `content/handbook.md`, `content/product-guide.md`, `content/faq.md` | Code change, then redeploy |
| Which models are used | Environment variables `ROBIN_MODEL`, `COMPARE_MODEL`, `GUARDRAIL_MODEL` (see section 5) | Change them in Render/Vercel settings, then redeploy |
| Look and feel of the chat widget or course panel | `widget/src/` | Run `npm run build` in `widget/`, then commit and redeploy |
| The test set | `experiments/robin-dataset.json` | Re-upload with `run_experiment.py --upload` |
| The judge prompts | `EVALUATORS.md`, or directly in Langfuse → Evaluators | The GitHub Action **Set up Langfuse evaluators** creates any that don't exist yet |
| The order or logic of the steps in a turn | `robin.py` | Code change, then run the tests and redeploy |

**Important:** `prompts.py` holds only the *starting* versions of the prompts. Robin copies them into
Langfuse on its first run, and never overwrites them after that. **Langfuse is the live source.**
Editing a prompt in `prompts.py` only changes the backup text, which is used when Langfuse can't
be reached.

---

## 3. File-by-file reference

### The bot (backend, Python)

| File | What it does |
|---|---|
| `app.py` | The **server**: the program that keeps running and answers requests. It defines the addresses Robin listens on: `/api/chat`, `/api/feedback` (thumbs up/down), `/help` and `/help/<page>` (help centre), `/chunks` (database contents, behind the passcode) and `/` (the shop page). It also enforces the passcode, the 40-message limit and the 2000-character message limit. |
| `robin.py` | **One chat turn.** The most important file. Key parts: `handle_turn` (runs the whole turn), `mask_bank_accounts` (IBAN pattern check), `_injection_step`, `_look_up`, `_facts_check`, `STEPS` (the plain-language metadata each trace step gets), and `record_feedback` (turns a thumbs up/down into a Langfuse score). |
| `prompts.py` | All text: starting versions of every Langfuse prompt, the fixed fallback messages (in English and Dutch), and the text that replaces a masked bank number. |
| `lookup.py` | The RAG plumbing: splitting the handbook into chunks (one per section), embedding, storing chunks in Postgres, and searching for the closest chunks. Max results can be 1, 3 or 5 (default 3). |
| `help_pages.py` | Turns the three files in `content/` into web pages, one link per section. |

### Prompts in Langfuse

| Prompt | Used for |
|---|---|
| `robin/system-prompt` | Robin's answer when look-up is off. Has `{{return_policy}}` in it. |
| `robin/return-policy` | Filled into the system prompt *and* the facts check: one policy, two uses |
| `robin/injection-check` | Input guardrail |
| `robin/facts-check` | Output guardrail (look-up off) |
| `robin/retry-note` | Tells Robin what to fix when the facts check blocked an answer |
| `robin/handbook` | The full handbook: the source for ingestion |
| `robin/query-rewrite` | Look-up step 1: turns the message into a search query |
| `robin/system-prompt-lookup` | Robin's answer when look-up is on |
| `robin/facts-check-lookup` | Output guardrail when look-up is on |
| `robin/retry-note-lookup` | Retry note when look-up is on |

Guardrails always use the `production` label. Only the system prompt follows a student's own label.

### The widget (frontend, JavaScript/React)

| File | What it does |
|---|---|
| `widget/src/App.jsx` | The page layout: the demo shop and the course settings panel |
| `widget/src/RobinWidget.jsx` | The chat bubble and chat window (built with the assistant-ui library) |
| `widget/src/robinAdapter.js` | Sends messages to `/api/chat` and feedback to `/api/feedback` |
| `widget/src/mockAdapter.js` | Scripted fake answers, for showing the design without API keys (`npm run build:preview`) |
| `widget/src/styles.css` | Colours, fonts, spacing |
| `public/index.html` | **The built result.** Generated from `widget/`. Don't edit it by hand: it gets overwritten on every build. |
| `public/chunks.html` | The page behind `/chunks` that shows the database contents |

### Content and ingestion

| File | What it does |
|---|---|
| `content/handbook.md` | Starting version of the customer handbook (the live version is in Langfuse) |
| `content/product-guide.md`, `content/faq.md` | Help-centre content |
| `ingestion/ingest_handbook.py` | Fetches `robin/handbook` from Langfuse, tidies it, chunks it, embeds it and replaces the old chunks in the database. Each run is traced as "Ingestion – customer handbook". |

### Experiments and evals

| File | What it does |
|---|---|
| `experiments/robin-dataset.json` | 51 test items: message, optional history, a description of a good answer, and metadata such as category, language and whether it's an attack |
| `experiments/run_experiment.py` | Runs the full Robin on the dataset with a chosen model and guardrail setting, as a Langfuse experiment |
| `experiments/create_evaluators.py` | Creates all evaluators from `EVALUATORS.md` in Langfuse |
| `experiments/code_evaluator_form_checks.py` | The four "form" checks (one question, short answer, no bank number, no leaked instructions) as exact code instead of an LLM judge |
| `EVALUATORS.md` | The LLM-as-a-judge prompts |
| `experiments/README.md` | How to run experiments, three ways |

### Dashboard

| File | What it does |
|---|---|
| `dashboard-kit/robin_adapter.py` | Pulls traces from Langfuse and writes `dashboard-data.json` |
| `dashboard-kit/dashboard-data.json` | The generated data. **Holds real participants' messages**, so it's deliberately kept out of GitHub. |
| `dashboard-kit/data-contract.js` | Describes the shape the data must have, so the dashboard and adapter agree |
| `dashboard-kit/dashboard.html` | The dashboard page itself (UI in Dutch for now) |
| `dashboard-kit/server.js` | A small local server that shows the dashboard in your browser |
| `dashboard-kit/thread-view/` | A separate mini-app that shows one conversation as a chat thread, with Bronnen (sources) and Beoordeling (review) panels |

### Settings, deploy and housekeeping

| File | What it does |
|---|---|
| `.env` | Your real keys and settings. **Only on your computer, never on GitHub.** |
| `.env.example` | Empty template of `.env` |
| `requirements.txt` | The Python add-on packages Robin needs |
| `render.yaml` / `vercel.json` | Instructions for the two hosting services |
| `.github/workflows/` | Three button-press jobs on GitHub (see section 4) |
| `tests/` | Automatic checks with a fake model (free to run) |
| `.claude/skills/` | This repo's own Claude Code skills: `robin-start`, `robin-dashboard`, `robin-backlog`, `robin-usecase-discovery`, `robin-conversation-design-review`, `robin-test-case-generator`, `robin-trace-to-persona` |
| `BACKLOG.md` / `HANDOVER.md` | Open work, and a snapshot of where things stand |
| `.gitignore` | List of files Git must never upload (such as `.env` and `dashboard-data.json`) |

---

## 4. Things outside the repo

The repo is only the code. Robin depends on these services:

| Service | What it holds or does | Where you manage it |
|---|---|---|
| **OpenAI** | The models: GPT-6 Sol (Robin), GPT-4.1 mini (comparison), GPT-6 Luna (guardrails and judges), text-embedding-3-small (embeddings) | platform.openai.com: keys and spending limits |
| **Langfuse** | Prompts, traces, scores, datasets, experiments, evaluators | cloud.langfuse.com |
| **Render** | Hosts Robin (option 1) and the Postgres content database | dashboard.render.com |
| **Vercel** | Hosts Robin (option 2) | vercel.com |
| **GitHub** | Stores the code and runs the three Actions | github.com: the repo's **Actions** tab |

### The three GitHub Actions

Each one runs on GitHub's computers when you press **Actions → (name) → Run workflow**:

| Action | Does |
|---|---|
| **Ingest the handbook** | Re-ingests `robin/handbook` into the database. Run it after every handbook change. |
| **Run Robin experiment** | Runs the dataset on one setting, or on a four-run comparison |
| **Set up Langfuse evaluators** | Creates the judges from `EVALUATORS.md` (skips any that already exist) |

---

## 5. Settings (environment variables)

These are set in `.env` locally, or in the Render/Vercel project settings online.

| Setting | What it controls | Default |
|---|---|---|
| `OPENAI_API_KEY` | Access to OpenAI | — |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | Access to your Langfuse project | — |
| `LANGFUSE_BASE_URL` | Langfuse region | `https://cloud.langfuse.com` (EU) |
| `LANGFUSE_TRACING_ENVIRONMENT` | Label that keeps course traces apart | `course` |
| `ROBIN_MODEL` | Robin's main model | `gpt-6-sol` |
| `COMPARE_MODEL` | The second model in the model switch | `gpt-4.1-mini` |
| `GUARDRAIL_MODEL` | Small model for guardrails | `gpt-6-luna` |
| `GUARDRAIL_EFFORT` | Reasoning effort for the guardrail model | `low` |
| `MAX_MESSAGES_PER_CHAT` | Message limit per chat window | `40` |
| `COURSE_PASSCODE` | Word participants need to use Robin | empty |
| `DATABASE_URL` | Address of the Postgres content database (only needed for look-up) | — |

---

## 6. Commands you might run

Type these in a terminal opened in the repo folder, or simply ask Claude Code to run them for you.

| Command | What it does |
|---|---|
| `/robin-start` (in Claude Code) | Starts Robin locally; open http://127.0.0.1:3000 |
| `/robin-dashboard` (in Claude Code) | Refreshes and opens the PO/CxD dashboard |
| `python app.py` | Starts Robin locally by hand |
| `python -m pytest tests` | Runs all automatic tests (free: uses a fake model) |
| `npm install` then `npm run build` (inside `widget/`) | Rebuilds the widget into `public/index.html` |
| `python experiments/run_experiment.py --model "GPT-6 Sol" --guardrails on` | Runs an experiment from your laptop (costs OpenAI credits) |
| `git status` | Shows which files you've changed but not yet saved to history |

---

## 7. Code words, briefly

| Word | Meaning |
|---|---|
| **Repo** (repository) | This project folder, plus its full change history |
| **Commit** | One saved change in that history, with a message |
| **Push** | Upload your commits to GitHub |
| **Backend** | Code running on a server: here, Python |
| **Frontend** | Code running in the visitor's browser: here, React |
| **Server** | A program that keeps running and answers requests |
| **API / endpoint** | A fixed address on the server that does one job, such as `/api/chat` |
| **Build** | Turning source files into the final files a browser can load |
| **Deploy** | Putting a version of the code on a public server |
| **Environment variable** | A setting or secret kept outside the code |
| **Package / dependency** | A ready-made add-on the code uses (listed in `requirements.txt` or `package.json`) |
| **`.venv`** | A private folder with Robin's Python packages, so they don't clash with anything else |
| **`node_modules`** | The same idea for JavaScript packages. Big, generated, never edited by hand. |
| **Database** | Structured storage. Here, a table of handbook chunks with their embeddings. |
| **pgvector** | An add-on that lets Postgres search by embedding similarity |
| **GitHub Action** | A job GitHub runs for you on its own computers |
| **Test** | An automatic check that code still does what it should |
| **Fallback** | What the code does when something fails, such as built-in prompts when Langfuse is down |

---

## 8. Gotchas

- **Prompts:** edit them in Langfuse, not in `prompts.py`. Changes in `prompts.py` don't reach a Robin that's already running.
- **Handbook:** changing it in Langfuse does nothing until you run **Ingest the handbook**.
- **Widget:** changing `widget/src/` does nothing until you run `npm run build`. Never edit `public/index.html` directly.
- **Render** doesn't update automatically: use **Manual Deploy → Deploy latest commit**. Vercel updates on every push.
- **On a first visit all guardrails are off.** That's intentional, so participants see the bare system prompt first.
- **Secrets:** `.env` and `dashboard-data.json` must never go to GitHub. `.gitignore` already keeps them out.
- **Some gaps are deliberate teaching material:** no handover path, no knowledge of today's date, gaps in the return policy. See "Design choices" in `README.md`.
