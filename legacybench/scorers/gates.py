"""Pure functions behind the Java migration gates.

Everything here is testable without Docker. The scorer in java_migration.py only
collects raw evidence from the sandbox and calls these.

Gate definitions follow MigrationBench (arXiv 2505.09569) and FreshBrew
(arXiv 2510.04852):
- build and tests pass on the target JDK
- test files unchanged (MigrationBench hashes src/test; this is the strict form)
- number of tests run non-decreasing
- compiled class major version matches the target (52 = Java 8, 61 = Java 17, 65 = Java 21)
- FreshBrew coverage guard: cov_after / cov_before - 1 > -0.05 (relative, not points)
"""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

SUREFIRE_RE = re.compile(r"Tests run:\s*(\d+),\s*Failures:\s*(\d+),\s*Errors:\s*(\d+),\s*Skipped:\s*(\d+)")
RESULTS_RE = re.compile(r"\[INFO\] Results:\n(.*?)(?:\n\[INFO\] -{10,}|\Z)", re.S)
COMPILER_FAIL_RE = re.compile(r"Failed to execute goal org\.apache\.maven\.plugins:maven-compiler-plugin:[^:]+:compile")


@dataclass(frozen=True)
class TestCounts:
    tests_run: int
    failures: int
    errors: int
    skipped: int

    @property
    def passed_all(self) -> bool:
        return self.failures == 0 and self.errors == 0


def build_success(log: str) -> bool:
    return "BUILD SUCCESS" in log and "BUILD FAILURE" not in log and "[FATAL]" not in log


def compilation_failed(log: str) -> bool:
    return bool(COMPILER_FAIL_RE.search(log))


def parse_surefire(log: str) -> TestCounts | None:
    """Sum the per-class Surefire lines, as FreshBrew's verifier does.

    Surefire also prints a 'Results:' summary; summing per-class lines double counts
    when that summary is present, so prefer the summary block when it exists.
    """
    summary = RESULTS_RE.search(log)
    if summary:
        m = SUREFIRE_RE.search(summary.group(1))
        if m:
            return TestCounts(*map(int, m.groups()))
    matches = SUREFIRE_RE.findall(log)
    if not matches:
        return None
    t = [0, 0, 0, 0]
    for m in matches:
        for i, v in enumerate(m):
            t[i] += int(v)
    return TestCounts(*t)


def class_major_version(class_bytes: bytes) -> int | None:
    """Major version lives at bytes 6-7 of a .class file (after 0xCAFEBABE and minor)."""
    if len(class_bytes) < 8 or class_bytes[:4] != b"\xca\xfe\xba\xbe":
        return None
    return int.from_bytes(class_bytes[6:8], "big")


def parse_major_versions_from_od(od_output: str) -> list[int]:
    """Parse `od -An -tu1 -j6 -N2 file` output lines ('  0  61') into major versions."""
    out = []
    for line in od_output.splitlines():
        parts = line.split()
        if len(parts) == 2 and all(p.isdigit() for p in parts):
            out.append(int(parts[0]) * 256 + int(parts[1]))
    return out


def target_major(java_version: int) -> int:
    return 44 + java_version


def parse_jacoco_xml(xml_text: str) -> tuple[int, int]:
    """Return (covered, missed) LINE counters from a jacoco.xml report root element."""
    root = ET.fromstring(xml_text)
    covered = missed = 0
    for counter in root.findall("./counter"):
        if counter.get("type") == "LINE":
            covered += int(counter.get("covered", 0))
            missed += int(counter.get("missed", 0))
    return covered, missed


def line_percent(covered: int, missed: int) -> float | None:
    total = covered + missed
    return (covered / total * 100.0) if total else None


def coverage_guard(before_pct: float | None, after_pct: float | None, floor_relative: float = -0.05) -> bool | None:
    """FreshBrew rule. None when it cannot be evaluated (no baseline or no report)."""
    if before_pct is None or after_pct is None:
        return None
    if before_pct == 0:
        return after_pct >= 0
    return (after_pct / before_pct - 1.0) > floor_relative


def fingerprint(files: dict[str, bytes]) -> dict[str, str]:
    return {path: hashlib.sha256(data).hexdigest() for path, data in files.items()}


def parse_sha256sum(output: str, strip_prefix: str = "") -> dict[str, str]:
    """Parse `sha256sum` output into {relative_path: hash}."""
    out: dict[str, str] = {}
    for line in output.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2 or len(parts[0]) != 64:
            continue
        path = parts[1].lstrip("*")
        if strip_prefix and path.startswith(strip_prefix):
            path = path[len(strip_prefix):]
        out[path.lstrip("./")] = parts[0]
    return out


def unchanged_test_files(before: dict[str, str], after: dict[str, str]) -> tuple[bool, dict[str, list[str]]]:
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    modified = sorted(p for p in set(before) & set(after) if before[p] != after[p])
    ok = not (added or removed or modified)
    return ok, {"added": added, "removed": removed, "modified": modified}


TEST_METHOD_RE = re.compile(r"@(?:org\.junit(?:\.jupiter\.api)?\.)?Test\b[^\n]*\n(?:\s*@[^\n]*\n)*\s*(?:public\s+)?(?:static\s+)?[\w<>\[\], ]+\s+(\w+)\s*\(")


def extract_test_method_names(java_source: str) -> set[str]:
    """Softer gate: names of @Test methods. Reported, not primary."""
    return set(TEST_METHOD_RE.findall(java_source))


def evaluate_gates(
    *,
    compile_log: str,
    test_log: str | None,
    baseline_tests_run: int,
    class_majors: list[int],
    target_java: int,
    cov_before: float | None,
    cov_after: float | None,
    tests_before: dict[str, str],
    tests_after: dict[str, str],
    required: list[str],
    cov_floor_relative: float = -0.05,
) -> dict:
    """Combine evidence into per-gate results and an overall pass under `required`."""
    gates: dict[str, bool | None] = {}
    details: dict[str, object] = {}

    gates["build"] = (not compilation_failed(compile_log)) and ("BUILD FAILURE" not in compile_log)
    counts = parse_surefire(test_log) if test_log else None
    gates["tests_pass"] = bool(test_log) and build_success(test_log) and counts is not None and counts.passed_all
    details["test_counts"] = counts.__dict__ if counts else None

    unchanged, diff = unchanged_test_files(tests_before, tests_after)
    gates["test_files_unchanged"] = unchanged
    details["test_file_diff"] = diff

    gates["test_count_non_decreasing"] = counts is not None and counts.tests_run >= baseline_tests_run
    details["baseline_tests_run"] = baseline_tests_run

    tm = target_major(target_java)
    gates["class_major_version"] = bool(class_majors) and all(m >= tm for m in class_majors)
    details["class_majors_observed"] = sorted(set(class_majors))

    gates["coverage_guard"] = coverage_guard(cov_before, cov_after, cov_floor_relative)
    details["cov_before"] = cov_before
    details["cov_after"] = cov_after

    passed = all(gates.get(g) is True for g in required)
    return {"passed": passed, "gates": gates, "details": details, "required": required}
