#!/usr/bin/env python3
"""Confirm every manifest repo builds and passes its tests on JDK 8 inside the image.

This is protocol step 4. It reads the baseline logs recorded at image build time
(/opt/baselines/<id>.log) and compares tests run against the manifest; with --rerun it
re-executes the JDK 8 test run in a fresh container instead. A repo that fails here
must be removed from the manifest before `prereg/hash.sh`, and the removal logged as
a deviation.

    python scripts/verify_image.py tasks/pilot.yaml [--image legacybench/java-migration:pilot-v0] [--rerun]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from legacybench.manifest import Manifest  # noqa: E402
from legacybench.scorers.gates import build_success, parse_surefire  # noqa: E402


def docker_sh(image: str, cmd: str, timeout: int) -> str:
    res = subprocess.run(
        ["docker", "run", "--rm", "--network", "none", image, "bash", "-lc", cmd],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return (res.stdout or "") + (res.stderr or "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--image", default="legacybench/java-migration:pilot-v0")
    ap.add_argument("--rerun", action="store_true", help="re-run JDK 8 tests instead of reading build-time logs")
    args = ap.parse_args()

    m = Manifest.load(args.manifest)
    bad = 0
    print(f"{'task':60} {'build':6} {'tests_run':>9} {'baseline':>8} {'ok':>3}")
    for t in m.tasks:
        image_id = t.image_dir.split("/")[-1]
        if args.rerun:
            cmd = (
                f"cp -r {t.image_dir} /tmp/r && cd /tmp/r && export JAVA_HOME=$JAVA8_HOME && "
                "mvn -B -o org.jacoco:jacoco-maven-plugin:0.8.12:prepare-agent test 2>&1"
            )
            log = docker_sh(args.image, cmd, timeout=3600)
        else:
            log = docker_sh(args.image, f"cat /opt/baselines/{image_id}.log", timeout=120)
        ok_build = build_success(log)
        counts = parse_surefire(log)
        run = counts.tests_run if counts else -1
        ok = ok_build and counts is not None and counts.passed_all and run >= t.baseline.tests_run
        bad += 0 if ok else 1
        print(f"{t.id:60} {str(ok_build):6} {run:9d} {t.baseline.tests_run:8d} {'yes' if ok else 'NO':>3}")
    if bad:
        print(f"\n{bad} repo(s) do not reproduce their baseline inside the image. Remove them from the manifest and log the deviation.")
        return 1
    print("\nAll repos reproduce their JDK 8 baseline inside the image.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
