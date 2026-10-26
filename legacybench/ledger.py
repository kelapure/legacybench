"""Cost and latency ledger.

Dollars are computed from token counts and the dated price sheet, never read back
from a provider dashboard, so the analysis is reproducible after prices change.
"""

from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml

PRICES_PATH = Path(__file__).with_name("prices.yaml")


class MissingPriceError(ValueError):
    pass


def load_prices(path: str | Path = PRICES_PATH) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


def price_for(prices: dict[str, Any], model: str) -> dict[str, Any]:
    """Return the price entry for a model; accept names with or without provider prefix."""
    models = prices["models"]
    if model in models:
        entry = models[model]
    else:
        matches = [k for k in models if k.split("/", 1)[-1] == model.split("/", 1)[-1]]
        if len(matches) != 1:
            raise MissingPriceError(f"no price entry for model {model!r}")
        entry = models[matches[0]]
    for k in ("input", "output", "input_cache_read", "input_cache_write"):
        if entry.get(k) is None:
            raise MissingPriceError(
                f"price field {k!r} missing for {model!r} (confidence={entry.get('confidence')}); "
                "fill prices.yaml before running"
            )
    return entry


def cost_usd(
    usage: dict[str, int | None],
    entry: dict[str, Any],
    *,
    long_context: bool = False,
) -> float:
    """Dollars for one usage record.

    usage keys follow Inspect's ModelUsage: input_tokens (uncached), output_tokens
    (includes reasoning), input_tokens_cache_read, input_tokens_cache_write.
    """
    inp = usage.get("input_tokens") or 0
    out = usage.get("output_tokens") or 0
    cr = usage.get("input_tokens_cache_read") or 0
    cw = usage.get("input_tokens_cache_write") or 0
    p_in, p_out = entry["input"], entry["output"]
    if long_context and entry.get("long_context"):
        p_in = entry["long_context"]["input"]
        p_out = entry["long_context"]["output"]
    return (
        inp * p_in + out * p_out + cr * entry["input_cache_read"] + cw * entry["input_cache_write"]
    ) / 1_000_000


def is_long_context(usage: dict[str, int | None], entry: dict[str, Any]) -> bool:
    lc = entry.get("long_context")
    if not lc:
        return False
    total_in = (usage.get("input_tokens") or 0) + (usage.get("input_tokens_cache_read") or 0) + (
        usage.get("input_tokens_cache_write") or 0
    )
    return total_in > lc["threshold_input_tokens"]


