#!/usr/bin/env python3
"""Build tasks/pilot.yaml from FreshBrew's dataset files.

Selection is by explicit repo list and size stratum so that the manifest is
reproducible from the upstream data. Run:

    python scripts/build_pilot_manifest.py --freshbrew /path/to/freshbrew --out tasks/pilot.yaml

FreshBrew: https://github.com/mrcabbage972/freshbrew (Apache-2.0). Repos in it are
MIT / Apache-2.0 / BSD-licensed Java 8 Maven projects that fail to build on JDK 17.
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from legacybench.manifest import (  # noqa: E402
    TOKENS_PER_JAVA_LOC,
    Baseline,
    Limits,
    Manifest,
    SizeInfo,
    Stratum,
    Task,
)

# Two repos per single-shot stratum, ten for the breadth sample. Chosen from
# FreshBrew's full_dataset.yaml among single-module repos with >= 10 tests run.
# S: full emission ~12-15K output tokens. M: ~50K. L: ~140-150K, which exceeds a
# 128K output cap when the whole repository is emitted in one response.
PILOT_REPOS: dict[str, Stratum] = {
    "JakeWharton/DiskLruCache": Stratum.S,
    "AdRoll/cantor": Stratum.S,
    "square/javapoet": Stratum.M,
    "vincentrussell/sql-to-mongo-db-query-converter": Stratum.M,
    "perwendel/spark": Stratum.L,
    "julienchastang/charts4j": Stratum.L,
    "NetherlandsForensicInstitute/kafka-spout": Stratum.B,
    "Netflix/Surus": Stratum.B,
    "vbauer/caesar": Stratum.B,
    "jamesmorgan/ReloadablePropertiesAnnotation": Stratum.B,
    "mongobee/mongobee": Stratum.B,
    "jirutka/rsql-parser": Stratum.B,
    "rkapsi/patricia-trie": Stratum.B,
    "alibaba/spring-context-support": Stratum.B,
    "awslabs/dynamodb-streams-kinesis-adapter": Stratum.B,
    "HiveRunner/HiveRunner": Stratum.B,
}

DEFAULT_LIMITS = {
    # Caps chosen so the whole pilot fits in ~$200 at today's prices. Fable 5.1 is
    # roughly 4x the per-token price of the other three; the per-model override
    # lives in the workflow, these are the ceilings.
    "single_shot": Limits(cost_usd=9.0, tokens=1_500_000, messages=4, time_s=5400),
    "agentic": Limits(cost_usd=5.0, tokens=2_000_000, messages=120, time_s=3600),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freshbrew", required=True, help="path to a freshbrew checkout")
    ap.add_argument("--out", default="tasks/pilot.yaml")
    args = ap.parse_args()

    fb = Path(args.freshbrew)
    dataset = yaml.safe_load((fb / "data/migration_datasets/full_dataset.yaml").read_text())
    cov = {
        r["repo"]: r
        for r in csv.DictReader((fb / "data/migration_datasets/cov_data.csv").open())
    }

    tasks: list[Task] = []
    for rec in dataset:
        name = rec["repo_name"]
        if name not in PILOT_REPOS:
            continue
        stratum = PILOT_REPOS[name]
        feats = rec["repo_features"]
        covrow = cov.get(name.replace("/", "_"), {})
        cov_pct = float(covrow["percent_before"]) if covrow.get("percent_before") else None
        cov_total = int(float(covrow["total_before"])) if covrow.get("total_before") else None
        tests_run = (rec.get("test_count") or {}).get("tests_run") or feats["number_of_unit_tests"]
        arms = ["agentic"] if stratum == Stratum.B else ["single_shot", "agentic"]
        tasks.append(
            Task(
                id="freshbrew/" + name.replace("/", "__"),
                capability="upgrade_in_place",
                benchmark_of_origin="FreshBrew (arXiv 2510.04852) with MigrationBench gates (arXiv 2505.09569)",
                repo=name,
                commit=rec["commit"],
                license=rec["license"],
                commit_date=date.fromisoformat(rec["commit_date"][:10]),
                size=SizeInfo(
                    loc=feats["number_of_lines_of_code"],
                    java_files=feats["number_of_java_files"],
                    est_output_tokens=feats["number_of_lines_of_code"] * TOKENS_PER_JAVA_LOC,
                ),
                stratum=stratum,
                baseline=Baseline(tests_run=tests_run, cov_line_percent=cov_pct, cov_line_total=cov_total),
                arms=arms,
            )
        )

    missing = set(PILOT_REPOS) - {t.repo for t in tasks}
    if missing:
        sys.exit(f"repos not found in FreshBrew dataset: {sorted(missing)}")

    order = {Stratum.S: 0, Stratum.M: 1, Stratum.L: 2, Stratum.B: 3}
    tasks.sort(key=lambda t: (order[t.stratum], t.size.loc))

    manifest = Manifest(
        version="pilot-v0",
        created=date.today(),
        source_dataset="FreshBrew data/migration_datasets/full_dataset.yaml + cov_data.csv",
        selection_rule=(
            "Single-module Java 8 Maven repos with >= 10 tests run; two per size stratum "
            f"(S/M/L by LOC, est_output_tokens = LOC x {TOKENS_PER_JAVA_LOC}) for the single-shot "
            "and agentic arms; ten small-to-medium repos (B) for the agentic breadth sample."
        ),
        default_limits=DEFAULT_LIMITS,
        tasks=tasks,
    )
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    manifest.dump(args.out)
    print(f"wrote {len(tasks)} tasks to {args.out}")


if __name__ == "__main__":
    main()
