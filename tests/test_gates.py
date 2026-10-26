from legacybench.scorers.gates import (
    class_major_version,
    compilation_failed,
    coverage_guard,
    evaluate_gates,
    parse_jacoco_xml,
    parse_major_versions_from_od,
    parse_sha256sum,
    parse_surefire,
    target_major,
    unchanged_test_files,
    extract_test_method_names,
)

SUREFIRE_LOG = """
[INFO] Running com.example.ATest
[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.1 s
[INFO] Running com.example.BTest
[INFO] Tests run: 2, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 0.1 s
[INFO]
[INFO] Results:
[INFO]
[ERROR] Failures:
[INFO]
[ERROR] Tests run: 5, Failures: 1, Errors: 0, Skipped: 0
[INFO]
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
"""


def test_parse_surefire_prefers_results_block():
    c = parse_surefire(SUREFIRE_LOG)
    assert (c.tests_run, c.failures, c.errors, c.skipped) == (5, 1, 0, 0)
    assert not c.passed_all


def test_parse_surefire_sums_without_results_block():
    log = "Tests run: 3, Failures: 0, Errors: 0, Skipped: 0\nTests run: 4, Failures: 0, Errors: 0, Skipped: 1\n"
    c = parse_surefire(log)
    assert c.tests_run == 7 and c.skipped == 1 and c.passed_all


def test_compilation_failure_detection():
    assert compilation_failed("[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.8.1:compile (default-compile)")
    assert not compilation_failed("[INFO] BUILD SUCCESS")


def test_class_major_version():
    header = b"\xca\xfe\xba\xbe" + (0).to_bytes(2, "big") + (61).to_bytes(2, "big") + b"\x00" * 8
    assert class_major_version(header) == 61
    assert class_major_version(b"not a class") is None
    assert target_major(17) == 61 and target_major(8) == 52 and target_major(21) == 65


def test_parse_od_output():
    assert parse_major_versions_from_od("   0  61\n   0  52\n") == [61, 52]


def test_jacoco_and_coverage_guard():
    xml = """<report name="x"><package name="p"><counter type="LINE" missed="5" covered="5"/></package>
    <counter type="INSTRUCTION" missed="1" covered="1"/><counter type="LINE" missed="20" covered="80"/></report>"""
    covered, missed = parse_jacoco_xml(xml)
    assert (covered, missed) == (80, 20)  # only root-level counters
    assert coverage_guard(80.0, 77.0) is True   # -3.75% relative
    assert coverage_guard(80.0, 75.0) is False  # exactly -6.25% relative
    assert coverage_guard(80.0, 76.0) is False  # -5.0% is not > -0.05
    assert coverage_guard(None, 70.0) is None


def test_test_file_fingerprints():
    before = parse_sha256sum("a" * 64 + "  src/test/java/ATest.java\n" + "b" * 64 + "  src/test/java/BTest.java\n")
    after = parse_sha256sum("a" * 64 + "  src/test/java/ATest.java\n" + "c" * 64 + "  src/test/java/BTest.java\n" + "d" * 64 + "  src/test/java/New.java\n")
    ok, diff = unchanged_test_files(before, after)
    assert not ok
    assert diff["modified"] == ["src/test/java/BTest.java"] and diff["added"] == ["src/test/java/New.java"]
    assert unchanged_test_files(before, dict(before))[0]


def test_test_method_names():
    src = """
    @Test
    public void addsNumbers() { }
    @org.junit.jupiter.api.Test
    @DisplayName("x")
    void handlesNull() { }
    """
    assert extract_test_method_names(src) == {"addsNumbers", "handlesNull"}


def test_evaluate_gates_all_pass_and_attribution():
    ok_log = "[INFO] Tests run: 13, Failures: 0, Errors: 0, Skipped: 0\n[INFO] BUILD SUCCESS\n"
    before = {"src/test/java/T.java": "a" * 64}
    r = evaluate_gates(
        compile_log="[INFO] BUILD SUCCESS",
        test_log=ok_log,
        baseline_tests_run=13,
        class_majors=[61, 61],
        target_java=17,
        cov_before=75.5,
        cov_after=75.0,
        tests_before=before,
        tests_after=dict(before),
        required=["build", "tests_pass", "test_files_unchanged", "test_count_non_decreasing", "class_major_version", "coverage_guard"],
    )
    assert r["passed"] and all(v is True for v in r["gates"].values())

    r2 = evaluate_gates(
        compile_log="[INFO] BUILD SUCCESS",
        test_log=ok_log,
        baseline_tests_run=13,
        class_majors=[52],
        target_java=17,
        cov_before=75.5,
        cov_after=75.0,
        tests_before=before,
        tests_after=dict(before),
        required=["build", "tests_pass", "class_major_version"],
    )
    assert not r2["passed"] and r2["gates"]["class_major_version"] is False and r2["gates"]["tests_pass"] is True