@dataclass
class SampleLedger:
    sample_id: str
    model: str
    arm: str
    task_id: str
    stratum: str
    score: float | None
    input_tokens: int = 0
    cached_input_tokens: int = 0
    cache_write_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cost_usd: float = 0.0
    total_time_s: float | None = None
    working_time_s: float | None = None
    model_time_s: float = 0.0
    tool_time_s: float = 0.0
    wait_time_s: float | None = None
    error: str | None = None
    limit: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def as_row(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("extra")
        return d


def _usage_dict(u: Any) -> dict[str, int | None]:
    if isinstance(u, dict):
        return u
    return {
        "input_tokens": getattr(u, "input_tokens", 0),
        "output_tokens": getattr(u, "output_tokens", 0),
        "input_tokens_cache_read": getattr(u, "input_tokens_cache_read", None),
        "input_tokens_cache_write": getattr(u, "input_tokens_cache_write", None),
        "reasoning_tokens": getattr(u, "reasoning_tokens", None),
    }


def ledger_for_sample(sample: Any, prices: dict[str, Any], *, arm: str, model: str) -> SampleLedger:
    """Build a ledger row from an Inspect EvalSample (or a duck-typed stand-in)."""
    meta = getattr(sample, "metadata", None) or {}
    scores = getattr(sample, "scores", None) or {}
    score_val: float | None = None
    for s in scores.values():
        v = getattr(s, "value", None)
        if isinstance(v, (int, float)):
            score_val = float(v)
            break
    row = SampleLedger(
        sample_id=str(getattr(sample, "id", "")),
        model=model,
        arm=arm,
        task_id=str(meta.get("id", "")),
        stratum=str(meta.get("stratum", "")),
        score=score_val,
        total_time_s=getattr(sample, "total_time", None),
        working_time_s=getattr(sample, "working_time", None),
        error=str(getattr(sample, "error", None) or "") or None,
        limit=str(getattr(getattr(sample, "limit", None), "type", "") or "") or None,
    )
    usage_by_model = getattr(sample, "model_usage", None) or {}
    for mname, u in usage_by_model.items():
        ud = _usage_dict(u)
        entry = price_for(prices, mname)
        row.input_tokens += ud.get("input_tokens") or 0
        row.cached_input_tokens += ud.get("input_tokens_cache_read") or 0
        row.cache_write_tokens += ud.get("input_tokens_cache_write") or 0
        row.output_tokens += ud.get("output_tokens") or 0
        row.reasoning_tokens += ud.get("reasoning_tokens") or 0
        row.cost_usd += cost_usd(ud, entry, long_context=is_long_context(ud, entry))
    for ev in getattr(sample, "events", None) or []:
        kind = getattr(ev, "event", None)
        wt = getattr(ev, "working_time", None) or 0.0
        if kind == "model":
            row.model_time_s += wt
        elif kind == "tool":
            row.tool_time_s += wt
    if row.total_time_s is not None and row.working_time_s is not None:
        row.wait_time_s = max(0.0, row.total_time_s - row.working_time_s)
    return row


def ledger_for_log(log_path: str | Path, prices: dict[str, Any] | None = None) -> list[SampleLedger]:
    from inspect_ai.log import read_eval_log

    prices = prices or load_prices()
    log = read_eval_log(str(log_path))
    model = log.eval.model
    arm = (log.eval.task_args or {}).get("arm") or log.eval.task.split("/")[-1]
    return [ledger_for_sample(s, prices, arm=str(arm), model=model) for s in (log.samples or [])]


def write_csv(rows: Iterable[SampleLedger], path: str | Path) -> None:
    rows = list(rows)
    if not rows:
        Path(path).write_text("")
        return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].as_row().keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r.as_row())


def register_costs_with_inspect(prices: dict[str, Any] | None = None) -> list[str]:
    """Tell Inspect the prices so --cost-limit can enforce per-sample caps.

    Models with incomplete prices are skipped and returned so the caller can refuse
    to run them.
    """
    from inspect_ai.model import ModelCost, set_model_cost

    prices = prices or load_prices()
    skipped = []
    for name, e in prices["models"].items():
        if any(e.get(k) is None for k in ("input", "output", "input_cache_read", "input_cache_write")):
            skipped.append(name)
            continue
        set_model_cost(
            name,
            ModelCost(
                input=e["input"],
                output=e["output"],
                input_cache_write=e["input_cache_write"],
                input_cache_read=e["input_cache_read"],
            ),
        )
    return skipped


def summarize(rows: list[SampleLedger]) -> dict[str, Any]:
    """Descriptive cost/time summary: median, mean, p95 per model and arm."""
    import numpy as np

    out: dict[str, Any] = {}
    keys = sorted({(r.model, r.arm) for r in rows})
    for model, arm in keys:
        sub = [r for r in rows if r.model == model and r.arm == arm]
        costs = np.array([r.cost_usd for r in sub])
        times = np.array([r.total_time_s for r in sub if r.total_time_s is not None], dtype=float)
        out[f"{model}|{arm}"] = {
            "n": len(sub),
            "cost_median": float(np.median(costs)) if len(costs) else math.nan,
            "cost_mean": float(costs.mean()) if len(costs) else math.nan,
            "cost_p95": float(np.percentile(costs, 95)) if len(costs) else math.nan,
            "cost_total": float(costs.sum()) if len(costs) else 0.0,
            "time_p50_s": float(np.median(times)) if len(times) else math.nan,
            "time_p95_s": float(np.percentile(times, 95)) if len(times) else math.nan,
        }
    return out
