# Experiments with Robin

`robin-dataset.json` holds 51 test items for Langfuse experiments: regular questions, policy edge cases, out-of-scope questions, guardrail tests (bank account numbers, prompt injection, facts check), other languages, several questions at once, long messages, and three conversations that continue an earlier chat.

Each item has:

| Field | What's in it |
| --- | --- |
| `input.message` | The customer's message |
| `input.history` | Earlier turns of the conversation (empty for most items) |
| `expected_output.good_answer` | What a good answer does, in one or two sentences |
| `metadata` | `category`, `language`, `attack` (true for injection attempts), `bank_number` (the number to check isn't repeated), and `source` (its number in the test messages doc) |

There are two ways to run it. Use both: they answer different questions.

## 1. In the Langfuse UI: compare models on the system prompt alone

This runs only Robin's system prompt, without guardrails. It's the quickest way to compare models.

1. Upload the dataset and the chat prompt once, from your own computer: `python experiments/run_experiment.py --upload`. This creates the dataset `robin-experiment` and the chat prompt `robin/experiment-chat` (the system prompt, then the `history` placeholder, then `{{message}}`).
2. In Langfuse, open **Datasets > robin-experiment > Start Experiment** and create a prompt experiment.
3. Choose the prompt `robin/experiment-chat`, an LLM connection and a model, and the evaluator below.
4. Repeat with another model. Compare the runs side by side on the dataset page.

The chat prompt holds its own copy of the system prompt and return policy. If you change `robin/system-prompt` or `robin/return-policy`, change this one too.

## 2. With the script: the full Robin, with or without guardrails

This runs Robin exactly as the chatbot does, including the guardrails you choose:

```
python experiments/run_experiment.py --model "GPT-6 Sol" --guardrails on
python experiments/run_experiment.py --model "GPT-6 Sol" --guardrails off
python experiments/run_experiment.py --model "GPT-4.1 mini" --guardrails on
python experiments/run_experiment.py --model "GPT-6 Sol" --effort low --guardrails injection,facts
```

`--guardrails` takes `on`, `off`, or a list of the ones to switch on: `bank_account`, `injection`, `facts`. To try another model, point `COMPARE_MODEL` in your `.env` at it (for example `COMPARE_MODEL=gpt-6-luna`) and run with `--model "GPT-4.1 mini"`: that label then uses your model.

Add `--user "Your name"` to show your name as the user in Langfuse (the default is `experiment`). Each run gets a name such as `GPT-6 Sol · effort medium · guardrails all off`.

The checks run in Langfuse, as evaluators (see "The evaluators in Langfuse" below), so they score UI experiments and live chats too. Add `--local-checks` to have the script score the four form checks itself, for example when the code evaluator isn't set up. Don't use both at once: the scores would be counted twice.

Every item also has Robin's usual trace inside it, with the guardrail steps and the `outcome` score. The runs use the tracing environment `experiment`, so they stay apart from the course chats.

Each item makes up to five model calls with guardrails on, so a run of 51 items is a few hundred calls. Check your OpenAI spending limit before running many settings.

## 3. On GitHub, with one button

The workflow `.github/workflows/experiment.yml` runs the script on GitHub's servers, so you don't need Python on your own computer.

1. **Add your keys once**, in the repository on GitHub: **Settings > Secrets and variables > Actions > New repository secret**. Add three secrets: `OPENAI_API_KEY`, `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`. Use keys for the Langfuse project you want the runs in. GitHub keeps secrets hidden, also from people who can read the repository. If your Langfuse project isn't in the EU region, add a *variable* (not a secret) `LANGFUSE_BASE_URL` on the same page.
2. **Start a run:** **Actions > Run Robin experiment > Run workflow**. Choose one run (a model and a guardrail setting) or the comparison (both models, guardrails on and off: four runs), and fill in your name as the user.
3. **Look at the results** in Langfuse under **Datasets > robin-experiment**. The first run uploads the dataset by itself.

A comparison makes four runs of 51 items, so up to a thousand model calls with guardrails on. Check your OpenAI spending limit first.

## The evaluators in Langfuse

The scoring happens in Langfuse, with **LLM-as-a-Judge evaluators** you build in the Langfuse screens, so students can open each one and read what it checks. The prompts are in [`EVALUATORS.md`](../EVALUATORS.md). For experiments, use at least these:

| Evaluator | Checks |
| --- | --- |
| `eval: one question at a time` | At most one question per answer |
| `eval: short answer` | Fewer than 60 words |
| `eval: no bank account number repeated` | No bank account number in the answer |
| `eval: no instructions leaked` | No instructions revealed |
| `eval: matches the good answer` | Does what the item's good-answer description says (uses the expected output) |
| `eval: only facts from the policy` | Every fact is in the return policy |

**To create them all at once:** run **Actions > Set up Langfuse evaluators > Run workflow** on GitHub (or `python experiments/create_evaluators.py` on your own computer). It creates every evaluator in `EVALUATORS.md` as a Boolean LLM-as-a-Judge evaluator, on GPT-6 Luna, plus two rules: **Robin – experiments** (on, for new runs of `robin-experiment`) and **Robin – live chats** (off; switch it on in Langfuse when you want live scoring). Evaluators and rules that already exist are left alone. Afterwards they're under **Evaluators**, where you and your students can open, read and edit each one.

To build one by hand instead, set it to **Boolean**, aim it at **experiments** on the dataset `robin-experiment`, and Langfuse scores every new run. True means Robin did well, so the ideal is true for every item. Each judgement is one model call, so six evaluators on a run of 51 items is about 300 calls: use a small model such as GPT-6 Luna for the judges.

**Optional, exact checks in code:** `code_evaluator_form_checks.py` does the four form checks as one Langfuse **code evaluator** (Evaluators > New evaluator > Code evaluator > Python). It's exact and free, but students see Python code instead of a prompt. Comparing it with the LLM judges is a good discussion: the word count in particular is something a model does badly and a rule does perfectly. The script can also score these checks itself with `--local-checks`.

## Good comparisons for the course

| Question | Runs to compare |
| --- | --- |
| What do guardrails add? | Same model, `--guardrails on` and `--guardrails off`. Look at the attack items and `eval: no instructions leaked` |
| Does a bigger model need fewer guardrails? | GPT-6 Sol and GPT-4.1 mini, both with guardrails off |
| What does reasoning effort change? | GPT-6 Sol with `--effort low` and `--effort high`; compare scores and latency |
| Which guardrail catches what? | `--guardrails injection` and `--guardrails facts`, one at a time |
