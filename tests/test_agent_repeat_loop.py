"""Week 8 -- regression test for the s4 failure mode: the agent used to
call get_chunk on the exact same chunk_id repeatedly (observed for real:
5 identical calls in a row, see data/agent/race_raw.json's s4 run) when
that chunk_id's content never changed and never helped, burning the
entire MAX_STEPS budget with final_answer=None. This test forces the
identical-repeat condition deterministically (get_chunk always returns
the same heading-only text) and asserts the agent never dispatches that
same tool call more than once in a row -- proving the repeated-call
detection added to app/agent.py actually intercepts it.
"""

from app.agent_tools import ToolCallResult


def _heading_only_get_chunk(chunk_id: str) -> ToolCallResult:
    return ToolCallResult(tool_name="get_chunk", output=f"[{chunk_id}] policy=HR-207 section=4: ## 4. Section 4.2 -- Probationary Employee Carry-Over Cap")


def test_agent_does_not_repeat_the_same_tool_call_back_to_back(monkeypatch):
    import app.agent as agent_module

    monkeypatch.setattr(agent_module, "get_chunk", _heading_only_get_chunk)
    # search_policy keeps steering the model back toward the same
    # heading-only chunk, reproducing the real s4 conditions where the
    # agent had no other lead to follow.
    monkeypatch.setattr(agent_module, "search_policy", lambda query, region=None: ToolCallResult(
        tool_name="search_policy",
        output="[HR-207_carryover_apac.md::structure_aware::4] policy=HR-207 section=4 score=0.858: ## 4. Section 4.2 -- Probationary Employee Carry-Over Cap",
    ))

    scenario = {
        "id": "repeat_loop_test",
        "question": "Probationary employee in APAC (India), unique phrasing jkl321, what's my carry-over cap during probation?",
        "region": "APAC",
    }

    run = agent_module.run_agent(scenario)

    consecutive_identical_dispatches = 0
    for prev, curr in zip(run.steps, run.steps[1:]):
        if prev.action == curr.action == "get_chunk" and prev.action_input == curr.action_input:
            # the second of the pair must be the synthetic repeated-call
            # nudge, not a second real tool dispatch of the same call.
            assert curr.observation.startswith("(REPEATED CALL DETECTED"), (
                f"step {curr.step_number} re-dispatched an identical get_chunk call instead of "
                "being intercepted by the repeat-call guard"
            )
            consecutive_identical_dispatches += 1

    assert run.stop_reason != "max_steps_exceeded (6)" or consecutive_identical_dispatches == 0, (
        "the agent still burned its whole step budget on identical repeated calls"
    )
