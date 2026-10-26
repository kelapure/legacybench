"""Output-ceiling probe.

Asks each model for an artifact of known length that can be checked mechanically,
and records how much it actually produced, why it stopped, how many reasoning
tokens it spent, and how fast it decoded. This is the direct test of the LinkedIn
post's Claim A (documented caps vs. real caps). One call per length per model.

    inspect eval legacybench/probe/ceiling.py --model google/gemini-4-argon \
        -T lengths=2000,8000,20000,60000 --max-tokens 1048576 --cost-limit 12

Each function line is about 14 tokens, so 2,000 / 8,000 / 20,000 / 60,000 functions
are roughly 28K / 115K / 290K / 870K output tokens: under every cap, at the 128K cap,
above it, and near 1M.
"""

from __future__ import annotations

import ast
import re

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.scorer import Score, Target, mean, scorer
from inspect_ai.solver import TaskState, generate

LINE_RE = re.compile(r"^def f_(\d{5})\(x\):\s*return x \+ (\d+)\s*$")

PROMPT = (
    "Output exactly {n} Python function definitions and nothing else: no prose, no "
    "code fences, no blank lines, no comments. Function k (for k from 1 to {n}) must be "
    "written on a single line exactly as:\n"
    "def f_{{k:05d}}(x): return x + {{k}}\n"
    "For example the first two lines are:\n"
    "def f_00001(x): return x + 1\n"
    "def f_00002(x): return x + 2\n"
    "Continue in order until f_{n:05d}. Do not stop early and do not summarize."
)


def parse_probe_output(text: str, n: int) -> dict:
    """Pure function: count well-formed, in-order lines and check the whole thing parses."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    valid = 0
    in_order = True
    for i, ln in enumerate(lines, start=1):
        m = LINE_RE.match(ln.strip())
        if not m:
            break
        k, add = int(m.group(1)), int(m.group(2))
        if k != i or add != i:
            in_order = False
            break
        valid += 1
    try:
        ast.parse("\n".join(lines[:valid]))
        parses = True
    except SyntaxError:
        parses = False
    return {
        "requested": n,
        "valid_lines": valid,
        "total_lines": len(lines),
        "in_order": in_order,
        "parses": parses,
        "fraction": valid / n if n else 0.0,
        "complete": valid >= n,
    }


@scorer(metrics=[mean()])
def ceiling_scorer():
    async def score(state: TaskState, target: Target) -> Score:
        n = int(state.metadata["n_functions"])
        result = parse_probe_output(state.output.completion or "", n)
        usage = state.output.usage
        meta = {
            **result,
            "stop_reason": state.output.stop_reason,
            "output_tokens": getattr(usage, "output_tokens", None) if usage else None,
            "reasoning_tokens": getattr(usage, "reasoning_tokens", None) if usage else None,
            "input_tokens": getattr(usage, "input_tokens", None) if usage else None,
            "generation_time_s": state.output.time,
            "error": str(state.output.error) if state.output.error else None,
        }
        if meta["output_tokens"] and meta["generation_time_s"]:
            meta["decode_tokens_per_s"] = meta["output_tokens"] / meta["generation_time_s"]
        return Score(value=result["fraction"], answer=str(result["valid_lines"]), metadata=meta)

    return score


@task
def output_ceiling(lengths: str = "2000,8000,20000,60000") -> Task:
    ns = [int(x) for x in str(lengths).split(",") if x.strip()]
    samples = [
        Sample(
            id=f"probe-{n}",
            input=PROMPT.format(n=n),
            target=str(n),
            metadata={"n_functions": n, "approx_output_tokens": n * 14},
        )
        for n in ns
    ]
    return Task(
        dataset=MemoryDataset(samples),
        solver=generate(),
        scorer=ceiling_scorer(),
        fail_on_error=False,  # a provider rejecting max_tokens above its cap is a finding, not a crash
        name="output_ceiling",
    )
