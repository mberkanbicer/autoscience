"""Tests for effect size extraction from experiment stdout."""

import pytest

from app.engine.effect_size_extraction import (
    extract_effect_sizes,
    format_effect_sizes_for_manuscript,
    format_effect_sizes_as_validation_results,
    EffectSize,
)


class TestCohensDExtraction:
    """Tests for Cohen's d extraction."""

    def test_direct_d_assignment(self):
        stdout = "Cohen's d = 0.45"
        result = extract_effect_sizes(stdout)
        assert result.total_count >= 1
        d_effects = [e for e in result.effect_sizes if e.effect_type == "cohens_d"]
        assert len(d_effects) >= 1
        assert d_effects[0].value == pytest.approx(0.45, abs=0.01)
        assert d_effects[0].interpretation == "small_to_medium"

    def test_d_equals_pattern(self):
        stdout = "d = 0.82"
        result = extract_effect_sizes(stdout)
        d_effects = [e for e in result.effect_sizes if e.effect_type == "cohens_d"]
        assert len(d_effects) >= 1
        assert d_effects[0].value == pytest.approx(0.82, abs=0.01)
        assert d_effects[0].interpretation == "large"

    def test_d_colon_pattern(self):
        stdout = "d: 0.20"
        result = extract_effect_sizes(stdout)
        d_effects = [e for e in result.effect_sizes if e.effect_type == "cohens_d"]
        assert len(d_effects) >= 1
        assert d_effects[0].value == pytest.approx(0.20, abs=0.01)
        assert d_effects[0].interpretation == "small"

    def test_large_effect(self):
        stdout = "Cohen's d = 1.50"
        result = extract_effect_sizes(stdout)
        d_effects = [e for e in result.effect_sizes if e.effect_type == "cohens_d"]
        assert len(d_effects) >= 1
        assert d_effects[0].interpretation == "very_large"

    def test_negative_d(self):
        stdout = "d = -0.65"
        result = extract_effect_sizes(stdout)
        d_effects = [e for e in result.effect_sizes if e.effect_type == "cohens_d"]
        assert len(d_effects) >= 1
        assert d_effects[0].value == pytest.approx(-0.65, abs=0.01)
        assert d_effects[0].direction == "negative"


class TestEtaSquaredExtraction:
    """Tests for η² extraction."""

    def test_direct_eta_squared(self):
        stdout = "η² = 0.14"
        result = extract_effect_sizes(stdout)
        eta = [e for e in result.effect_sizes if e.effect_type == "eta_squared"]
        assert len(eta) >= 1
        assert eta[0].value == pytest.approx(0.14, abs=0.01)
        # η² = 0.14 is the conventional threshold for "large" (Cohen, 1988)

    def test_eta_squared_text_pattern(self):
        stdout = "partial eta-squared: 0.06"
        result = extract_effect_sizes(stdout)
        eta = [e for e in result.effect_sizes if e.effect_type == "eta_squared"]
        assert len(eta) >= 1
        assert eta[0].value == pytest.approx(0.06, abs=0.01)
        # η² = 0.06 is the conventional threshold for "medium"

    def test_small_eta(self):
        stdout = "eta_sq = 0.009"
        result = extract_effect_sizes(stdout)
        eta = [e for e in result.effect_sizes if e.effect_type == "eta_squared"]
        assert len(eta) >= 1
        assert eta[0].interpretation == "none"


class TestRSquaredExtraction:
    """Tests for R² extraction."""

    def test_r_squared(self):
        stdout = "R² = 0.85"
        result = extract_effect_sizes(stdout)
        r2 = [e for e in result.effect_sizes if e.effect_type == "r_squared"]
        assert len(r2) >= 1
        assert r2[0].value == pytest.approx(0.85, abs=0.01)
        assert r2[0].interpretation == "large"

    def test_r_squared_text(self):
        stdout = "R-squared: 0.72"
        result = extract_effect_sizes(stdout)
        r2 = [e for e in result.effect_sizes if e.effect_type == "r_squared"]
        assert len(r2) >= 1
        assert r2[0].value == pytest.approx(0.72, abs=0.01)


