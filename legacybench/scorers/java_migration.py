"""Sandbox scorer for Java version migrations.

Collects evidence inside the task sandbox and hands it to gates.evaluate_gates.
The reference copy of the repository is baked into the image at /opt/repos/<id>
(read-only to the agent user), so test-file integrity is checked against the
original rather than against anything the agent could have touched.
"""

from __future__ import annotations

import json

from inspect_ai.scorer import Score, Target, accuracy, scorer, stderr
from inspect_ai.solver import TaskState
from inspect_ai.util import sandbox

from legacybench.scorers import gates

REPO = "/workspace/repo"
JACOCO = "org.jacoco:jacoco-maven-plugin:0.8.12"


async def _sh(cmd: str, timeout: int) -> tuple[str, int]:
    res = await sandbox().exec(["bash", "-lc", cmd], timeout=timeout)
    return (res.stdout or "") + (res.stderr or ""), res.returncode


@scorer(metrics=[accuracy(), stderr()])
def migration_gates(build_timeout: int = 1800, test_timeout: int = 3600, run_coverage: bool = True):
    async def score(state: TaskState, target: Target) -> Score:
        meta = state.metadata
        target_java = int(meta.get("target_java", 17))
        ref_dir = meta["image_dir"]
        java_home = f"$JAVA{target_java}_HOME"
        mvn = f"export JAVA_HOME={java_home}; export PATH=$JAVA_HOME/bin:$PATH; cd {REPO} && mvn -B -o"

        compile_log, _ = await _sh(f"{mvn} -q clean compile 2>&1; echo; mvn -B -o compile 2>&1 | tail -n 200", build_timeout)
        test_log: str | None = None
        if not gates.compilation_failed(compile_log) and "BUILD FAILURE" not in compile_log:
            test_log, _ = await _sh(f"{mvn} test 2>&1", test_timeout)

        before_out, _ = await _sh(f"cd {ref_dir} && find src/test -type f 2>/dev/null | sort | xargs -r sha256sum", 300)
        after_out, _ = await _sh(f"cd {REPO} && find src/test -type f 2>/dev/null | sort | xargs -r sha256sum", 300)
        tests_before = gates.parse_sha256sum(before_out)
        tests_after = gates.parse_sha256sum(after_out)

        od_out, _ = await _sh(
            f"cd {REPO} && find . -path '*/target/classes/*' -name '*.class' | head -n 500 | "
            "while read -r f; do od -An -tu1 -j6 -N2 \"$f\"; done",
            300,
        )
        majors = gates.parse_major_versions_from_od(od_out)

        cov_after = None
        if run_coverage and test_log and gates.build_success(test_log):
            await _sh(f"{mvn} {JACOCO}:prepare-agent test {JACOCO}:report 2>&1 | tail -n 50", test_timeout)
            xml_out, rc = await _sh(
                f"cd {REPO} && for f in $(find . -path '*/target/site/jacoco*/jacoco.xml'); do cat \"$f\"; echo '<<<SPLIT>>>'; done",
                120,
            )
            covered = missed = 0
            for chunk in xml_out.split("<<<SPLIT>>>"):
                chunk = chunk.strip()
                if not chunk:
                    continue
                try:
                    c, m = gates.parse_jacoco_xml(chunk)
                except Exception:
                    continue
                covered += c
                missed += m
            cov_after = gates.line_percent(covered, missed)

        result = gates.evaluate_gates(
            compile_log=compile_log,
            test_log=test_log,
            baseline_tests_run=int(meta.get("baseline_tests_run", 0)),
            class_majors=majors,
            target_java=target_java,
            cov_before=meta.get("baseline_cov_line_percent"),
            cov_after=cov_after,
            tests_before=tests_before,
            tests_after=tests_after,
            required=list(meta.get("required_gates", [])),
            cov_floor_relative=float(meta.get("cov_floor_relative", -0.05)),
        )
        result["solver_store"] = {k: v for k, v in state.store.items() if k.startswith("single_shot.")}
        return Score(
            value=1.0 if result["passed"] else 0.0,
            answer=json.dumps(result["gates"]),
            explanation=json.dumps(result["details"], default=str)[:4000],
            metadata=result,
        )

    return score
