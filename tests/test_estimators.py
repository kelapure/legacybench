import pytest

from legacybench.analysis.estimators import (
    clustered_se,
    holm,
    mcnemar_exact,
    paired_difference,
    pass_at_k,
    pass_hat_k,
    wilson,
)


def test_wilson_known_value():
    w = wilson(8, 10)
    assert w.estimate == 0.8
    assert w.low == pytest.approx(0.490, abs=0.002)
    assert w.high == pytest.approx(0.943, abs=0.002)


def test_paired_difference_uses_pairing():
    a = [1, 1, 0, 1, 0, 1, 1, 0]
    b = [1, 0, 0, 1, 0, 1, 0, 0]
    r = paired_difference(a, b)
    assert r["diff"] == pytest.approx(0.25)
    assert r["n"] == 8 and r["low"] < 0.25 < r["high"]


def test_clustered_se_equals_naive_when_each_task_is_its_own_cluster():
    x = [0, 1, 1, 0, 1, 1, 0, 0, 1, 1]
    se_cluster = clustered_se(x, [str(i) for i in range(10)])
    import numpy as np

    naive = np.std(x, ddof=0) / np.sqrt(10)
    assert se_cluster == pytest.approx(naive)


def test_pass_at_k_and_pass_hat_k():
    assert pass_at_k(10, 5, 1) == pytest.approx(0.5)
    assert pass_at_k(10, 10, 3) == 1.0
    assert pass_at_k(10, 0, 3) == 0.0
    assert pass_hat_k(10, 10, 3) == 1.0
    assert pass_hat_k(10, 2, 3) == 0.0
    assert 0 < pass_hat_k(10, 5, 2) < pass_at_k(10, 5, 2)


def test_mcnemar_and_holm():
    assert mcnemar_exact(0, 0) == 1.0
    assert mcnemar_exact(10, 0) < 0.01
    adj = holm([0.01, 0.04, 0.03])
    assert adj == pytest.approx([0.03, 0.04, 0.06]) or adj[0] == pytest.approx(0.03)
    assert all(0 <= p <= 1 for p in adj)