class TestCorrelationExtraction:
    """Tests for correlation coefficient extraction."""

    def test_pearson_r(self):
        stdout = "Pearson r = 0.42"
        result = extract_effect_sizes(stdout)
        corr = [e for e in result.effect_sizes if e.effect_type == "correlation"]
        assert len(corr) >= 1
        assert corr[0].value == pytest.approx(0.42, abs=0.01)
        assert corr[0].interpretation == "medium"

    def test_negative_correlation(self):
        stdout = "r = -0.35"
        result = extract_effect_sizes(stdout)
        corr = [e for e in result.effect_sizes if e.effect_type == "correlation"]
        assert len(corr) >= 1
        assert corr[0].value == pytest.approx(-0.35, abs=0.01)
        assert corr[0].direction == "negative"

    def test_spearman_rho(self):
        stdout = "Spearman's ρ = 0.55"
        result = extract_effect_sizes(stdout)
        corr = [e for e in result.effect_sizes if e.effect_type == "correlation"]
        assert len(corr) >= 1
        assert corr[0].value == pytest.approx(0.55, abs=0.01)
        assert corr[0].interpretation == "large"


class TestComputeFromTestStatistics:
    """Tests for computing effect sizes from test statistics."""

    def test_d_from_t_statistic(self):
        """d = 2*t / sqrt(df) for two-sample test."""
        stdout = "t(28) = 2.14"
        result = extract_effect_sizes(stdout)
        d_effects = [e for e in result.effect_sizes if e.effect_type == "cohens_d"]
        # Should have computed d = 2*2.14 / sqrt(28) ≈ 0.81
        expected_d = 2 * 2.14 / (28 ** 0.5)
        computed = [e for e in d_effects if "computed from" in e.evidence]
        assert len(computed) >= 1
        assert computed[0].value == pytest.approx(expected_d, abs=0.05)

    def test_eta_from_f_statistic(self):
        """η² = F*df1 / (F*df1 + df2)."""
        stdout = "F(1, 28) = 5.23"
        result = extract_effect_sizes(stdout)
        eta = [e for e in result.effect_sizes if e.effect_type == "eta_squared"]
        expected_eta2 = (5.23 * 1) / (5.23 * 1 + 28)
        computed = [e for e in eta if "computed from" in e.evidence]
        assert len(computed) >= 1
        assert computed[0].value == pytest.approx(expected_eta2, abs=0.02)


class TestOddsRatioExtraction:
    """Tests for odds ratio extraction."""

    def test_or_label(self):
        stdout = "OR = 2.50"
        result = extract_effect_sizes(stdout)
        or_es = [e for e in result.effect_sizes if e.effect_type == "odds_ratio"]
        assert len(or_es) >= 1
        assert or_es[0].value == pytest.approx(2.50, abs=0.01)
        assert or_es[0].interpretation == "medium"

    def test_odds_ratio_label(self):
        stdout = "odds ratio: 1.35"
        result = extract_effect_sizes(stdout)
        or_es = [e for e in result.effect_sizes if e.effect_type == "odds_ratio"]
        assert len(or_es) >= 1
        assert or_es[0].interpretation == "small"


