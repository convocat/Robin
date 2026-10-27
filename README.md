# Robin – a chatbot with guardrails, traces and evals

Robin is the customer service assistant of Nest & Co, an invented online homeware shop. It's built for the course *GenAI design for conversations and content*, to show today's architecture in one working bot:

- **System prompt:** Robin's behavior, written upfront (in `prompts.py`).
- **Input guardrails:** bank account numbers are removed by a pattern check (no LLM), and prompt injection is caught by a small model.
- **The LLM call:** GPT-6 Sol, with a switch to GPT-4.1 mini for comparison, and a reasoning effort setting.
- **Output guardrail:** a small model checks that every fact is in the return policy. If not, Robin tries once more, and otherwise gives a fixed, honest answer.
- **Observability:** every message becomes a readable trace in Langfuse.
- **Evals:** ready-made LLM-as-a-Judge prompts in `EVALUATORS.md`.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/convocat/Robin)

*(This button deploys the course version from `convocat/Robin`. In your own copy, change `convocat/Robin` in the link to your GitHub name and repository.)*

## What you need

- An **OpenAI API key** with access to GPT-6 Sol, GPT-6 Luna and GPT-4.1 mini. Set a monthly spending limit in your OpenAI account.
- A **Langfuse project** and its API keys (Settings > API Keys). Langfuse Cloud has a free tier.
- A free **GitHub** account and a free **Render** account, to put Robin online.

## Put Robin online with Render

Render runs Robin for you. The project includes a `render.yaml` file that tells Render exactly what to do, so you don't have to configure anything by hand. Robin runs in Render's EU region (Frankfurt).

### The first time (for the course teacher)

1. **Put the project on GitHub.** Create a new repository called `robin` on github.com, make it **public**, and upload all files from this folder, including `render.yaml`. Don't upload `.env`.
2. **Make it a template** (optional, for students): in the repository's **Settings**, tick **Template repository**.
3. **Fix the button:** in this README, change the repository in the "Deploy to Render" link to yours.
4. **Click the "Deploy to Render" button** and sign in to Render (you can sign in with GitHub).
5. **Fill in the values Render asks for:** your OpenAI key, your two Langfuse keys, and a course passcode (a word you give participants in the session). The other settings are already filled in.
6. **Click Deploy.** After a few minutes, Render shows a link like `https://robin-xxxx.onrender.com`. That's Robin.

### For students who want their own Robin

1. On the course's `robin` repository on GitHub, click **Use this template** to make your own copy (or download the files and upload them to a new repository).
2. In **your** copy's README, change the GitHub name in the "Deploy to Render" link to yours.
3. Click the button and follow steps 4 to 6 above, with your own keys.

### Good to know about the free plan

- **Robin falls asleep after 15 minutes without visitors.** The next visitor waits about a minute while it wakes up. Before a session, open Robin yourself a few minutes early.
- **Want Robin always awake?** In Render, change the plan to **Starter** (a paid plan, about $7 a month at the time of writing).
- **After the course:** suspend or delete the service in Render, so nobody keeps using your OpenAI key.
- **Changing Robin:** with the button, Render doesn't automatically pick up changes you make on GitHub later. In Render, click **Manual Deploy** to update.

## Run Robin on your own computer (for demos and testing)

