"""Agentic arm: one shared minimal scaffold for every model.

Shell plus file editor, nothing model-specific. The sandbox has JDK 8 and 17 and an
offline Maven repository, so the agent can build and run tests itself. Caps on
messages, tokens, time and dollars are the pilot's budget enforcement.
"""

from __future__ import annotations

from inspect_ai.solver import Solver, basic_agent, system_message
from inspect_ai.tool import bash, text_editor

SYSTEM = """\
You are migrating the Java {source} Maven project at /workspace/repo to Java {target}.
JDK {source} is at $JAVA{source}_HOME and JDK {target} at $JAVA{target}_HOME; Maven is on PATH and works offline (-o).

Success is judged mechanically after you submit:
1. `mvn compile` succeeds on JDK {target}.
2. `mvn test` succeeds on JDK {target}: all existing tests pass.
3. Files under src/test are byte-for-byte unchanged. Do not edit, delete, or add tests.
4. The number of tests run is not lower than before ({tests_run}).
5. Compiled classes target JDK {target}.
6. Line coverage does not fall more than 5% relative to the original.

Work in the sandbox with the tools. When the build and tests pass on JDK {target}, call submit().
If you cannot finish, submit anyway with a one-line note of what is left; partial work is scored as it stands.
"""


def agentic(message_limit: int = 120, token_limit: int | str | None = "2m", bash_timeout: int = 900) -> Solver:
    return basic_agent(
        init=system_message(SYSTEM),
        tools=[bash(timeout=bash_timeout, user="agent"), text_editor(timeout=120, user="agent")],
        message_limit=message_limit,
        token_limit=token_limit,
        submit_description="Submit the migrated repository for mechanical grading.",
    )
