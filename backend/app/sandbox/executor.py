"""Isolated sandbox execution engine for scientific experiments."""

import asyncio
import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()

# Known artifact file extensions
ARTIFACT_EXTENSIONS = {".json", ".csv", ".tsv", ".png", ".svg", ".pdf", ".html", ".txt", ".npy", ".npz"}

# Maximum artifact file size (50 MB) — larger files are skipped to avoid OOM
MAX_ARTIFACT_SIZE = 50 * 1024 * 1024
MAX_ARTIFACT_SIZE_MB = 50


@dataclass
class SandboxResult:
    """Result of a sandbox execution."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    artifacts: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None


class SandboxExecutor:
    """Executes code in an isolated environment."""

    def __init__(
        self,
        artifact_dir: str | None = None,
        docker_image: str = "python:3.11-slim",
        timeout_seconds: int = 300,
        memory_limit: str = "512m",
        cpu_limit: float = 1.0,
    ):
        default_dir = Path(tempfile.gettempdir()) / "autoscience_sandbox"
        self.artifact_dir = Path(artifact_dir) if artifact_dir else default_dir
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.docker_image = docker_image
        self.timeout_seconds = timeout_seconds
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit

    async def run_python(
        self,
        code: str,
        requirements: list[str] | None = None,
        timeout_seconds: int | None = None,
    ) -> SandboxResult:
        """Run Python code in a temporary Docker container.

        The container mounts:
          - ``script`` at ``/app/experiment.py:ro``
          - An empty ``/app/outputs/`` directory (writable) for results

        After execution, any files written to ``/app/outputs/`` are harvested
        and attached to the returned ``SandboxResult``.
        """
        import time

        start_time = time.time()
        timeout = timeout_seconds or self.timeout_seconds

        # Create temporary working directory
        with tempfile.TemporaryDirectory(dir=self.artifact_dir) as tmp_dir:
            tmp_path = Path(tmp_dir)
            script_path = tmp_path / "experiment.py"
            script_path.write_text(code)

            # Create writable outputs directory for the container to write into
            outputs_path = tmp_path / "outputs"
            outputs_path.mkdir(parents=True, exist_ok=True)

            # Create requirements.txt if needed
            if requirements:
                req_path = tmp_path / "requirements.txt"
                req_path.write_text("\n".join(requirements))

            # Docker command
            docker_cmd = [
                "docker", "run", "--rm",
                "--network", "none",
                "--memory", self.memory_limit,
                f"--cpus={self.cpu_limit}",
                "--pids-limit", "64",
                "--user", "1000:1000",
                "--read-only",
                "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
                "-v", f"{script_path.absolute()}:/app/experiment.py:ro",
                "-v", f"{outputs_path.absolute()}:/app/outputs:rw",
                "-w", "/app",
                self.docker_image,
                "sh", "-c",
                (
                    f"pip install --user --quiet {' '.join(requirements or [])} && python experiment.py"
                    if requirements
                    else "python experiment.py"
                ),
            ]

            try:
                process = await asyncio.create_subprocess_exec(
                    *docker_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), timeout=timeout,
                    )
                    exit_code = process.returncode or 0
                except TimeoutError:
                    process.kill()
                    return SandboxResult(
                        success=False,
                        stdout="",
                        stderr="Execution timed out",
                        exit_code=-1,
                        duration_ms=int((time.time() - start_time) * 1000),
                        error_message=f"Timeout after {timeout}s",
                    )

                duration_ms = int((time.time() - start_time) * 1000)

                # Harvest any artifacts written to the outputs directory
                artifacts = await self.harvest_artifacts(outputs_path)

                return SandboxResult(
                    success=(exit_code == 0),
                    stdout=stdout.decode(),
                    stderr=stderr.decode(),
                    exit_code=exit_code,
                    duration_ms=duration_ms,
                    artifacts=artifacts,
                )

            except Exception as e:
                logger.error("sandbox_execution_failed", error=str(e), exc_info=True)
                return SandboxResult(
                    success=False,
                    stdout="",
                    stderr=str(e),
                    exit_code=-1,
                    duration_ms=int((time.time() - start_time) * 1000),
                    error_message=str(e),
                )

    async def harvest_artifacts(self, directory: Path) -> dict[str, Any]:
        """Scan *directory* for artifact files and return a structured dict.

        Recognised file types (by extension):

        ======== ==================================
        Type     Extension(s)
        ======== ==================================
        JSON     ``.json`` — parsed and included as dicts
        CSV/TSV  ``.csv``, ``.tsv`` — read with ``pandas`` if available, else raw text
        Images   ``.png``, ``.svg``, ``.pdf`` — returned as base64 data URIs
        Text     ``.txt``, ``.html`` — raw text content
        NumPy    ``.npy``, ``.npz`` — read with ``numpy`` if available, else skipped
        ======== ==================================

        Returns ``{"files": [...], "data": {...}}`` where ``files`` is a manifest
        and ``data`` contains parsed content for JSON and text files.
        """
        if not directory.is_dir():
            logger.warning("harvest_artifacts_not_a_directory", path=str(directory))
            return {"files": [], "data": {}}

        files_manifest: list[dict[str, Any]] = []
        data: dict[str, Any] = {}
        errors: list[str] = []

        for child in sorted(directory.iterdir()):
            if not child.is_file() or child.is_symlink():
                continue

            ext = child.suffix.lower()
            if ext not in ARTIFACT_EXTENSIONS:
                continue

            stat = child.stat()
            if stat.st_size > MAX_ARTIFACT_SIZE:
                logger.warning("harvest_artifact_skipped_large", filename=child.name, size_bytes=stat.st_size)
                errors.append(f"{child.name}: skipped (>{MAX_ARTIFACT_SIZE_MB}MB)")
                continue
            entry: dict[str, Any] = {
                "filename": child.name,
                "extension": ext,
                "size_bytes": stat.st_size,
                "modified_at": stat.st_mtime,
            }
            files_manifest.append(entry)

            try:
                if ext == ".json":
                    raw = child.read_text(encoding="utf-8", errors="replace")
                    data[child.stem] = json.loads(raw)

                elif ext in (".csv", ".tsv"):
                    raw = child.read_text(encoding="utf-8", errors="replace")
                    data[child.stem] = raw  # raw text; caller can parse

                elif ext in (".txt", ".html"):
                    data[child.stem] = child.read_text(
                        encoding="utf-8", errors="replace",
                    )

                elif ext in (".npy", ".npz"):
                    try:
                        import numpy as np  # fmt: skip
                        if ext == ".npy":
                            arr = np.load(str(child))
                            data[child.stem] = {
                                "shape": list(arr.shape),
                                "dtype": str(arr.dtype),
                            }
                        else:
                            npz = np.load(str(child))
                            data[child.stem] = {
                                "keys": list(npz.keys()),
                                "shapes": {k: list(npz[k].shape) for k in npz.keys()},
                            }
                            npz.close()
                    except ImportError:
                        # numpy not available in host process – skip binary files
                        errors.append(f"numpy not available to parse {child.name}")

                elif ext in (".png", ".svg", ".pdf"):
                    import base64
                    binary = child.read_bytes()
                    data[child.stem] = {
                        "mime_type": (
                            "image/png" if ext == ".png"
                            else "image/svg+xml" if ext == ".svg"
                            else "application/pdf"
                        ),
                        "data_uri": (
                            f"data:{'image/png' if ext == '.png' else 'image/svg+xml' if ext == '.svg' else 'application/pdf'};"
                            f"base64,{base64.b64encode(binary).decode('ascii')}"
                        ),
                        "size_bytes": len(binary),
                    }

            except Exception as exc:
                logger.warning(
                    "harvest_artifact_parse_failed",
                    filename=child.name,
                    error=str(exc),
                )
                errors.append(f"{child.name}: {exc}")

        result: dict[str, Any] = {
            "files": files_manifest,
            "data": data,
        }
        if errors:
            result["errors"] = errors
        return result


