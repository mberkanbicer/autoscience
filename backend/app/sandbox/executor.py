"""Docker-based sandbox for safe code execution."""

import asyncio
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class SandboxConfig:
    """Configuration for the sandbox."""

    docker_image: str = "python:3.11-slim"
    timeout_seconds: int = 300
    memory_limit: str = "512m"
    cpu_limit: float = 1.0
    max_output_size: int = 10 * 1024 * 1024  # 10MB
    network_enabled: bool = False
    allowed_packages: list[str] = field(default_factory=lambda: [
        "numpy", "pandas", "scipy", "scikit-learn",
        "matplotlib", "seaborn", "statsmodels",
    ])


@dataclass
class ExecutionResult:
    """Result from sandbox execution."""

    execution_id: str
    status: str  # success, failed, timeout
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    duration_seconds: float = 0
    output_files: list[str] = field(default_factory=list)
    error: str | None = None


class SandboxExecutor:
    """Executor for running code in Docker sandbox."""

    def __init__(self, config: SandboxConfig | None = None):
        self.config = config or SandboxConfig()
        self.work_dir = Path(tempfile.mkdtemp(prefix="autoscience_sandbox_"))

    async def execute(
        self,
        script: str,
        datasets: dict[str, bytes] | None = None,
        timeout: int | None = None,
    ) -> ExecutionResult:
        """Execute a script in the sandbox."""
        execution_id = str(uuid4())
        timeout = timeout or self.config.timeout_seconds

        logger.info(
            "sandbox_execution_started",
            execution_id=execution_id,
            script_length=len(script),
        )

        try:
            # Prepare execution directory
            exec_dir = self.work_dir / execution_id
            exec_dir.mkdir(parents=True, exist_ok=True)

            # Write script
            script_path = exec_dir / "analysis.py"
            script_path.write_text(script)

            # Write datasets
            if datasets:
                data_dir = exec_dir / "data"
                data_dir.mkdir(exist_ok=True)
                for name, content in datasets.items():
                    (data_dir / name).write_bytes(content)

            # Create output directory
            output_dir = exec_dir / "output"
            output_dir.mkdir(exist_ok=True)

            # Build Docker command
            cmd = self._build_docker_command(exec_dir, output_dir, timeout)

            # Execute
            start_time = asyncio.get_event_loop().time()
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
                duration = asyncio.get_event_loop().time() - start_time

                # Collect output files
                output_files = self._collect_output_files(output_dir)

                result = ExecutionResult(
                    execution_id=execution_id,
                    status="success" if process.returncode == 0 else "failed",
                    stdout=stdout.decode(errors="replace")[:self.config.max_output_size],
                    stderr=stderr.decode(errors="replace")[:self.config.max_output_size],
                    return_code=process.returncode or 0,
                    duration_seconds=duration,
                    output_files=output_files,
                )

            except asyncio.TimeoutError:
                process.kill()
                result = ExecutionResult(
                    execution_id=execution_id,
                    status="timeout",
                    error=f"Execution timed out after {timeout} seconds",
                )

            logger.info(
                "sandbox_execution_completed",
                execution_id=execution_id,
                status=result.status,
                duration=result.duration_seconds,
            )

            return result

        except Exception as e:
            logger.error("sandbox_execution_failed", error=str(e))
            return ExecutionResult(
                execution_id=execution_id,
                status="failed",
                error=str(e),
            )

    def _build_docker_command(
        self,
        exec_dir: Path,
        output_dir: Path,
        timeout: int,
    ) -> str:
        """Build Docker command for execution."""
        cmd_parts = [
            "docker run",
            "--rm",
            f"--memory={self.config.memory_limit}",
            f"--cpus={self.config.cpu_limit}",
            f"--timeout={timeout}",
            f"-v {exec_dir}:/app",
            f"-v {output_dir}:/output",
            "-w /app",
        ]

        if not self.config.network_enabled:
            cmd_parts.append("--network=none")

        cmd_parts.append(self.config.docker_image)
        cmd_parts.append("python /app/analysis.py")

        return " ".join(cmd_parts)

    def _collect_output_files(self, output_dir: Path) -> list[str]:
        """Collect output files from the output directory."""
        files = []
        if output_dir.exists():
            for f in output_dir.rglob("*"):
                if f.is_file():
                    files.append(str(f.relative_to(output_dir)))
        return files

    def read_output_file(self, execution_id: str, filename: str) -> bytes | None:
        """Read an output file from a completed execution."""
        file_path = self.work_dir / execution_id / "output" / filename
        if file_path.exists():
            return file_path.read_bytes()
        return None

    def cleanup(self, execution_id: str) -> None:
        """Clean up execution directory."""
        exec_dir = self.work_dir / execution_id
        if exec_dir.exists():
            import shutil
            shutil.rmtree(exec_dir)


