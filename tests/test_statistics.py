"""Model card §11: statistical budget and yield. Expected values are copied from the card."""

import pytest

from oicd.report import evaluate
from oicd.statistics import LABEL, analytic_yield, monte_carlo_yield, normal_cdf

from .conftest import with_sigma

MATINGS = (0, 2, 4)  # TX FAU, patch connector, RX FAU in the §2 order


@pytest.fixture(scope="module")
def card_link(worked_example):
    # §11: the three matings (means 1.5, 1.0, 1.5 dB) each sigma 0.2 dB, fiber fixed.
    return with_sigma(worked_example, MATINGS, 0.2)


def test_hand_case(card_link):
    # §11: sigma_total 0.34641 dB, z 1.44107, yield 0.92522, margin at 3 sigma -0.54003 dB.
    result = analytic_yield(card_link)
    assert result.sigma_total_db == pytest.approx(0.34641, abs=1e-5)
    assert result.z == pytest.approx(1.44107, abs=1e-5)
    assert result.yield_fraction == pytest.approx(0.92522, abs=1e-5)
    assert result.margin_at_3sigma_db == pytest.approx(-0.54003, abs=1e-5)
    assert result.m_mean_db == pytest.approx(0.4992, abs=1e-12)
    assert result.label == LABEL == "statistical, assumption-dependent"
    assert [d.path for d in result.distributed] == [
        f"channel[{i}].loss_distribution" for i in MATINGS
    ]


def test_monte_carlo_reproduces_the_analytic_yield(card_link):
    # §11: a seeded Monte Carlo with 10^6 samples lands within 0.002 of 0.92522.
    mc = monte_carlo_yield(card_link, n_samples=1_000_000, seed=20261018)
    assert mc.yield_fraction == pytest.approx(0.92522, abs=0.002)
    assert sum(mc.histogram.counts) + mc.histogram.below + mc.histogram.above == mc.n_samples
    assert mc.sample_std_db == pytest.approx(0.34641, abs=0.002)


def test_monte_carlo_is_deterministic(card_link):
    a = monte_carlo_yield(card_link, n_samples=10_000, seed=7)
    b = monte_carlo_yield(card_link, n_samples=10_000, seed=7)
    assert a == b
    assert monte_carlo_yield(card_link, n_samples=10_000, seed=8) != a


def test_worst_case_verdict_is_unchanged(worked_example, card_link):
    # §11: the statistical result never changes the worst-case verdict.
    with_dist, without = evaluate(card_link), evaluate(worked_example)
    assert with_dist.verdict == without.verdict
    assert with_dist.margin_db == without.margin_db
    assert analytic_yield(card_link).worst_case_margin_db == without.margin_db


def test_no_distribution_means_a_step_yield(worked_example, make_link):
    # §11: with sigma_total = 0 the yield is 1 if M_mean >= -ε, else 0, and z is null.
    passing = analytic_yield(worked_example)
    assert (passing.sigma_total_db, passing.z, passing.yield_fraction) == (0.0, None, 1.0)
    failing = analytic_yield(make_link(channel_db=(("c", 5.0),)))
    assert failing.yield_fraction == 0.0


def test_normal_cdf_values():
    assert normal_cdf(0.0) == 0.5
    assert normal_cdf(1.44107) == pytest.approx(0.92522, abs=1e-5)
    assert normal_cdf(-8.0) == pytest.approx(6.22096e-16, rel=1e-4)


@pytest.mark.parametrize("kwargs", [{"n_samples": 0}, {"bins": 0}, {"seed": -1}])
def test_invalid_monte_carlo_arguments(card_link, kwargs):
    with pytest.raises(ValueError):
        monte_carlo_yield(card_link, **kwargs)
