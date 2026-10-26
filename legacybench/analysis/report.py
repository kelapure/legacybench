"""Descriptive pilot report from a directory of Inspect .eval logs.

    python -m legacybench.analysis.report logs/ --out reports/pilot

Produces ledger.csv (one row per sample), summary.md (per model x arm: pass rate
with Wilson interval, cost and time quantiles), and states the minimum detectable
effect at the pilot's n so nobody reads a pilot gap as a result.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from legacybench.analysis.estimators import wilson
from legacybench.analysis.power import mde
from legacybench.ledger import ledger_for_log, load_prices, summarize, write_csv


def build(log_dir: Path, out_dir: Path) -> Path:
    prices = load_prices()
    rows = []
    for p in sorted(log_dir.glob("*.eval")):
        rows.extend(ledger_for_log(p, prices))
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(rows, out_dir / "ledger.csv")

    by = defaultdict(list)
    for r in rows:
        by[(r.model, r.arm)].append(r)
    cost_summary = summarize(rows)

    lines = ["# Pilot summary (descriptive; no ranking claims)", ""]
    lines.append(
        "This is a pilot with k = 1 run per task. Differences between models below are not "
        "evidence of a difference unless the intervals are disjoint, and even then the "
        "pre-registration labels them exploratory."
    )
    lines.append("")
    lines.append("| model | arm | n | passed | pass rate | 95% Wilson | MDE at this n (k=1) | cost median $ | cost p95 $ | cost total $ | time p50 s | time p95 s |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for (model, arm), rs in sorted(by.items()):
        scored = [r for r in rs if r.score is not None]
        n = len(scored)
        passed = sum(1 for r in scored if r.score and r.score >= 1.0)
        w = wilson(passed, n) if n else None
        cs = cost_summary[f"{model}|{arm}"]
        lines.append(
            f"| {model} | {arm} | {n} | {passed} | "
            f"{(passed / n):.2f} | " if n else f"| {model} | {arm} | 0 | 0 | - | "
        )
        if n:
            lines[-1] += (
                f"[{w.low:.2f}, {w.high:.2f}] | {mde(n):.2f} | {cs['cost_median']:.2f} | {cs['cost_p95']:.2f} | "
                f"{cs['cost_total']:.2f} | {cs['time_p50_s']:.0f} | {cs['time_p95_s']:.0f} |"
            )
        else:
            lines[-1] += "- | - | - | - | - | - | - |"
    lines.append("")
    lines.append("Per-sample rows, including per-gate results, are in ledger.csv.")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    (out_dir / "cost_summary.json").write_text(json.dumps(cost_summary, indent=2))
    return out_dir / "summary.md"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("log_dir", type=Path)
    ap.add_argument("--out", type=Path, default=Path("reports/pilot"))
    args = ap.parse_args()
    print(build(args.log_dir, args.out))


if __name__ == "__main__":
    main()
