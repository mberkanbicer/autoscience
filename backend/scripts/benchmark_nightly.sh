#!/usr/bin/env bash
# Nightly benchmark smoke — run via cron: 0 2 * * * /path/to/benchmark_nightly.sh
set -euo pipefail
cd "$(dirname "$0")/.."
STAMP=$(date +%Y%m%d)
OUT="./benchmark_results/nightly-${STAMP}"
mkdir -p "$OUT"
python scripts/benchmark_smoke.py | tee "${OUT}/smoke.log"
python -m app.benchmarks.run_benchmark --output "$OUT" --ideas 1 --cycles 1 2>&1 | tee "${OUT}/run.log" || true
echo "Nightly benchmark complete: $OUT"