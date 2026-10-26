from pathlib import Path

import pytest
from pydantic import ValidationError

from legacybench.manifest import Manifest, Stratum, Task, parse_strata

ROOT = Path(__file__).resolve().parents[1]


def _task(**over):
    base = dict(
        id="freshbrew/x__y",
        capability="upgrade_in_place",
        benchmark_of_origin="FreshBrew",
        repo="x/y",
        commit="a" * 40,
        license="MIT",
        commit_date="2020-01-01",
        size={"loc": 100, "java_files": 2, "est_output_tokens": 1000},
        stratum="S",
        baseline={"tests_run": 3},
        arms=["single_shot", "agentic"],
    )
    base.update(over)
    return base


def test_task_validates_and_image_dir():
    t = Task.model_validate(_task())
    assert t.image_dir == "/opt/repos/freshbrew__x__y"
    assert t.oracle.coverage_floor_relative == -0.05


def test_rejects_short_sha_and_missing_stratum():
    with pytest.raises(ValidationError):
        Task.model_validate(_task(commit="abc123"))
    bad = _task()
    del bad["stratum"]
    with pytest.raises(ValidationError):
        Task.model_validate(bad)


def test_duplicate_ids_rejected():
    with pytest.raises(ValidationError):
        Manifest.model_validate(
            dict(
                version="v",
                created="2026-10-26",
                source_dataset="s",
                selection_rule="r",
                default_limits={"agentic": {"cost_usd": 1, "tokens": 1, "messages": 1, "time_s": 1}},
                tasks=[_task(), _task()],
            )
        )


def test_pilot_manifest_loads_and_has_expected_shape():
    m = Manifest.load(ROOT / "tasks" / "pilot.yaml")
    assert len(m.tasks) == 16
    assert len(m.by_strata({Stratum.S, Stratum.M, Stratum.L}, arm="single_shot")) == 6
    assert len(m.by_strata({Stratum.B}, arm="agentic")) == 10
    assert all(t.license in {"MIT", "Apache-2.0", "BSD-3-Clause"} for t in m.tasks)
    assert all(t.baseline.tests_run >= 10 for t in m.tasks)
    assert parse_strata("s, m") == {Stratum.S, Stratum.M}
