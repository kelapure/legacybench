from legacybench.probe.ceiling import PROMPT, parse_probe_output


def _lines(n):
    return "\n".join(f"def f_{k:05d}(x): return x + {k}" for k in range(1, n + 1))


def test_complete_output():
    r = parse_probe_output(_lines(5), 5)
    assert r["complete"] and r["valid_lines"] == 5 and r["in_order"] and r["parses"] and r["fraction"] == 1.0


def test_truncated_output_counts_valid_prefix():
    text = _lines(3) + "\ndef f_00004(x): retu"
    r = parse_probe_output(text, 10)
    assert r["valid_lines"] == 3 and not r["complete"] and r["fraction"] == 0.3


def test_out_of_order_stops_count():
    text = "def f_00001(x): return x + 1\ndef f_00003(x): return x + 3\n"
    r = parse_probe_output(text, 3)
    assert r["valid_lines"] == 1 and not r["in_order"]


def test_prompt_formats_without_leaking_braces():
    p = PROMPT.format(n=2000)
    assert "f_02000" in p and "{n}" not in p and "{k:05d}" in p
