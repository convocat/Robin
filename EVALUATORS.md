# Evals for Robin in Langfuse

These are the evals from the pop quiz, ready to paste into Langfuse as **LLM-as-a-Judge** evaluators. Each one gives a PASS or FAIL per chat turn. Langfuse adds them up, so you can see, for example, that 12% of answers asked more than one question.

## Naming: guardrail vs eval

Robin's trace already carries some scores. Their names tell you what they are:

| Score name starts with | What it is | When it's made |
| --- | --- | --- |
| `guardrail:` | The result of a guardrail check (PASS, BLOCK, MASKED, ERROR or SKIPPED) | **During** the conversation, by Robin's code |
| `outcome` | What happened in the end: answered, blocked by input guardrail, fallback after output guardrail, or error | **During** the conversation |
| `user feedback` | Thumbs up (1) or down (0) from the chat window | When a participant clicks it |
| `eval:` | One of the evals below | **After** the conversation, by Langfuse |

Give your evaluators names that start with `eval:`, so they sit together in the score columns and newcomers can tell them apart from guardrails.

## How to set up each evaluator

1. In Langfuse, open **Evaluators** and click **New evaluator**. Choose **LLM-as-a-Judge**, then start from a blank prompt.
2. **Model:** pick GPT-6 Luna (cheap and fast) or GPT-6 Sol (more careful). If you want to set reasoning effort, add it as a provider option, for example `{"reasoning_effort": "low"}`.
3. **Prompt:** paste the prompt below.
4. **Score type:** Boolean.
5. **Map the variables:** `{{input}}` to the observation's **input** (the customer's message) and `{{output}}` to the observation's **output** (Robin's final answer).
6. **Test** it on a few traces on the right, then save and **attach it to a rule**:
   - filter on the observation name `Robin – chat turn`, with **Is Root Observation** switched on;
   - set a sampling rate if you want to save costs (100% is fine for a course).

The exact labels in the Langfuse screens may differ slightly from these. The Langfuse docs on LLM-as-a-Judge describe the current screens.

---

## eval: one question at a time

```
You review one answer from Robin, the customer service chatbot of an online homeware shop.

Robin's conversation design requires it to ask at most one question per answer, so customers aren't overwhelmed.

Customer's message:
{{input}}

Robin's answer:
{{output}}

Count the questions Robin asks the customer. Count indirect questions as well, such as "Let me know your order number and the delivery date." Don't count rhetorical questions.

Return true if the answer contains at most one question. Return false if it contains two or more. Explain your decision in one sentence.
```

## eval: only facts from the policy

```
You review one answer from Robin, the customer service chatbot of an online homeware shop.

Robin may only use facts from this return policy:
- Customers can return products within 30 days of delivery.
- Products must be unused and in their original packaging.
- Made-to-measure products can't be returned.
- Returns cost €4.95, deducted from the refund. Returning a damaged product is free.
- The refund is paid within 14 days after the return arrives.

Customer's message:
{{input}}

Robin's answer:
{{output}}

Check every factual statement in Robin's answer about periods, amounts, costs, conditions and procedures. Ignore greetings, empathy, questions to the customer, and next steps Robin offers. Also check: if the policy doesn't answer the customer's question, did Robin say so, or did it guess?

Return true if every factual statement is in the policy and Robin didn't guess. Return false otherwise. Explain your decision in one sentence.
```

## eval: clear next step

```
You review one answer from Robin, the customer service chatbot of an online homeware shop.

Every answer should leave the customer knowing what happens next: a return label, an action they can take, a question to answer, or a handover to a colleague.

Customer's message:
{{input}}

Robin's answer:
{{output}}

Return true if the customer knows what the next step is after reading this answer. Return false if the answer leaves them stuck, or only gives information without a way forward. Explain your decision in one sentence.
```

## eval: natural language

```
You review one answer from Robin, the customer service chatbot of an online homeware shop. Robin answers in the language the customer writes in.

Customer's message:
{{input}}

Robin's answer:
{{output}}

Judge only the language of Robin's answer, not its content. Does it sound like natural, everyday language that a native speaker would write in a customer service chat? Watch for literal translations, stiff company jargon, and sentences that sound translated from English.

Return true if the answer sounds natural. Return false if a native speaker would phrase it differently. Explain your decision in one sentence, quoting the phrase that sounds unnatural if there is one.
```

---

## Note: evals judge one answer at a time

These evals look at one chat turn. Some questions only make sense for a whole conversation, such as "Did the customer leave with a return label?". For that, look at the **Sessions** view in Langfuse: every chat with Robin is one session. Session-level evals are a good next step for the course, once participants are comfortable with these.
