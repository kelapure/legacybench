from types import SimpleNamespace

import pytest

from legacybench.ledger import (
    MissingPriceError,
    cost_usd,
    is_long_context,
    ledger_for_sample,
    load_prices,
    price_for,
)


def test_fable_cost_matches_hand_computation():
    prices = load_prices()
    e = price_for(prices, "anthropic/claude-fable-5-1")
    usage = {"input_tokens": 100_000, "output_tokens": 20_000, "input_tokens_cache_read": 400_000, "input_tokens_cache_write": 0}
    # 0.1M * $10 + 0.02M * $50 + 0.4M * $0.25 = 1.0 + 1.0 + 0.1
    assert cost_usd(usage, e) == pytest.approx(2.1)


def test_provider_prefix_optional():
    prices = load_prices()
    assert price_for(prices, "gemini-4-argon")["output"] == 10.0


def test_missing_price_is_loud():
    prices = load_prices()
    with pytest.raises(MissingPriceError):
        price_for(prices, "openai/gpt-6-astra")


def test_long_context_switch():
    prices = load_prices()
    e = price_for(prices, "openai/gpt-6.1-sol")
    small = {"input_tokens": 100_000, "output_tokens": 1000}
    big = {"input_tokens": 300_000, "output_tokens": 1000}
    assert not is_long_context(small, e) and is_long_context(big, e)
    assert cost_usd(big, e, long_context=True) == pytest.approx(0.3 * 4.0 + 0.001 * 15.0)


def test_ledger_row_from_duck_typed_sample():
    prices = load_prices()
    usage = SimpleNamespace(input_tokens=1_000_000, output_tokens=100_000, input_tokens_cache_read=0, input_tokens_cache_write=0, reasoning_tokens=40_000)
    sample = SimpleNamespace(
        id="t1",
        metadata={"id": "freshbrew/x", "stratum": "S"},
        scores={"migration_gates": SimpleNamespace(value=1.0)},
        model_usage={"google/gemini-4-argon": usage},
        total_time=100.0,
        working_time=80.0,
        events=[SimpleNamespace(event="model", working_time=50.0), SimpleNamespace(event="tool", working_time=30.0)],
        error=None,
        limit=None,
    )
    row = ledger_for_sample(sample, prices, arm="agentic", model="google/gemini-4-argon")
    assert row.cost_usd == pytest.approx(2.0 + 1.0)
    assert row.reasoning_tokens == 40_000
    assert row.model_time_s == 50.0 and row.tool_time_s == 30.0 and row.wait_time_s == pytest.approx(20.0)
    assert row.score == 1.0 and row.stratum == "S"