class TestRealWorldExamples:
    """Tests with realistic experiment output blocks."""

    def test_anova_output(self):
        stdout = """ANOVA Results:
        F(2, 87) = 4.82, p = 0.010
        η² = 0.10
        """
        result = extract_effect_sizes(stdout)
        assert result.total_count >= 1
        types = {e.effect_type for e in result.effect_sizes}
        assert "eta_squared" in types
        # Direct η² = 0.10 should be medium
        eta = [e for e in result.effect_sizes if e.effect_type == "eta_squared"]
        assert any(e.interpretation == "medium" for e in eta)

    def test_regression_output(self):
        stdout = """Linear Regression Results:
        R² = 0.73, Adjusted R² = 0.71
        F(3, 96) = 86.42, p < 0.001
        Cohen's f² = 2.70
        """
        result = extract_effect_sizes(stdout)
        assert result.total_count >= 1
        types = {e.effect_type for e in result.effect_sizes}
        assert "r_squared" in types
        # R² = 0.73 should be large
        r2 = [e for e in result.effect_sizes if e.effect_type == "r_squared"]
        assert any(r.interpretation == "large" for r in r2)

    def test_t_test_output(self):
        stdout = """Two-sample t-test:
        t(58) = 2.45, p = 0.017
        Cohen's d = 0.64
        """
        result = extract_effect_sizes(stdout)
        # Direct d=0.64 and computed d from t (2*2.45/sqrt(58)≈0.643) are within 5%,
        # so dedup reduces them to one. total_count should be >= 1.
        assert result.total_count >= 1
        d_effects = [e for e in result.effect_sizes if e.effect_type == "cohens_d"]
        assert len(d_effects) >= 1
        assert d_effects[0].interpretation in ("medium", "small_to_medium")

    def test_empty_stdout(self):
        result = extract_effect_sizes("")
        assert result.total_count == 0

    def test_no_effect_sizes(self):
        stdout = "Processing complete. Status: OK. Elapsed: 12.3 seconds."
        result = extract_effect_sizes(stdout)
        assert result.total_count == 0
        assert "No effect sizes" in result.notes


class TestFormatting:
    """Tests for formatting functions."""

    def test_format_for_manuscript(self):
        es_list = [
            EffectSize(effect_type="cohens_d", value=0.65),
            EffectSize(effect_type="eta_squared", value=0.20),
        ]
        formatted = format_effect_sizes_for_manuscript(es_list)
        assert len(formatted) == 2
        assert "Cohen's d" in formatted[0]
        assert "η²" in formatted[1]
        assert "medium" in formatted[0]

    def test_format_as_validation_results(self):
        es_list = [
            EffectSize(effect_type="cohens_d", value=2.00),
        ]
        results = format_effect_sizes_as_validation_results(es_list)
        assert len(results) == 1
        assert "effect_size_cohens_d" in results[0]["metric"]
        assert "Very Large" in results[0]["result"]


class TestInterpretationThresholds:
    """Tests for interpretation thresholds."""

    def test_cohens_d_thresholds(self):
        cases = [
            (0.01, "none"),
            (0.15, "small"),
            (0.35, "small_to_medium"),
            (0.65, "medium"),
            (1.00, "large"),
            (1.50, "very_large"),
        ]
        for value, expected in cases:
            es = EffectSize(effect_type="cohens_d", value=value)
            assert es.interpretation == expected, f"d={value}: expected {expected}, got {es.interpretation}"

    def test_eta_squared_thresholds(self):
        cases = [
            (0.005, "none"),
            (0.03, "small"),
            (0.10, "medium"),
            (0.20, "large"),
        ]
        for value, expected in cases:
            es = EffectSize(effect_type="eta_squared", value=value)
            assert es.interpretation == expected, f"η²={value}: expected {expected}, got {es.interpretation}"

    def test_r_squared_thresholds(self):
        cases = [
            (0.005, "none"),
            (0.10, "small"),
            (0.20, "medium"),
            (0.30, "large"),
        ]
        for value, expected in cases:
            es = EffectSize(effect_type="r_squared", value=value)
            assert es.interpretation == expected, f"R²={value}: expected {expected}, got {es.interpretation}"

    def test_correlation_thresholds(self):
        cases = [
            (0.02, "none"),
            (0.20, "small"),
            (0.40, "medium"),
            (0.55, "large"),
        ]
        for value, expected in cases:
            es = EffectSize(effect_type="correlation", value=value)
            assert es.interpretation == expected, f"r={value}: expected {expected}, got {es.interpretation}"
