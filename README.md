# Robin – a chatbot with guardrails, traces and evals

Robin is the customer service assistant of Nest & Co, an invented online homeware shop. It's built for the course *GenAI design for conversations and content*, to show today's architecture in one working bot:

- **A real chatbot widget** on a demo shop page: a chat bubble bottom right, built with [assistant-ui](https://www.assistant-ui.com).
- **System prompt:** Robin's behavior, written upfront (in `prompts.py`).
- **Input guardrails:** bank account numbers are removed by a pattern check (no LLM), and prompt injection is caught by a small model.
- **The LLM call:** GPT-6 Sol, with a switch to GPT-4.1 mini for comparison, and a reasoning effort setting.
- **Output guardrail:** a small model checks that every fact is in the return policy. If not, Robin tries once more, and otherwise gives a fixed, honest answer.
- **Observability:** every message becomes a readable trace in Langfuse.
- **Evals:** ready-made LLM-as-a-Judge prompts in `EVALUATORS.md`.

Robin runs on **Render** or **Vercel**. Same code, same traces: pick one, or try both and compare.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/convocat/Robin) [![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/clone?repository-url=https%3A%2F%2Fgithub.com%2Fconvocat%2FRobin&env=OPENAI_API_KEY%2CLANGFUSE_PUBLIC_KEY%2CLANGFUSE_SECRET_KEY%2CLANGFUSE_BASE_URL%2CCOURSE_PASSCODE&envDefaults=%7B%22LANGFUSE_BASE_URL%22%3A%20%22https%3A%2F%2Fcloud.langfuse.com%22%7D&envDescription=Your%20OpenAI%20API%20key%2C%20the%20public%20and%20secret%20key%20of%20your%20Langfuse%20project%20%28Settings%20%3E%20API%20Keys%29%2C%20the%20Langfuse%20region%20URL%2C%20and%20a%20passcode%20for%20participants.&envLink=https%3A%2F%2Fgithub.com%2Fconvocat%2FRobin%23what-you-need&project-name=robin&repository-name=robin)

*(These buttons deploy the course version from `convocat/Robin`. In your own copy, change `convocat/Robin` in both links to your GitHub name and repository.)*

## What you need

- An **OpenAI API key** with access to GPT-6 Sol, GPT-6 Luna and GPT-4.1 mini. Set a monthly spending limit in your OpenAI account.
- A **Langfuse project** and its API keys (Settings > API Keys). Langfuse Cloud has a free tier.
- A free **GitHub** account, and a free **Render** or **Vercel** account.

Both buttons ask for the same values: your OpenAI key, your two Langfuse keys, the Langfuse URL (`https://cloud.langfuse.com` for the EU region) and a course passcode, a word you give participants in the session.

## Option 1: Render

1. Click **Deploy to Render** and sign in (you can sign in with GitHub).
2. Fill in the values Render asks for. The other settings are already filled in by `render.yaml`.
3. Click **Deploy**. After a few minutes, Render shows a link like `https://robin-xxxx.onrender.com`.

Good to know:
- **On the free plan, Robin falls asleep after 15 minutes without visitors.** The next visitor waits about a minute. Open Robin yourself a few minutes before a session, or switch to the paid **Starter** plan (about $7 a month at the time of writing) to keep it awake.
- **Updating:** Render doesn't pick up changes on GitHub automatically. Click **Manual Deploy > Deploy latest commit**.
- Robin runs in Render's EU region (Frankfurt).

## Option 2: Vercel

1. Click **Deploy with Vercel** and sign in. Vercel makes a copy of the repository in your GitHub account.
2. Fill in the values Vercel asks for, and click **Deploy**. After a minute or two, Vercel shows a link like `https://robin-xxxx.vercel.app`.

Good to know:
- **Vercel runs Robin as functions:** every message starts the API, gets an answer, and stops. There's no sleeping server, but the first message after a quiet spell can take a few seconds longer.
- **Vercel's free (Hobby) plan is for personal, non-commercial use only.** Vercel defines commercial use broadly, so a bot used in a paid course probably needs the Pro plan. A student's own practice copy fits the free plan. If in doubt, ask Vercel support.
- **Updating:** every change pushed to GitHub is deployed automatically.
- Robin's API runs in Vercel's Frankfurt region (`fra1`, set in `vercel.json`).

## For students who want their own Robin

1. On the course's `Robin` repository on GitHub, click **Use this template** to make your own copy.
2. In **your** copy's README, change `convocat/Robin` in the button links to your GitHub name and repository.
3. Click a button and follow the steps above, with your own keys.

## Using Robin

Open the link, and fill in the **Course settings** panel (bottom left): your first name or a nickname, the passcode, Robin's model and the reasoning effort. Then click the chat bubble (bottom right). The settings panel sits outside the chatbot on purpose, so the widget looks and works like a real customer service widget.

## Run Robin on your own computer

You need Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate          # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then fill in your keys in .env
python app.py
```

Open http://127.0.0.1:3000 in your browser.

## Reading a trace in Langfuse

Every message a participant sends becomes **one trace**, named `Robin – chat turn`. Inside it, the steps are numbered in the order they happen. The step names never change, whichever model you pick, so the trace tree and the graph always look the same:

```
Robin – chat turn                                      input: the customer's message · output: Robin's final answer
├── 1. Input guardrail – bank account numbers          no LLM: a pattern check
├── 2. Input guardrail – prompt injection               small model
│   └── Injection check (small model)
├── 3. Robin writes the answer                          Robin's model, with the system prompt
├── 4. Output guardrail – facts check                   small model
│   └── Facts check (small model)
├── 5. Robin rewrites the answer                        only if step 4 blocked the answer
└── 6. Output guardrail – facts check on the rewrite    only if step 4 blocked the answer
```

Because the trace contains guardrail and agent steps, Langfuse also draws it as a **graph**. You'll find it in the trace view.

**Every step explains itself.** Click a step and look at its **metadata**:

| Metadata | What it says |
| --- | --- |
| `layer` | Input guardrail, LLM call, or output guardrail |
| `uses_llm` | Whether the step uses a model, and which kind ("no: a pattern check in code", "yes: the small model") |
| `what_it_does` | One sentence about the step |
| `if_it_fails` | Fail open or fail closed, for the guardrails |
| `result` | PASS, BLOCK, MASKED or ERROR, for the guardrails |

The guardrail outputs also carry an `explanation` in plain words, such as "Not in the return policy: a €20 voucher".

**The turn itself carries a summary** in its metadata: `outcome`, `what_happened` (one sentence), `step_1_bank_account_check`, `step_2_injection_check`, `step_4_facts_check` and `rewrite_needed`.

The model calls (steps 3 and 5, and the small-model checks) are **linked to their prompt** in Langfuse, with its version number. Click the prompt name to open it.

## Seeing when a guardrail hits

There are three ways, from quickest to most complete:

1. **Warnings in the trace.** Every guardrail that blocks, masks or fails is marked as a **warning**, with the reason as its status message. So is the whole turn, when Robin didn't send its own answer. In the trace tree, these steps stand out, and in the traces table you can filter on level = WARNING to see every turn where something was caught.
2. **Score columns.** Each turn has the scores `guardrail: bank account` (PASS or MASKED), `guardrail: prompt injection` (PASS, BLOCK or ERROR) and `guardrail: facts check` (PASS, BLOCK, ERROR or SKIPPED), plus `outcome`. Show them as columns in the traces table and filter on them, for example `guardrail: prompt injection` = BLOCK for every injection attempt.
3. **A dashboard.** In Langfuse's dashboards, chart the count of each guardrail score by value over time. That shows how often each guardrail fires across the whole cohort.

Note: `guardrail: facts check` shows the result of the last check. If the first answer was blocked and the rewrite passed, the score is PASS and the metadata says `rewrite_needed: yes`.

## Prompts in Langfuse

Robin's prompts live in Langfuse's **Prompt Management**, in the folder `robin/`:

| Prompt | Used by | Variables |
| --- | --- | --- |
| `robin/system-prompt` | Step 3 and 5: Robin's answer | `{{return_policy}}` |
| `robin/return-policy` | Filled into the system prompt and the facts check | none |
| `robin/injection-check` | Step 2: the input guardrail | none |
| `robin/facts-check` | Step 4 and 6: the output guardrail | `{{return_policy}}` |
| `robin/retry-note` | Step 5: tells Robin what to fix | `{{unsupported}}` |

- **The first time Robin runs, it creates these prompts in your Langfuse project** from the texts in `prompts.py`, with the label `production`. It never overwrites prompts that already exist.
- **To change a prompt, edit it in Langfuse** and give the new version the label `production`. Robin picks it up within a minute, without a redeploy. To go back, move the `production` label to an older version.
- **The return policy is one prompt, used in two places.** Change it once, and Robin and the facts check both use the new policy. That's the "context" layer from the course, made visible.
- **If Langfuse can't be reached,** Robin falls back to the texts in `prompts.py`. Those model calls then have no prompt link in the trace.

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

All traces are sent with the environment `course`, so they're easy to keep apart from other work in the same Langfuse project.

## Privacy and costs

- Bank account numbers are removed **before** anything is sent to OpenAI or Langfuse. Other personal data is not. Ask participants not to type real personal details.
- The participant's nickname is stored in Langfuse as the user. Tell participants this, as the course settings panel does.
- Robin runs in the EU (Render Frankfurt, or Vercel's Frankfurt region `fra1`), but conversations are sent to OpenAI and to Langfuse. Choose Langfuse's EU region (`https://cloud.langfuse.com`) to keep traces in the EU.
- Each chat is limited to 40 messages (`MAX_MESSAGES_PER_CHAT`). The conversation is kept in the browser, so a determined participant could get around this limit: set spending limits at OpenAI (and in Vercel, if you use it) rather than relying on it. Most messages make three model calls: two on the small Luna model and one on Robin's model. A retry after a blocked answer adds two more. A blocked injection attempt costs only one small call.

## Design choices you can discuss with participants

These are deliberate, so participants can find and improve them:

- **No handover path.** Robin's system prompt doesn't say what to do when the policy has no answer. Only the facts check fallback offers a colleague.
- **No date.** Robin doesn't know today's date, so it can't really check the 30-day window. A better design passes the date in, or lets code calculate it.
- **Gaps in the policy.** Does a return with one damaged and one unused item cost €4.95? The policy doesn't say.
- **Fail open vs fail closed.** If the injection check fails, the message is let through. If the facts check fails, the answer is not sent. Which is right for which guardrail?

## Changing Robin

- **Prompts:** edit them in Langfuse (see "Prompts in Langfuse" above). The fixed fallback messages, and the starting versions of the prompts, are in `prompts.py`.
- **Models:** the environment variables `ROBIN_MODEL`, `COMPARE_MODEL`, `GUARDRAIL_MODEL` and `GUARDRAIL_EFFORT`, in your Render or Vercel project settings (redeploy afterwards). Check the exact model names in your OpenAI account: the defaults are `gpt-6-sol`, `gpt-4.1-mini` and `gpt-6-luna`. GPT-4.1 mini leaves the OpenAI API on January 14, 2027.
- **The chat widget:** the source is in `widget/` (React with assistant-ui). After changing it, run `npm install` and `npm run build` inside `widget/`. That rebuilds `public/index.html`, the single page that Render and Vercel serve. `npm run build:preview` makes a version with scripted answers, for showing the design without keys.
- **Logic and tracing:** `robin.py`.

## Files

| File | What it does |
| --- | --- |
| `app.py` | Robin's API: `/api/chat` and `/api/feedback`. Also serves the chat page |
| `robin.py` | One chat turn: guardrails, the LLM call, and the Langfuse trace |
| `prompts.py` | All the text: system prompt, guardrail prompts, fallback messages |
| `public/index.html` | The demo shop page with the chat widget (built from `widget/`) |
| `widget/` | Source of the chat widget and the shop page |
| `EVALUATORS.md` | Eval prompts to paste into Langfuse |
| `render.yaml` | Tells Render how to run Robin |
| `vercel.json` | Tells Vercel how to run Robin |
| `requirements.txt` | Python packages |
| `.env.example` | Template for your keys when running locally |
| `tests/` | Offline tests with a fake model (`python -m pytest tests`) |