class ScriptGenerator:
    """Generator for analysis scripts."""

    def __init__(self):
        self.imports = [
            "import pandas as pd",
            "import numpy as np",
            "import matplotlib.pyplot as plt",
            "import json",
            "import os",
        ]

    def generate_analysis_script(
        self,
        analysis_type: str,
        dataset_info: dict[str, Any],
        hypothesis: str,
        metrics: list[str],
    ) -> str:
        """Generate an analysis script."""
        script_parts = [
            "# Auto-generated analysis script",
            f"# Analysis type: {analysis_type}",
            f"# Hypothesis: {hypothesis}",
            "",
            *self.imports,
            "",
            "# Load data",
            self._generate_data_loading(dataset_info),
            "",
            "# Analysis",
            self._generate_analysis(analysis_type, metrics),
            "",
            "# Save results",
            self._generate_save_results(),
        ]

        return "\n".join(script_parts)

    def _generate_data_loading(self, dataset_info: dict[str, Any]) -> str:
        """Generate data loading code."""
        data_path = dataset_info.get("path", "data/dataset.csv")
        return f"""
# Load dataset
df = pd.read_csv('{data_path}')
print(f"Loaded dataset: {{len(df)}} rows, {{len(df.columns)}} columns")
print(f"Columns: {{list(df.columns)}}")
"""

    def _generate_analysis(self, analysis_type: str, metrics: list[str]) -> str:
        """Generate analysis code based on type."""
        if analysis_type == "comparison":
            return self._generate_comparison_analysis(metrics)
        elif analysis_type == "correlation":
            return self._generate_correlation_analysis(metrics)
        elif analysis_type == "regression":
            return self._generate_regression_analysis(metrics)
        else:
            return self._generate_descriptive_analysis(metrics)

    def _generate_comparison_analysis(self, metrics: list[str]) -> str:
        """Generate comparison analysis code."""
        return """
# Comparison analysis
results = {}

for metric in """ + str(metrics) + """:
    if metric in df.columns:
        results[metric] = {
            'mean': df[metric].mean(),
            'std': df[metric].std(),
            'min': df[metric].min(),
            'max': df[metric].max(),
        }

# Create comparison visualization
fig, axes = plt.subplots(1, len(metrics), figsize=(5*len(metrics), 4))
if len(metrics) == 1:
    axes = [axes]

for ax, metric in zip(axes, metrics):
    if metric in df.columns:
        df[metric].hist(ax=ax, bins=20)
        ax.set_title(metric)
        ax.set_xlabel(metric)
        ax.set_ylabel('Count')

plt.tight_layout()
plt.savefig('output/comparison_plot.png', dpi=150, bbox_inches='tight')
plt.close()

# Print results
print("\\nComparison Results:")
print(json.dumps(results, indent=2))
"""

    def _generate_correlation_analysis(self, metrics: list[str]) -> str:
        """Generate correlation analysis code."""
        return """
# Correlation analysis
numeric_cols = df[metrics].select_dtypes(include=[np.number]).columns
corr_matrix = df[numeric_cols].corr()

# Visualize correlation matrix
plt.figure(figsize=(10, 8))
plt.imshow(corr_matrix, cmap='coolwarm', aspect='auto')
plt.colorbar()
plt.xticks(range(len(numeric_cols)), numeric_cols, rotation=45)
plt.yticks(range(len(numeric_cols)), numeric_cols)
plt.title('Correlation Matrix')
plt.tight_layout()
plt.savefig('output/correlation_matrix.png', dpi=150, bbox_inches='tight')
plt.close()

# Print correlations
print("\\nCorrelation Matrix:")
print(corr_matrix.to_string())
"""

    def _generate_regression_analysis(self, metrics: list[str]) -> str:
        """Generate regression analysis code."""
        return """
# Simple regression analysis
from scipy import stats

results = {}
numeric_cols = df[metrics].select_dtypes(include=[np.number]).columns

if len(numeric_cols) >= 2:
    x_col = numeric_cols[0]
    y_col = numeric_cols[1]
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        df[x_col].dropna(), df[y_col].dropna()
    )
    
    results = {
        'x': x_col,
        'y': y_col,
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value**2,
        'p_value': p_value,
        'std_error': std_err,
    }
    
    # Visualization
    plt.figure(figsize=(8, 6))
    plt.scatter(df[x_col], df[y_col], alpha=0.5)
    plt.plot(df[x_col], slope * df[x_col] + intercept, 'r-', label='Regression line')
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(f'{y_col} vs {x_col}')
    plt.legend()
    plt.tight_layout()
    plt.savefig('output/regression_plot.png', dpi=150, bbox_inches='tight')
    plt.close()

print("\\nRegression Results:")
print(json.dumps(results, indent=2))
"""

    def _generate_descriptive_analysis(self, metrics: list[str]) -> str:
        """Generate descriptive statistics."""
        return """
# Descriptive statistics
results = {}

for metric in """ + str(metrics) + """:
    if metric in df.columns:
        results[metric] = {
            'count': int(df[metric].count()),
            'mean': float(df[metric].mean()),
            'std': float(df[metric].std()),
            'min': float(df[metric].min()),
            '25%': float(df[metric].quantile(0.25)),
            '50%': float(df[metric].quantile(0.50)),
            '75%': float(df[metric].quantile(0.75)),
            'max': float(df[metric].max()),
        }

print("\\nDescriptive Statistics:")
print(json.dumps(results, indent=2))
"""

    def _generate_save_results(self) -> str:
        """Generate code to save results."""
        return """
# Save results to JSON
with open('output/results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\\nResults saved to output/results.json")
print("Plots saved to output/")
"""
