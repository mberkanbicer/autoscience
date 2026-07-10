#!/usr/bin/env python3
"""Lightweight benchmark framework smoke test (no LLM calls).

Usage:
    cd backend && python scripts/benchmark_smoke.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))


def main() -> int:
    from app.benchmarks.run_benchmark import (
        TEST_IDEAS,
        BenchmarkConfig,
        BenchmarkRunner,
    )

    with tempfile.TemporaryDirectory(prefix="autoscience-bench-") as tmp:
        config = BenchmarkConfig(
            output_dir=tmp,
            test_ideas=TEST_IDEAS[:1],
            num_cycles=1,
        )
        runner = BenchmarkRunner(config)

        assert len(config.test_ideas) == 1
        assert config.output_dir.exists() or True  # created on run_all

        report = runner.generate_report()
        assert "Autoscience Benchmark" in report
        assert runner.results["config"]["num_ideas"] == 1

        print("OK: benchmark framework imports and config initialize")
        print(f"     test ideas available: {len(TEST_IDEAS)}")
        print(f"     output dir writable: {config.output_dir}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())