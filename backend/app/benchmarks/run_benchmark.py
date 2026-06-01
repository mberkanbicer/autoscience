"""Evaluation and benchmarking framework.

Run: python -m app.benchmarks.run_benchmark --output ./benchmark_results
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


# Test idea set — diverse research topics across domains
TEST_IDEAS = [
    "Can transformer-based models effectively predict protein-ligand binding affinity from sequence data alone?",
    "To what extent do adversarial training methods improve out-of-distribution generalization in medical image classification?",
    "How does in-context learning in large language models compare to fine-tuning for low-resource machine translation?",
    "Can differentiable neural architecture search produce architectures competitive with hand-designed ones in computer vision?",
    "What is the relationship between model scale and factual accuracy in autoregressive language models?",
    "Are graph neural networks effective for predicting molecular properties in drug discovery pipelines?",
    "How do self-supervised learning representations transfer across different downstream NLP tasks compared to supervised pretraining?",
    "Can reinforcement learning from human feedback reduce hallucination in large language models more effectively than supervised fine-tuning?",
    "What is the impact of training data composition on bias amplification in language models across demographic groups?",
    "To what extent can sparse mixture-of-experts models match dense model performance at reduced computational cost?",
    "How effective are current watermarking techniques for detecting AI-generated text across different domains and generation settings?",
    "What is the relationship between tokenization strategy and multilingual model performance on morphologically rich languages?",
]


class BenchmarkConfig:
    """Configuration for benchmark runs."""

    def __init__(
        self,
        output_dir: str = "./benchmark_results",
        test_ideas: list[str] | None = None,
        num_cycles: int = 1,
        max_papers_per_run: int = 15,
        enable_scoring: bool = True,
        enable_skill_reuse: bool = True,
    ):
        self.output_dir = Path(output_dir)
        self.test_ideas = test_ideas or TEST_IDEAS
        self.num_cycles = num_cycles
        self.max_papers_per_run = max_papers_per_run
        self.enable_scoring = enable_scoring
        self.enable_skill_reuse = enable_skill_reuse


class BenchmarkRunner:
    """Runs benchmarks and collects metrics."""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.results: dict[str, Any] = {
            "config": {
                "num_ideas": len(config.test_ideas),
                "num_cycles": config.num_cycles,
                "max_papers_per_run": config.max_papers_per_run,
            },
            "runs": [],
            "metrics": {},
        }

    async def run_single_evaluation(
        self,
        idea: str,
        cycle: int = 0,
    ) -> dict[str, Any]:
        """Run a single research cycle and collect metrics."""
        from ..services.orchestrator import ResearchOrchestrator
        from ..database import AsyncSessionLocal

        start_time = time.time()

        async with AsyncSessionLocal() as db:
            from ..llm.router import create_default_router
            from ..connectors.manager import create_default_manager

            llm = create_default_router()
            connectors = create_default_manager()

            orchestrator = ResearchOrchestrator(
                db=db,
                llm_router=llm,
                connector_manager=connectors,
            )

            # Create project and run
            try:
                result = await orchestrator.run_research(
                    project_id="benchmark",
                    idea_text=idea,
                    run_type="user_directed",
                    flexibility=0.6,
                )

                elapsed = time.time() - start_time

                metrics = {
                    "idea": idea[:100],
                    "cycle": cycle,
                    "duration_seconds": round(elapsed, 2),
                    "papers_found": len(result.papers) if result else 0,
                    "clusters": len(result.clusters) if result else 0,
                    "conflicts": len(result.conflicts) if result else 0,
                    "questions": len(result.questions) if result else 0,
                    "hypotheses": len(result.hypotheses) if result else 0,
                    "scores": len(result.scores) if result else 0,
                    "sources_searched": result.sources_searched if result else 0,
                    "success": True,
                }
            except Exception as e:
                elapsed = time.time() - start_time
                metrics = {
                    "idea": idea[:100],
                    "cycle": cycle,
                    "duration_seconds": round(elapsed, 2),
                    "success": False,
                    "error": str(e),
                }

        return metrics

    async def run_all(self):
        """Run all benchmark evaluations."""
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        for i, idea in enumerate(self.config.test_ideas[:3]):  # Limit to 3 for speed
            logger.info("benchmark_start", idea=idea[:60], index=i)
            result = await self.run_single_evaluation(idea)
            self.results["runs"].append(result)

            # Save intermediate results
            self._save_results()

        self._compute_metrics()
        logger.info(
            "benchmark_complete",
            total_runs=len(self.results["runs"]),
            avg_duration=self.results["metrics"].get("avg_duration"),
        )
        return self.results

    def _compute_metrics(self):
        """Compute aggregate metrics."""
        runs = self.results["runs"]
        if not runs:
            return

        successful = [r for r in runs if r.get("success")]
        self.results["metrics"] = {
            "total_runs": len(runs),
            "successful_runs": len(successful),
            "success_rate": len(successful) / len(runs) if runs else 0,
            "avg_duration": sum(r.get("duration_seconds", 0) for r in runs) / len(runs) if runs else 0,
            "avg_papers": sum(r.get("papers_found", 0) for r in successful) / len(successful) if successful else 0,
            "avg_conflicts": sum(r.get("conflicts", 0) for r in successful) / len(successful) if successful else 0,
            "avg_hypotheses": sum(r.get("hypotheses", 0) for r in successful) / len(successful) if successful else 0,
            "total_sources_searched": sum(r.get("sources_searched", 0) for r in successful),
        }

    def _save_results(self):
        """Save results to disk."""
        output_path = self.config.output_dir / "benchmark_results.json"
        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info("benchmark_saved", path=str(output_path))

    def generate_report(self) -> str:
        """Generate a human-readable benchmark report."""
        m = self.results["metrics"]
        report = [
            "# Benchmark Report",
            "",
            f"**Test Ideas**: {len(self.config.test_ideas)}",
            f"**Runs**: {m.get('total_runs', 0)} ({m.get('successful_runs', 0)} successful)",
            f"**Success Rate**: {m.get('success_rate', 0) * 100:.1f}%",
            "",
            "## Performance",
            f"- Avg Duration: {m.get('avg_duration', 0):.1f}s",
            f"- Avg Papers Found: {m.get('avg_papers', 0):.1f}",
            f"- Avg Conflicts: {m.get('avg_conflicts', 0):.1f}",
            f"- Avg Hypotheses: {m.get('avg_hypotheses', 0):.1f}",
            f"- Total Sources Searched: {m.get('total_sources_searched', 0)}",
            "",
            "## Run Details",
        ]
        for r in self.results["runs"]:
            status = "✓" if r.get("success") else "✗"
            report.append(
                f"- {status} {r.get('idea', '')[:60]}... "
                f"({r.get('duration_seconds', 0):.1f}s, "
                f"{r.get('papers_found', 0)} papers, "
                f"{r.get('hypotheses', 0)} hypotheses)"
            )

        report.extend([
            "",
            "## Limitations",
            "- Time estimates depend on LLM provider speed",
            "- Paper counts depend on academic database availability",
            "- Scoring requires API key",
            "",
            "---",
            "*Auto-generated by Autoscience Benchmark Framework*",
        ])
        return "\n".join(report)


def main():
    """Run the benchmark CLI."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Autoscience benchmark")
    parser.add_argument("--output", default="./benchmark_results", help="Output directory")
    parser.add_argument("--ideas", type=int, default=3, help="Number of test ideas to evaluate (max 12)")
    parser.add_argument("--cycles", type=int, default=1, help="Number of cycles per idea")

    args = parser.parse_args()

    config = BenchmarkConfig(
        output_dir=args.output,
        test_ideas=TEST_IDEAS[:args.ideas],
        num_cycles=args.cycles,
    )

    runner = BenchmarkRunner(config)
    results = asyncio.run(runner.run_all())

    print(runner.generate_report())
    return results


if __name__ == "__main__":
    main()
