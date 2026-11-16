---
name: robin-start
description: "Start Robin (the chatbot) locally on this machine: checks the .venv and .env, installs requirements if needed, starts app.py in the background and confirms it answers on http://127.0.0.1:3000. Triggers: '/robin-start', 'start Robin', 'start Robin locally', 'run Robin', 'run Robin locally', 'launch Robin'."
---

# robin-start — run Robin on this computer

When invoked, get Robin running at http://127.0.0.1:3000 without Maaike touching the CLI herself.

## Step 1 — Already running?

Check port 3000 first:
```bash
curl -s -m 3 http://127.0.0.1:3000/ -o /dev/null -w "%{http_code}"
```
A `200` means something is serving there. Confirm it's Robin: the page title is `Nest & Co demo shop` (`curl -s -m 3 http://127.0.0.1:3000/ | grep -o '<title>[^<]*</title>'`). If it is, Robin is already up: skip to Step 4 (don't start a second one). If another program holds port 3000, tell Maaike which one (`netstat -ano | grep ':3000 '` gives the PID) and ask before doing anything; don't stop it yourself.

## Step 2 — Check prerequisites

1. **Virtual environment:** `.venv/Scripts/python.exe` must exist. If it's missing, create it (`python -m venv .venv`) and run `.venv/Scripts/python.exe -m pip install -r requirements.txt`.
2. **Packages:** run `.venv/Scripts/python.exe -c "import flask, waitress, langfuse, openai, dotenv"`. If that fails, run `.venv/Scripts/python.exe -m pip install -r requirements.txt`.
3. **Keys:** `.env` must exist at the repo root with at least `OPENAI_API_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` and `LANGFUSE_BASE_URL` filled in. Check only the key *names* — never print the values. If `.env` or a key is missing, tell Maaike which one and stop; never guess or invent values. (`.env.example` is the template.)

## Step 3 — Start Robin

Run from the repo root, in the background (the server keeps running):
```bash
.venv/Scripts/python.exe app.py
```
`app.py` serves with waitress on port `PORT` (default 3000). Wait a few seconds, then repeat the curl from Step 1 until it returns `200` (give up after ~30 seconds and show the server's output if it doesn't come up).

## Step 4 — Confirm and hand off

Tell Maaike Robin runs at **http://127.0.0.1:3000** and mention:
- Which Langfuse environment the local traces go to: the value of `LANGFUSE_TRACING_ENVIRONMENT` in `.env` (safe to show — it's not a secret). If it's `course`, warn that local test chats will show up between the real course chats and in the robin-dashboard.
- The course passcode is set in `.env` (`COURSE_PASSCODE`) — don't print it.
- To stop Robin: stop the background task, or close the terminal it runs in.

She opens it herself; only open the browser pane if she asks to see it.

## Notes

- The page is `public/index.html`, built from `widget/`. After changing the widget, run `npm install` and `npm run build` inside `widget/`, then refresh the browser — no restart needed. Changes to Python files (`app.py`, `robin.py`, `prompts.py`, …) do need a restart: waitress has no auto-reload.
- Prompts come from Langfuse (label `production`); on the first run Robin creates any missing prompts from `prompts.py`.
