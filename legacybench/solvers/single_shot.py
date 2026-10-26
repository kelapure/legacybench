"""Single-response arm.

The model sees the whole repository and must return the migrated repository in one
response using a fenced multi-file format. No tools, no feedback. This is the arm
that tests the one-shot thesis: it is deliberately handicapped by output caps, and
that handicap is the measurement.
"""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass, field

from inspect_ai.model import ChatMessageUser
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import sandbox

FILE_START = re.compile(r"^=== FILE: (.+?) ===\s*$")
FILE_END = re.compile(r"^=== END FILE ===\s*$")
DELETE_RE = re.compile(r"^=== DELETE: (.+?) ===\s*$")

REPO_ROOT = "/workspace/repo"

INCLUDE_PATTERNS = ("*.java", "pom.xml", "*.properties", "*.xml", "*.yml", "*.yaml", "*.gradle", "*.kt")
MAX_SNAPSHOT_CHARS = 2_500_000  # ~600K tokens; above this the task is out of range for any model


@dataclass
class ParsedResponse:
    files: dict[str, str] = field(default_factory=dict)
    deletes: list[str] = field(default_factory=list)
    truncated: bool = False
    errors: list[str] = field(default_factory=list)


def _safe_rel_path(p: str) -> str | None:
    p = p.strip().strip("`").strip()
    if not p or p.startswith("/") or p.startswith("\\"):
        return None
    norm = posixpath.normpath(p)
    if norm.startswith("..") or "/../" in norm or norm == ".":
        return None
    return norm


def parse_multi_file(text: str) -> ParsedResponse:
    """Parse the fenced multi-file format. Pure function, unit-tested."""
    out = ParsedResponse()
    cur: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        if cur is None:
            m = FILE_START.match(line)
            if m:
                path = _safe_rel_path(m.group(1))
                if path is None:
                    out.errors.append(f"unsafe path rejected: {m.group(1)!r}")
                    cur = "\0reject"
                else:
                    cur = path
                buf = []
                continue
            d = DELETE_RE.match(line)
            if d:
                path = _safe_rel_path(d.group(1))
                if path is None:
                    out.errors.append(f"unsafe delete rejected: {d.group(1)!r}")
                else:
                    out.deletes.append(path)
            continue
        if FILE_END.match(line):
            if cur != "\0reject":
                out.files[cur] = "\n".join(buf) + ("\n" if buf else "")
            cur = None
            buf = []
            continue
        buf.append(line)
    if cur is not None:
        out.truncated = True
        out.errors.append(f"unterminated file block: {cur!r}")
    return out


INSTRUCTIONS_ALL = """\
You are migrating a Java {source} Maven project to Java {target} in ONE response, with no tools and no follow-up.

Success is judged mechanically, in this order:
1. `mvn compile` succeeds on JDK {target}.
2. `mvn test` succeeds on JDK {target}: all existing tests pass.
3. Files under src/test are byte-for-byte unchanged (you may not edit, delete, or add tests).
4. The number of tests run is not lower than before ({tests_run}).
5. Compiled classes target JDK {target} (class-file major version {major}).
6. Line coverage does not fall more than 5% relative to the original.

Emit the COMPLETE migrated repository: every source and build file, in full, even files you did not change. \
Use exactly this format for each file, with nothing between blocks:

=== FILE: relative/path/from/repo/root ===
<entire file contents>
=== END FILE ===

To delete a file write a single line: === DELETE: relative/path ===
Do not use Markdown code fences. Do not write explanations. Start with the first file block immediately.
"""

INSTRUCTIONS_CHANGED = INSTRUCTIONS_ALL.replace(
    "Emit the COMPLETE migrated repository: every source and build file, in full, even files you did not change.",
    "Emit every file you change, in full. Files you do not emit are kept as they are.",
)


async def _snapshot_repo() -> tuple[str, int, int]:
    """Return a concatenated snapshot of the repository from the sandbox."""
    find = " -o ".join(f"-name '{p}'" for p in INCLUDE_PATTERNS)
    cmd = f"cd {REPO_ROOT} && find . -type f \\( {find} \\) -not -path './target/*' -not -path './.git/*' | sort"
    res = await sandbox().exec(["bash", "-lc", cmd], timeout=120)
    paths = [p.strip()[2:] for p in res.stdout.splitlines() if p.strip()]
    parts: list[str] = []
    total = 0
    for rel in paths:
        content = await sandbox().read_file(f"{REPO_ROOT}/{rel}")
        parts.append(f"=== FILE: {rel} ===\n{content.rstrip()}\n=== END FILE ===\n")
        total += len(content)
        if total > MAX_SNAPSHOT_CHARS:
            break
    return "".join(parts), len(paths), total


@solver
def single_shot(emit_all_files: bool = True) -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        meta = state.metadata
        instr = (INSTRUCTIONS_ALL if emit_all_files else INSTRUCTIONS_CHANGED).format(
            source=meta.get("source_java", 8),
            target=meta.get("target_java", 17),
            tests_run=meta.get("baseline_tests_run", "unknown"),
            major=44 + int(meta.get("target_java", 17)),
        )
        snapshot, n_files, n_chars = await _snapshot_repo()
        state.store.set("single_shot.snapshot_files", n_files)
        state.store.set("single_shot.snapshot_chars", n_chars)
        state.messages = [
            ChatMessageUser(content=instr + "\nHere is the repository:\n\n" + snapshot)
        ]
        state = await generate(state)

        parsed = parse_multi_file(state.output.completion or "")
        written = 0
        for rel, content in parsed.files.items():
            await sandbox().write_file(f"{REPO_ROOT}/{rel}", content)
            written += 1
        for rel in parsed.deletes:
            await sandbox().exec(["rm", "-f", f"{REPO_ROOT}/{rel}"], timeout=30)
        usage = state.output.usage
        state.store.set("single_shot.files_written", written)
        state.store.set("single_shot.files_deleted", len(parsed.deletes))
        state.store.set("single_shot.truncated", parsed.truncated)
        state.store.set("single_shot.stop_reason", state.output.stop_reason)
        state.store.set("single_shot.parse_errors", parsed.errors)
        state.store.set("single_shot.output_tokens", getattr(usage, "output_tokens", None) if usage else None)
        state.store.set("single_shot.reasoning_tokens", getattr(usage, "reasoning_tokens", None) if usage else None)
        state.store.set("single_shot.emit_all_files", emit_all_files)
        return state

    return solve
