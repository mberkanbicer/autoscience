"""Tests for statistical power analysis."""

import pytest

from app.engine.power_analysis import proportion_test_power, two_sample_ttest_power


def test_two_sample_ttest_power():
    result = two_sample_ttest_power(0.5, alpha=0.05, power=0.8)
    assert result.sample_size_per_group is not None
    assert result.sample_size_per_group >= 30
    assert result.test_type == "two_sample_ttest"


def test_proportion_test_power():
    result = proportion_test_power(0.3, 0.5, alpha=0.05, power=0.8)
    assert result.sample_size_per_group is not None
    assert result.total_sample_size == 2 * result.sample_size_per_group


def test_invalid_effect_size():
    with pytest.raises(ValueError):
        two_sample_ttest_power(0)