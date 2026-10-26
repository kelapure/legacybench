from legacybench.solvers.single_shot import parse_multi_file


def test_round_trip_two_files_and_delete():
    text = (
        "=== FILE: pom.xml ===\n<project/>\n=== END FILE ===\n"
        "=== FILE: src/main/java/A.java ===\nclass A {}\n\n=== END FILE ===\n"
        "=== DELETE: src/main/java/Old.java ===\n"
    )
    p = parse_multi_file(text)
    assert p.files == {"pom.xml": "<project/>\n", "src/main/java/A.java": "class A {}\n\n"}
    assert p.deletes == ["src/main/java/Old.java"]
    assert not p.truncated and p.errors == []


def test_truncated_block_is_flagged():
    p = parse_multi_file("=== FILE: a.java ===\nclass A {\n")
    assert p.truncated
    assert "a.java" not in p.files
    assert any("unterminated" in e for e in p.errors)


def test_unsafe_paths_rejected():
    p = parse_multi_file(
        "=== FILE: ../../etc/passwd ===\nx\n=== END FILE ===\n"
        "=== FILE: /abs/path ===\nx\n=== END FILE ===\n"
        "=== DELETE: ../x ===\n"
    )
    assert p.files == {}
    assert p.deletes == []
    assert len(p.errors) == 3


def test_prose_outside_blocks_is_ignored():
    p = parse_multi_file("Here is the migration:\n=== FILE: a ===\n1\n=== END FILE ===\nDone.")
    assert p.files == {"a": "1\n"}
