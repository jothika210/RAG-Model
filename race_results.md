# Agent vs Fixed Workflow — Race Results (Week 7, HR Policy)

6 scenarios, each run through both a hand-built agent loop (`app/agent.py`, real OpenRouter calls deciding each step, with short-term memory (a distilled scratchpad, not the full raw transcript), long-term memory (a JSON file recalling previously-answered questions), and a web_search fallback tool for questions the internal HR corpus doesn't cover) and a fixed sequence (`app/fixed_workflow.py`, keyword-detected categories, one search per category, no adaptive step count, no memory, no web fallback).

## Comparison table

| Scenario | Agent time | Agent cost | Agent outcome | Workflow time | Workflow cost | Workflow outcome |
|---|---|---|---|---|---|---|
| s1 | 21.0s | $0.00159 | finished | 2.4s | $0.00010 | answered |
| s2 | 13.1s | $0.00125 | finished | 3.4s | $0.00026 | answered |
| s3 | 9.9s | $0.00096 | finished | 3.2s | $0.00018 | answered |
| s4 | 12.2s | $0.00131 | max_steps_exceeded (6) | 1.8s | $0.00013 | answered |
| s5 | 9.5s | $0.00096 | finished | 1.9s | $0.00018 | answered |
| s6 | 15.0s | $0.00129 | finished | 1.4s | $0.00007 | answered |

## Aggregate

- **Speed**: agent avg 13.4s vs workflow avg 2.3s
- **Cost**: agent avg $0.00123 vs workflow avg $0.00015
- **Reliability (completed cleanly)**: agent 5/6 vs workflow 6/6
- **Agent hit a stop condition (not a clean finish) on**: 1/6 scenarios

## Full step log for one representative agent run

**Scenario s1**: I'm a full-time confirmed employee based in Singapore (APAC). What's my carry-over cap, and what does 'continuous service' mean for me?

- **Step 1** (fallback_parse=False)
  - Thought: I need to search the HR policy corpus for information regarding the carry-over cap for full-time employees in the APAC region and the definition of 'continuous service.'
  - Action: `search_policy` `{'query': 'carry-over cap full-time employee', 'region': 'APAC'}`
  - Observation: [HR-207_carryover_apac.md::structure_aware::3] policy=HR-207 section=3 score=0.781: ## 3. Revised Carry-Over Table  | Employment Status | Region | Carry-Over Cap | Effective | |---|---|---|---| | Full
- **Step 2** (fallback_parse=False)
  - Thought: I have found relevant information regarding the carry-over cap for full-time confirmed employees in Singapore, which is 7 days. Now, I need to find the definition of 'continuous service' to provide a complete answer. I will search for 'continuous service definition' in the HR policy corpus to find the relevant section.
  - Action: `search_policy` `{'query': 'continuous service definition', 'region': 'APAC'}`
  - Observation: [HR-207_carryover_apac.md::structure_aware::1] policy=HR-207 section=1.1 score=0.792: ### 1.1 Definitions  "Continuous service" carries the same meaning defined in HR-201 Section 1.2: unbroken employm
- **Step 3** (fallback_parse=False)
  - Thought: I need to retrieve the specific details regarding the carry-over cap for full-time employees in Singapore and the definition of "continuous service" to provide a complete answer. I will first get the relevant chunk for the carry-over cap and then the definition of continuous service.
  - Action: `get_chunk` `{'chunk_id': 'HR-201_annual_leave_apac.md::structure_aware::6'}`
  - Observation: [HR-201_annual_leave_apac.md::structure_aware::6] policy=HR-201 section=3: ## 3. Eligibility Table

| Employment Status | Minimum Continuous Service | Annual Entitlement | Carry-Over Cap |
|---|---|--
- **Step 4** (fallback_parse=False)
  - Thought: I have found the relevant information regarding the carry-over cap for full-time confirmed employees in Singapore, as well as the definition of "continuous service." I will now retrieve the exact definitions for "continuous service" to ensure accuracy before finalizing the answer.
  - Action: `get_chunk` `{'chunk_id': 'HR-201_annual_leave_apac.md::structure_aware::2'}`
  - Observation: [HR-201_annual_leave_apac.md::structure_aware::2] policy=HR-201 section=1.2: ### 1.2 Definitions

"Continuous service" means unbroken employment with the company from the employee's confirmed start da
- **Step 5** (fallback_parse=False)
  - Thought: I need to find the specific carry-over cap for full-time employees based in Singapore. I have already searched for the carry-over cap and found relevant chunks, but I need to confirm the exact details from the relevant policy section. I will retrieve the chunk that discusses the carry-over cap for full-time employees in Singapore to provide an accurate answer.
  - Action: `get_chunk` `{'chunk_id': 'HR-201_annual_leave_apac.md::structure_aware::10'}`
  - Observation: [HR-201_annual_leave_apac.md::structure_aware::10] policy=HR-201 section=4.2: ### 4.2 Regional Exception — Singapore

Employees based in Singapore may carry over up to 7 days (not the standard 5-day c
- **Step 6** (fallback_parse=False)
  - Thought: I have gathered information about the carry-over cap for full-time confirmed employees in Singapore and the definition of "continuous service." Now, I will summarize the findings to provide a clear answer to the user's question.
  - Action: `finish` `{'summary': "As a full-time confirmed employee based in Singapore, you can carry over up to 7 days of leave due to statutory minimum requirements under the Singapore Employment Act. This is an exception to the standard 5-day cap applicable to other regions. 'Continuous service' means unbroken employment with the company, which is essential for determining eligibility for various benefits.", 'citations': ['HR-201_annual_leave_apac.md::structure_aware::10', 'HR-201_annual_leave_apac.md::structure_aware::2']}`
  - Observation: (finished)
- **Stop reason**: finished
- **Final answer**: As a full-time confirmed employee based in Singapore, you can carry over up to 7 days of leave due to statutory minimum requirements under the Singapore Employment Act. This is an exception to the standard 5-day cap applicable to other regions. 'Continuous service' means unbroken employment with the company, which is essential for determining eligibility for various benefits.
- **Citations**: ['HR-201_annual_leave_apac.md::structure_aware::10', 'HR-201_annual_leave_apac.md::structure_aware::2']

## Where the agent's extra capability actually mattered

3 of 6 scenarios (s1, s4, s6) were designed to need a cross-reference chase (a chunk mentioning "as defined in Section X") that the fixed workflow cannot follow, since it never calls get_chunk. For each: did the agent actually chase it, and did the fixed workflow's answer admit the resulting gap or silently omit the detail?

- **s1**: agent chased a cross-reference (`get_chunk` called): **True**; fixed workflow's answer explicitly admitted the gap: **True**
- **s4**: agent chased a cross-reference (`get_chunk` called): **True**; fixed workflow's answer explicitly admitted the gap: **True**
- **s6**: agent chased a cross-reference (`get_chunk` called): **False**; fixed workflow's answer explicitly admitted the gap: **True**

## Memory and web-search fallback behavior

Of 6 agent runs: 0 were answered by recalling long-term memory (zero new tool calls made) and 1 triggered the web_search fallback tool at least once. The escalation rule in `app/agent.py`'s `SYSTEM_PROMPT` requires two failed internal searches before web_search is allowed, and every scenario that used it in this run followed that order (verified by inspecting the step log directly, not merely by prompt instruction).

## Which one would I ship, and why

**Fixed workflow wins speed** (agent 13.4s vs workflow 2.3s, ~5.8x) and **fixed workflow wins cost** (agent $0.00123 vs workflow $0.00015, ~8.0x). The agent completed 5/6 scenarios cleanly, versus 6/6 for the fixed workflow — the workflow is also MORE reliable on raw completion, not just faster and cheaper, on this run.

**A real reliability caveat on the agent's number**: 1/6 agent run(s) in this specific execution hit the step-count safety cap rather than finishing cleanly. Investigating why revealed a genuine format-reliability problem, not a one-off fluke: the underlying model does not consistently follow the prescribed `Action: name` / `Action Input: {json}` template. Across development we observed at least three distinct drifts -- inline call syntax with keyword args, purely positional args with no keywords, and an inline call paired with an empty (but syntactically valid) `Action Input: {}` that silently masked the real arguments -- each was patched into the parser (`app/agent.py::_parse_action`) as found, and this run still shows a residual case (a `get_chunk` call whose chunk_id could not be extracted at all). This is exactly the kind of open-ended reliability risk a fixed workflow does not carry, since it never depends on an LLM emitting a specific, parseable action string.

**A second, distinct reliability issue found during testing (reasoning-action mismatch)**: in one observed run, the model's own Thought at step 3 stated "I have found the relevant information... I will now summarize this information and prepare to finish" -- but its chosen Action that same turn was `search_policy`, not `finish`. The model correctly reasoned it had enough information, then acted against its own stated conclusion anyway, eventually exhausting the step budget without ever answering. This is not a parsing bug (both fields parsed correctly) -- it is a genuine LLM behavior quirk with no code-level fix attempted here, reported honestly as further evidence that a hand-built agent's reliability is not fully controllable by prompt engineering alone.

**Recommendation: ship the fixed workflow as the default path.** It is faster and cheaper on every scenario measured, and where it can't fully answer (a question needing a cross-reference the fixed sequence structurally can't chase), it honestly admits the gap rather than guessing — a safe failure mode, not a silent wrong answer. Reserve the agent for a narrow, deliberate escalation path: run it only when the fixed workflow's own answer contains a self-reported gap (e.g. "not explicitly stated"), rather than paying the agent's full latency and cost premium on every request by default. This follows the week's own framing directly: an agent is for when the path changes with the input, and the fixed workflow's own admission of incompleteness is itself a cheap, reliable signal for exactly when that's happening.
