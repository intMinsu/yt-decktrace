from __future__ import annotations

import importlib.metadata
import os
import shutil
import subprocess
from pathlib import Path

_DLL_HANDLES: list[object] = []


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def find_ffmpeg() -> Path | None:
    """Find FFmpeg in PATH, an override directory, or a nearby portable install."""
    from_path = shutil.which("ffmpeg")
    if from_path:
        return Path(from_path)

    override = os.environ.get("YT_DECKTRACE_FFMPEG_DIR")
    candidates = []
    if override:
        candidates.append(Path(override))
    root = project_root()
    candidates.extend((root / "tools" / "ffmpeg" / "bin", root.parent / "tools" / "ffmpeg" / "bin"))

    executable = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    for directory in candidates:
        candidate = directory / executable
        if candidate.is_file():
            return candidate
    return None


def ffmpeg_version(path: Path) -> str:
    result = subprocess.run(
        [str(path), "-version"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.splitlines()[0]


def register_nvidia_dll_directories() -> list[Path]:
    """Make DLLs shipped by NVIDIA PyPI wheels visible to CTranslate2 on Windows."""
    if os.name != "nt":
        return []

    registered: list[Path] = []
    wheel_paths = {
        "nvidia-cublas-cu12": Path("nvidia/cublas/bin"),
        "nvidia-cudnn-cu12": Path("nvidia/cudnn/bin"),
    }
    for distribution_name, relative in wheel_paths.items():
        try:
            distribution = importlib.metadata.distribution(distribution_name)
        except importlib.metadata.PackageNotFoundError:
            continue
        directory = Path(distribution.locate_file(relative)).resolve()
        if not directory.is_dir():
            continue
        if hasattr(os, "add_dll_directory"):
            _DLL_HANDLES.append(os.add_dll_directory(str(directory)))
        os.environ["PATH"] = f"{directory}{os.pathsep}{os.environ.get('PATH', '')}"
        registered.append(directory)
    return registered
