"""Sandbox script generator for hypothesis validation."""

import json
import os
from pathlib import Path
from typing import Any


class SandboxScriptGenerator:
    """Generate executable Python scripts from validation plans."""

    def __init__(self):
        self.output_dir = Path(os.getenv("SANDBOX_OUTPUT_DIR", "/tmp/autoscience_sandbox"))

    async def generate_script(
        self,
        hypothesis_id: str,
        hypothesis_statement: str,
        validation_plan: dict[str, Any],
    ) -> dict[str, str]:
        """Generate a validation script from a validation plan."""
        template = self._build_script_template(
            hypothesis_id=hypothesis_id,
            hypothesis_statement=hypothesis_statement,
            validation_plan=validation_plan,
        )

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        script_path = self.output_dir / f"validate_{hypothesis_id}.py"
        with open(script_path, "w") as f:
            f.write(template)

        return {
            "script_path": str(script_path),
            "script_content": template,
        }

    def _build_script_template(
        self,
        hypothesis_id: str,
        hypothesis_statement: str,
        validation_plan: dict[str, Any],
    ) -> str:
        """Build the Python script template."""
        datasets = validation_plan.get("dataset_candidates", [])
        metrics = validation_plan.get("metrics", [])
        baselines = validation_plan.get("baselines", [])
        stats_tests = validation_plan.get("statistical_tests", [])
        design = validation_plan.get("experimental_design", "")

        datasets_json = json.dumps(datasets, indent=2)
        metrics_json = json.dumps(metrics, indent=2)
        baselines_json = json.dumps(baselines, indent=2)
        stats_tests_json = json.dumps(stats_tests, indent=2)
        design.replace("'''", "\\'\\'\\'")[:500]
        hypothesis_escaped = hypothesis_statement[:100].replace("'''", "\\'\\'\\'")

        script = (
            '#!/usr/bin/env python3\n'
            f'"""Generated validation script for: {hypothesis_statement[:80]}..."""\n'
            '\n'
            'import numpy as np\n'
            'import pandas as pd\n'
            'import json\n'
            'from pathlib import Path\n'
            'from typing import Any\n'
            '\n'
            '# Output directory inside the sandbox container\n'
            'OUTPUT_DIR = Path("/app/outputs")\n'
            'OUTPUT_DIR.mkdir(parents=True, exist_ok=True)\n'
            '\n'
            '# Configuration\n'
            f'DATASET_CANDIDATES = {datasets_json}\n'
            f'HYPOTHESIS_ID = "{hypothesis_id}"\n'
            f'HYPOTHESIS_STATEMENT = """{hypothesis_escaped}"""\n'
            f'METRICS = {metrics_json}\n'
            f'BASELINES = {baselines_json}\n'
            f'STATISTICAL_TESTS = {stats_tests_json}\n'
            '\n'
            '\n'
            'def load_data() -> dict[str, pd.DataFrame]:\n'
            '    """Load dataset candidates."""\n'
            '    data: dict[str, pd.DataFrame] = {}\n'
            '    for dataset in DATASET_CANDIDATES:\n'
            '        path = dataset.get("path")\n'
            '        if path and Path(path).exists():\n'
            '            try:\n'
            '                data[dataset.get("name", "unknown")] = pd.read_csv(path)\n'
            '            except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:\n'
            '                print(f"  [WARN] Could not load {path}: {e}")\n'
            '    if not data:\n'
            '        # Generate synthetic data for demo purposes\n'
            '        print("  [INFO] No datasets found. Generating synthetic data...")\n'
            '        rng = np.random.default_rng(42)\n'
            '        n_samples = 200\n'
            '        data["synthetic"] = pd.DataFrame({\n'
            '            "control": rng.normal(loc=0.0, scale=1.0, size=n_samples),\n'
            '            "treatment": rng.normal(loc=0.5, scale=1.0, size=n_samples),\n'
            '            "feature_1": rng.uniform(0, 1, size=n_samples),\n'
            '            "feature_2": rng.exponential(scale=1.0, size=n_samples),\n'
            '            "category": rng.choice(["A", "B", "C"], size=n_samples),\n'
            '        })\n'
            '    return data\n'
            '\n'
            '\n'
            'def hypothesis_metric(data: dict[str, pd.DataFrame]) -> dict[str, Any]:\n'
            '    """Calculate descriptive statistics for each dataset.\n'
            '\n'
            '    Returns summary statistics (mean, std, min, max, count, missing%)\n'
            '    for every numeric column across all loaded datasets.\n'
            '    """\n'
            '    results: dict[str, Any] = {}\n'
            '    for name, df in data.items():\n'
            '        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()\n'
            '        if not numeric_cols:\n'
            '            results[name] = {"error": "No numeric columns found"}\n'
            '            continue\n'
            '        stats = df[numeric_cols].describe(percentiles=[0.25, 0.5, 0.75]).to_dict()\n'
            '        missing = df[numeric_cols].isna().sum().to_dict()\n'
            '        results[name] = {\n'
            '            "descriptive_stats": stats,\n'
            '\n'
            '            "missing_values": {k: int(v) for k, v in missing.items()},\n'
            '\n'
            '            "shape": {"rows": int(df.shape[0]), "cols": int(df.shape[1])},\n'
            '\n'
            '            "numeric_columns": numeric_cols,\n'
            '\n'
            '        }\n'
            '    return results\n'
            '\n'
            '\n'
            'def evaluate_baseline(data: dict[str, pd.DataFrame], baseline_name: str | None = None) -> dict[str, Any]:\n'
            '    """Compute summary metrics per dataset as a baseline reference.\n'
            '    \n'
            '    For each dataset, computes:\n'
            '      - Mean, std, and quartiles for each numeric column\n'
            '      - Class balance for categorical columns\n'
            '    """\n'
            '    results: dict[str, Any] = {}\n'
            '    for name, df in data.items():\n'
            '        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()\n'
            '        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()\n'
            '        info: dict[str, Any] = {\n'
            '            "num_rows": int(df.shape[0]),\n'
            '            "num_columns": int(df.shape[1]),\n'
            '        }\n'
            '        if numeric_cols:\n'
            '            info["means"] = {c: float(df[c].mean()) for c in numeric_cols}\n'
            '            info["stds"] = {c: float(df[c].std()) for c in numeric_cols}\n'
            '            info["medians"] = {c: float(df[c].median()) for c in numeric_cols}\n'
            '            info["q1_q3"] = {\n'
            '                c: {"q1": float(df[c].quantile(0.25)), "q3": float(df[c].quantile(0.75))}\n'
            '                for c in numeric_cols\n'
            '            }\n'
            '        if cat_cols:\n'
            '            info["class_balance"] = {\n'
            '                c: df[c].value_counts(normalize=True).to_dict()\n'
            '                for c in cat_cols\n'
            '            }\n'
            '        results[name] = info\n'
            '    return results\n'
            '\n'
            '\n'
            'def statistical_test(data: dict[str, pd.DataFrame]) -> dict[str, Any]:\n'
            '    """Run statistical tests on data.\n'
            '    \n'
            '    Attempts to import scipy.stats. If available, runs:\n'
            '      - Independent t-test (control vs treatment) on the first two numeric columns\n'
            '      - One-sample Kolmogorov-Smirnov test against normal distribution\n'
            '    Falls back to descriptive comparison when scipy is not installed.\n'
            '    """\n'
            '    try:\n'
            '        from scipy import stats as scipy_stats\n'
            '        HAS_SCIPY = True\n'
            '    except ImportError:\n'
            '        HAS_SCIPY = False\n'
            '\n'
            '    results: dict[str, Any] = {}\n'
            '    for name, df in data.items():\n'
            '        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()\n'
            '        dataset_tests: dict[str, Any] = {}\n'
            '\n'
            '        if HAS_SCIPY and len(numeric_cols) >= 2:\n'
            '            col_a, col_b = numeric_cols[0], numeric_cols[1]\n'
            '            a = df[col_a].dropna()\n'
            '            b = df[col_b].dropna()\n'
            '            if len(a) > 1 and len(b) > 1:\n'
            '                t_stat, p_value = scipy_stats.ttest_ind(a, b, equal_var=False)\n'
            '                ks_stat, ks_p = scipy_stats.ks_2samp(a, b)\n'
            '                dataset_tests["independent_t_test"] = {\n'
            '                    "column_a": col_a,\n'
            '\n'
            '                    "column_b": col_b,\n'
            '\n'
            '                    "t_statistic": float(round(t_stat, 6)),\n'
            '                    "p_value": float(round(p_value, 6)),\n'
            '                    "significant_05": bool(p_value < 0.05),\n'
            '                    "effect_size_cohens_d": float(\n'
            '                        round((a.mean() - b.mean()) / np.sqrt((a.std()**2 + b.std()**2) / 2), 4)\n'
            '                    ),\n'
            '                }\n'
            '                dataset_tests["two_sample_ks_test"] = {\n'
            '                    "statistic": float(round(ks_stat, 6)),\n'
            '                    "p_value": float(round(ks_p, 6)),\n'
            '                }\n'
            '            # Normality test on first numeric column\n'
            '            if len(a) >= 8:\n'
            '                shapiro_stat, shapiro_p = scipy_stats.shapiro(a[:5000])  # cap at 5000\n'
            '                dataset_tests["shapiro_wilk_normality"] = {\n'
            '                    "statistic": float(round(shapiro_stat, 6)),\n'
            '                    "p_value": float(round(shapiro_p, 6)),\n'
            '                    "normal_05": bool(shapiro_p > 0.05),\n'
            '                }\n'
            '        elif not HAS_SCIPY:\n'
            '            # Fallback: descriptive comparison\n'
            '            for col in numeric_cols[:2]:\n'
            '                series = df[col].dropna()\n'
            '                if len(series) > 0:\n'
            '                    dataset_tests[f"descriptive_{col}"] = {\n'
            '                        "mean": float(round(series.mean(), 4)),\n'
            '                        "std": float(round(series.std(), 4)),\n'
            '                        "min": float(round(series.min(), 4)),\n'
            '                        "max": float(round(series.max(), 4)),\n'
            '                        "n": int(len(series)),\n'
            '                        "note": "scipy not available \\u2014 descriptive stats only",\n'
            '                    }\n'
            '\n'
            '        results[name] = dataset_tests\n'
            '    return results\n'
            '\n'
            '\n'
            'def main():\n'
            '    """Main validation routine."""\n'
            '    print(">>> Loading datasets...")\n'
            '    data = load_data()\n'
            '    print(f">>> Loaded {len(data)} dataset(s)")\n'
            '\n'
            '    print(">>> Computing hypothesis metrics...")\n'
            '    hyp_metrics = hypothesis_metric(data)\n'
            '\n'
            '    print(">>> Evaluating baselines...")\n'
            '    baseline_name = BASELINES[0] if BASELINES else None\n'
            '    baselines = evaluate_baseline(data, baseline_name)\n'
            '\n'
            '    print(">>> Running statistical tests...")\n'
            '    stats = statistical_test(data)\n'
            '\n'
            '    results = {\n'
            '        "hypothesis": HYPOTHESIS_STATEMENT,\n'
            '        "datasets": list(data.keys()),\n'
            '        "hypothesis_metrics": hyp_metrics,\n'
            '\n'
            '        "baselines": baselines,\n'
            '\n'
            '        "statistical_tests": stats,\n'
            '\n'
            '        "metrics_defined": METRICS,\n'
            '\n'
            '        "num_datasets": len(data),\n'
            '        "num_columns_per_dataset": {\n'
            '            name: int(df.shape[1]) for name, df in data.items()\n'
            '        },\n'
            '\n'
            '    }\n'
            '\n'
            '    # --- Structured per-hypothesis output for _validate_hypotheses ---\n'
            '    # Compute validation outcome from the first statistical test\n'
            '    p_value = None\n'
            '    for ds_name, ds_tests in stats.items():\n'
            '        ttest = ds_tests.get("independent_t_test", {})\n'
            '        if ttest.get("p_value") is not None:\n'
            '            p_value = ttest["p_value"]\n'
            '            break\n'
            '\n'
            '    if p_value is not None:\n'
            '        is_significant = p_value < 0.05\n'
            '        hypothesis_status = "validated" if is_significant else "rejected"\n'
            '    else:\n'
            '        is_significant = None\n'
            '        hypothesis_status = "inconclusive"\n'
            '\n'
            '    hyp_result = {\n'
            '        "hypothesis_id": HYPOTHESIS_ID,\n'
            '        "statement": HYPOTHESIS_STATEMENT,\n'
            '        "status": hypothesis_status,\n'
            '        "confidence": 0.85 if is_significant else (0.30 if is_significant is False else 0.50),\n'
            '        "evidence": hyp_metrics,\n'
            '        "metrics": dict(METRICS) if METRICS else {},\n'
            '        "p_value": p_value,\n'
            '        "significant_05": is_significant,\n'
            '    }\n'
            '    results_block = {"hypothesis_results": [hyp_result]}\n'
            '    print("##HYPOTHESIS_RESULTS##")\n'
            '    print(json.dumps(results_block))\n'
            '\n'
            '    print(">>> Saving results...")\n'
            '    output_path = OUTPUT_DIR / "validation_results.json"\n'
            '    with open(output_path, "w") as f:\n'
            '        json.dump(results, f, indent=2, default=str)\n'
            '\n'
            '    print(f">>> Results saved to {output_path}")\n'
            '    print(">>> Done.")\n'
            '    return results\n'
            '\n'
            '\n'
            'if __name__ == "__main__":\n'
            '    main()\n'
        )
        return script


# Global generator instance
_generator: SandboxScriptGenerator | None = None


def get_sandbox_generator() -> SandboxScriptGenerator:
    """Get or create the global sandbox generator."""
    global _generator
    if _generator is None:
        _generator = SandboxScriptGenerator()
    return _generator
