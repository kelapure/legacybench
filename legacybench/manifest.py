"""Task manifest schema.

Every task the harness runs is described here first. The manifest is part of the
pre-registration: its hash is recorded before any scored run, and the analysis
only reads tasks that are in it.
"""

from __future__ import annotations

import re
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

Capability = Literal[
    "comprehension",
    "translation",
    "upgrade_in_place",
    "test_generation",
    "agentic_repo",
]
Arm = Literal["single_shot", "agentic"]
Split = Literal["public", "post_cutoff"]

TOKENS_PER_JAVA_LOC = 10
"""Assumed tokens per Java line of code for output-size strata.

An assumption, not a measurement. The pilot's single-shot arm measures the real
ratio (output tokens / lines emitted) and the manifest generator should be re-run
with the measured value before the full study is registered.
"""


class Stratum(str, Enum):
    S = "S"  # small, target output well under every model's cap
    M = "M"  # medium, approaching the smallest documented cap
    L = "L"  # large, exceeds a 128K-token output cap when emitted in full
    B = "B"  # breadth sample, agentic arm only, for variance and cost


class SizeInfo(BaseModel):
    loc: int = Field(ge=0)
    java_files: int = Field(ge=0)
    est_output_tokens: int = Field(ge=0)


class Baseline(BaseModel):
    """Oracle facts about the unmodified repository."""

    tests_run: int = Field(ge=0)
    cov_line_percent: float | None = Field(default=None, ge=0, le=100)
    cov_line_total: int | None = Field(default=None, ge=0)


class Oracle(BaseModel):
    type: Literal["executable_tests"] = "executable_tests"
    required_gates: list[str] = Field(
        default_factory=lambda: [
            "build",
            "tests_pass",
            "test_files_unchanged",
            "test_count_non_decreasing",
            "class_major_version",
            "coverage_guard",
        ]
    )
    coverage_floor_relative: float = -0.05
    """FreshBrew rule: (cov_after / cov_before) - 1 must exceed this value.

    This is a relative change, not percentage points.
    """


class Validation(BaseModel):
    status: Literal["unvalidated", "validated", "rejected"] = "unvalidated"
    annotators: int = 0
    notes: str = ""


class Limits(BaseModel):
    """Per-sample caps. Hard caps are what make a $200 budget enforceable."""

    cost_usd: float = Field(gt=0)
    tokens: int = Field(gt=0)
    messages: int = Field(gt=0)
    time_s: int = Field(gt=0)


class Task(BaseModel):
    id: str
    capability: Capability
    benchmark_of_origin: str
    repo: str
    commit: str
    license: str
    commit_date: date
    source_java: int = 8
    target_java: int = 17
    size: SizeInfo
    stratum: Stratum
    split: Split = "public"
    baseline: Baseline
    oracle: Oracle = Field(default_factory=Oracle)
    validation: Validation = Field(default_factory=Validation)
    existing_port_known: bool = False
    arms: list[Arm]

    @field_validator("commit")
    @classmethod
    def _full_sha(cls, v: str) -> str:
        if not re.fullmatch(r"[0-9a-f]{40}", v):
            raise ValueError("commit must be a full 40-hex SHA")
        return v

    @field_validator("id")
    @classmethod
    def _safe_id(cls, v: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_.\-/]+", v) or ".." in v:
            raise ValueError("id contains unsafe characters")
        return v

    @property
    def image_dir(self) -> str:
        """Directory inside the sandbox image where the repo is baked at build time."""
        return "/opt/repos/" + self.id.replace("/", "__")


class Manifest(BaseModel):
    version: str
    created: date
    source_dataset: str
    selection_rule: str
    default_limits: dict[Arm, Limits]
    tasks: list[Task]

    @model_validator(mode="after")
    def _unique_ids(self) -> "Manifest":
        ids = [t.id for t in self.tasks]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            raise ValueError(f"duplicate task ids: {sorted(dupes)}")
        return self

    def by_strata(self, strata: set[Stratum] | None, arm: Arm | None = None) -> list[Task]:
        out = []
        for t in self.tasks:
            if strata is not None and t.stratum not in strata:
                continue
            if arm is not None and arm not in t.arms:
                continue
            out.append(t)
        return out

    @classmethod
    def load(cls, path: str | Path) -> "Manifest":
        with open(path) as f:
            return cls.model_validate(yaml.safe_load(f))

    def dump(self, path: str | Path) -> None:
        data = self.model_dump(mode="json")
        with open(path, "w") as f:
            yaml.safe_dump(data, f, sort_keys=False)


def parse_strata(spec: str) -> set[Stratum]:
    return {Stratum(s.strip().upper()) for s in spec.split(",") if s.strip()}
