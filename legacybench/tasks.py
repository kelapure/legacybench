"""Inspect task definitions for the pilot.

    inspect eval legacybench/tasks.py@pilot_single_shot --model anthropic/claude-fable-5-1 \
        -T strata=S,M,L --cost-limit 9 --log-dir logs/
    inspect eval legacybench/tasks.py@pilot_agentic --model google/gemini-4-argon \
        -T strata=S,M,L,B --cost-limit 1.5 --log-dir logs/

Both tasks read tasks/pilot.yaml. Model prices are registered from prices.yaml at
import so --cost-limit is enforced per sample; a model with an incomplete price
entry is refused.
"""

from __future__ import annotations

from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample

from legacybench.ledger import register_costs_with_inspect
from legacybench.manifest import Manifest, Stratum, parse_strata
from legacybench.manifest import Task as ManifestTask
from legacybench.scorers.java_migration import migration_gates
from legacybench.solvers.agentic import agentic
from legacybench.solvers.single_shot import single_shot

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "tasks" / "pilot.yaml"
COMPOSE = str(ROOT / "docker" / "compose.yaml")

UNPRICED_MODELS = register_costs_with_inspect()

SETUP_SH = """\
set -e
mkdir -p /workspace
rm -rf /workspace/repo
cp -r {image_dir} /workspace/repo
chown -R agent:agent /workspace/repo
chmod -R a-w {image_dir} || true
"""

USER_PROMPT = (
    "Migrate the Maven project in /workspace/repo from Java {source} to Java {target}. "
    "Build and tests must pass on JDK {target}; tests must not be modified."
)


def _sample(t: ManifestTask) -> Sample:
    return Sample(
        id=t.id,
        input=USER_PROMPT.format(source=t.source_java, target=t.target_java),
        target="all gates pass",
        setup=SETUP_SH.format(image_dir=t.image_dir),
        metadata={
            "id": t.id,
            "repo": t.repo,
            "commit": t.commit,
            "stratum": t.stratum.value,
            "capability": t.capability,
            "source_java": t.source_java,
            "target_java": t.target_java,
            "image_dir": t.image_dir,
            "baseline_tests_run": t.baseline.tests_run,
            "baseline_cov_line_percent": t.baseline.cov_line_percent,
            "required_gates": t.oracle.required_gates,
            "cov_floor_relative": t.oracle.coverage_floor_relative,
            "est_output_tokens": t.size.est_output_tokens,
            "loc": t.size.loc,
        },
    )


def _dataset(manifest_path: str, strata: str, arm: str) -> MemoryDataset:
    m = Manifest.load(manifest_path)
    tasks = m.by_strata(parse_strata(strata), arm=arm)  # type: ignore[arg-type]
    if not tasks:
        raise ValueError(f"no tasks for strata={strata!r} arm={arm!r} in {manifest_path}")
    return MemoryDataset([_sample(t) for t in tasks], name=f"{m.version}-{arm}")


@task
def pilot_single_shot(
    manifest: str = str(DEFAULT_MANIFEST),
    strata: str = "S,M,L",
    emit_all_files: bool = True,
    arm: str = "single_shot",
) -> Task:
    m = Manifest.load(manifest)
    lim = m.default_limits["single_shot"]
    return Task(
        dataset=_dataset(manifest, strata, "single_shot"),
        solver=single_shot(emit_all_files=emit_all_files),
        scorer=migration_gates(),
        sandbox=("docker", COMPOSE),
        message_limit=lim.messages,
        token_limit=lim.tokens,
        time_limit=lim.time_s,
        fail_on_error=False,
        name="pilot_single_shot",
        version="pilot-v0",
    )


@task
def pilot_agentic(
    manifest: str = str(DEFAULT_MANIFEST),
    strata: str = "S,M,L,B",
    arm: str = "agentic",
) -> Task:
    m = Manifest.load(manifest)
    lim = m.default_limits["agentic"]
    return Task(
        dataset=_dataset(manifest, strata, "agentic"),
        solver=agentic(message_limit=lim.messages, token_limit=lim.tokens),
        scorer=migration_gates(),
        sandbox=("docker", COMPOSE),
        time_limit=lim.time_s,
        fail_on_error=False,
        name="pilot_agentic",
        version="pilot-v0",
    )


__all__ = ["pilot_single_shot", "pilot_agentic", "UNPRICED_MODELS", "Stratum"]
