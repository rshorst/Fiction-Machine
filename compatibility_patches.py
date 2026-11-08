"""
CrewAI compatibility patches for Claude 4.x.

Import this module before any CrewAI imports in run scripts. The patches
apply at import time and are idempotent.

Upstream issue: CrewAI's handle_max_iterations_exceeded() appends an
assistant-role message to the conversation before making a final LLM call
to force task conclusion. Claude 4.x (claude-opus-4-7, claude-sonnet-4-6,
claude-haiku-4-5) rejects this pattern with HTTP 400:
"This model does not support assistant message prefill."

This is a known CrewAI / Claude 4.x compatibility gap. Remove this file
and its imports from the run scripts when CrewAI ships a fix upstream.
Track at: https://github.com/crewAIInc/crewAI/issues
"""

# ── Patch: handle_max_iterations_exceeded role="assistant" → role="user" ──────
#
# What:  replaces the assistant-prefill message with a user-role message in the
#        force-final-answer fallback that fires when an agent hits max_iter.
# Why:   Claude 4.x API rejects any conversation whose last message has
#        role="assistant" (the assistant-prefill pattern). The original code
#        appends role="assistant" before calling llm.call(), which crashes the
#        pipeline with a 400 error every time any agent hits its max_iter limit.
# Fix:   change role="assistant" to role="user". The force_final_answer content
#        reads naturally as a user instruction either way.
# When to remove: when CrewAI's handle_max_iterations_exceeded no longer uses
#        role="assistant". Verify by grepping for "role.*assistant" in
#        crewai/utilities/agent_utils.py.

try:
    from crewai.utilities import agent_utils as _agent_utils
    from crewai.agents import crew_agent_executor as _crew_exec

    def _patched_handle_max(
        formatted_answer, printer, i18n, messages, llm, callbacks, verbose=True
    ):
        if verbose:
            printer.print(
                content="Maximum iterations reached. Requesting final answer.",
                color="yellow",
            )
        if formatted_answer and hasattr(formatted_answer, "text"):
            force_msg = formatted_answer.text + f"\n{i18n.errors('force_final_answer')}"
        else:
            force_msg = i18n.errors("force_final_answer")

        # role="user" — Claude 4.x rejects assistant prefill
        messages.append(_agent_utils.format_message_for_llm(force_msg, role="user"))
        answer = llm.call(messages, callbacks=callbacks)

        if answer is None or answer == "":
            if verbose:
                printer.print(
                    content="Received None or empty response from LLM call.",
                    color="red",
                )
            raise ValueError("Invalid response from LLM call - None or empty.")

        from crewai.agents.parser import AgentFinish as _AgentFinish
        formatted = _agent_utils.format_answer(answer=answer)
        if isinstance(formatted, _AgentFinish):
            return formatted
        return _AgentFinish(
            thought=formatted.thought,
            output=formatted.text,
            text=formatted.text,
        )

    _agent_utils.handle_max_iterations_exceeded = _patched_handle_max
    _crew_exec.handle_max_iterations_exceeded = _patched_handle_max
    print("Applied CrewAI compatibility patch (handle_max_iterations_exceeded for Claude 4.x)")

except Exception:
    pass