You need Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate          # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then fill in your keys in .env
python app.py
```

Open http://127.0.0.1:7860 in your browser.

## Reading a trace in Langfuse

Every message a participant sends becomes **one trace**, named `Robin – chat turn`. Inside it, the steps are numbered in the order they happen:

```
Robin – chat turn                                  input: the customer's message · output: Robin's final answer
├── 1. Input guardrail – bank account numbers      result: PASS or MASKED
├── 2. Input guardrail – prompt injection          result: PASS, BLOCK or ERROR
│   └── Injection check (gpt-6-luna)               the small model's verdict
├── 3. Robin's answer (gpt-6-sol)                  the system prompt, the conversation and Robin's draft
├── 4. Output guardrail – facts check              result: PASS, BLOCK or ERROR
│   └── Facts check (gpt-6-luna)
└── 3b. / 4b.                                      only when the facts check blocked the first draft
```

Every guardrail step shows a plain-language **explanation** of its decision in its output.

**What to show in the traces table.** Use the column settings to show these, and save it as a view for participants:

| Column | What it shows |
| --- | --- |
| Input / Output | The customer's message and Robin's final answer, as plain text |
| User | The name or nickname the participant typed, so everyone can find their own chats |
| Session | One ID per chat window. Open the **Sessions** view to read a whole conversation |
| Tags | `robin` and the model, such as `model: gpt-6-sol`. Filter on this to compare models |
| Scores | `guardrail: bank account`, `guardrail: prompt injection`, `guardrail: facts check`, `outcome`, `user feedback`, and your `eval:` scores |
| Metadata | `robin_model`, `reasoning_effort`, `guardrail_model`, and `outcome` on the turn itself |
| Latency / Cost | How long a turn took, and its token cost (cost only appears once Langfuse knows the model's price) |

Two handy filters for the session: `outcome` is "blocked by input guardrail" (every injection attempt), and `guardrail: facts check` is BLOCK (every time Robin tried to say something that isn't in the policy).

All traces are sent with the environment `course`, so they're easy to keep apart from other work in the same Langfuse project.

## Privacy and costs

- Bank account numbers are removed **before** anything is sent to OpenAI or Langfuse. Other personal data is not. Ask participants not to type real personal details.
- The participant's nickname is stored in Langfuse as the user. Tell participants this, as the chat window does.
- Robin runs in the EU (Render Frankfurt), but conversations are sent to OpenAI and to Langfuse. Choose Langfuse's EU region (`https://cloud.langfuse.com`) to keep traces in the EU.
- Each chat is limited to 40 messages (`MAX_MESSAGES_PER_CHAT`). Most messages make three model calls: two on the small Luna model and one on Robin's model. A retry after a blocked answer adds two more. A blocked injection attempt costs only one small call.

## Design choices you can discuss with participants

These are deliberate, so participants can find and improve them:

- **No handover path.** Robin's system prompt doesn't say what to do when the policy has no answer. Only the facts check fallback offers a colleague.
- **No date.** Robin doesn't know today's date, so it can't really check the 30-day window. A better design passes the date in, or lets code calculate it.
- **Gaps in the policy.** Does a return with one damaged and one unused item cost €4.95? The policy doesn't say.
- **Fail open vs fail closed.** If the injection check fails, the message is let through. If the facts check fails, the answer is not sent. Which is right for which guardrail?

## Changing Robin

- **Text** (system prompt, guardrail prompts, fallback messages): `prompts.py`. No code knowledge needed. On GitHub you can edit it in the browser, then click **Manual Deploy** in Render.
- **Models:** the environment variables `ROBIN_MODEL`, `COMPARE_MODEL`, `GUARDRAIL_MODEL` and `GUARDRAIL_EFFORT`, under **Environment** in Render. Check the exact model names in your OpenAI account: the defaults are `gpt-6-sol`, `gpt-4.1-mini` and `gpt-6-luna`. GPT-4.1 mini leaves the OpenAI API on January 14, 2027.
- **Logic and tracing:** `robin.py`.

## Files

| File | What it does |
| --- | --- |
| `app.py` | The chat window (Gradio) |
| `robin.py` | One chat turn: guardrails, the LLM call, and the Langfuse trace |
| `prompts.py` | All the text: system prompt, guardrail prompts, fallback messages |
| `EVALUATORS.md` | Eval prompts to paste into Langfuse |
| `render.yaml` | Tells Render how to run Robin (used by the "Deploy to Render" button) |
| `requirements.txt` | Python packages |
| `.env.example` | Template for your keys when running locally |
| `tests/` | Offline tests with a fake model (`python -m pytest tests`) |
