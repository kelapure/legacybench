import pytest

from legacybench.analysis.power import mde, n_tasks, table, var_paired_diff


def test_main_scenario_matches_design_brief_table():
    # Appendix C of the design brief: B=1/12, W=1/6, rho=0.5
    assert n_tasks(0.05, k=1) == 1309
    assert n_tasks(0.10, k=1) == 328
    assert n_tasks(0.15, k=1) == 146
    assert n_tasks(0.05, k=3) == 611
    assert n_tasks(0.10, k=3) == 153
    assert n_tasks(0.15, k=3) == 68
    assert n_tasks(0.05, k=5) == 471
    assert n_tasks(0.10, k=5) == 118
    assert n_tasks(0.15, k=5) == 53


def test_unpaired_sanity_check_against_errorbars_readme():
    # no pairing (rho=0), k=1, B+W=0.25, delta=3 points -> ~4361
    assert n_tasks(0.03, B=0.125, W=0.125, rho=0.0, k=1) == pytest.approx(4361, abs=2)


def test_mde_inverts_n():
    n = n_tasks(0.10, k=3)
    assert mde(n, k=3) == pytest.approx(0.10, abs=0.002)


def test_more_runs_reduce_only_within_variance():
    assert var_paired_diff(k=1) > var_paired_diff(k=3) > var_paired_diff(k=100)
    assert var_paired_diff(k=10**9) == pytest.approx(2 * (1 / 12) * 0.5, rel=1e-6)


def test_table_shape():
    t = table()
    assert set(t) == {1, 3, 5} and set(t[1]) == {0.05, 0.10, 0.15}
