from __future__ import annotations

import importlib.metadata
import platform
import shutil
import subprocess
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from yt_decktrace import __version__
from yt_decktrace.pack import pack_run
from yt_decktrace.pipeline import analyze_youtube
from yt_decktrace.runtime import ffmpeg_version, find_ffmpeg, register_nvidia_dll_directories

app = typer.Typer(no_args_is_help=True, help="Prepare YouTube presentations for LLM analysis.")
console = Console()


class AsrMode(str, Enum):
    auto = "auto"
    youtube = "youtube"
    whisper = "whisper"


class WhisperLanguage(str, Enum):
    auto = "auto"
    ko = "ko"
    en = "en"


def _package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


@app.command()
def doctor() -> None:
    """Check local video and speech transcription prerequisites."""
    table = Table(title=f"yt-decktrace {__version__}")
    table.add_column("Component")
    table.add_column("Status")
    system = platform.system()
    table.add_row("Platform", f"{system} {platform.machine()}")

    ffmpeg = find_ffmpeg()
    if ffmpeg:
        try:
            ffmpeg_status = f"{ffmpeg} ({ffmpeg_version(ffmpeg)})"
        except (OSError, subprocess.SubprocessError) as error:
            ffmpeg_status = f"{ffmpeg} (failed: {error})"
    else:
        ffmpeg_status = "not found"
    table.add_row("FFmpeg", ffmpeg_status)

    if system == "Windows":
        nvidia_smi = shutil.which("nvidia-smi")
        if nvidia_smi:
            query = subprocess.run(
                [nvidia_smi, "--query-gpu=name,driver_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            driver_status = query.stdout.strip() or nvidia_smi
        else:
            driver_status = "not found (CPU transcription remains available)"
        table.add_row("NVIDIA driver", driver_status)

        dll_directories = register_nvidia_dll_directories()
        table.add_row(
            "NVIDIA wheel DLLs",
            "\n".join(map(str, dll_directories)) or "not installed (use the cuda environment)",
        )

    try:
        import ctranslate2

        cuda_devices = ctranslate2.get_cuda_device_count()
        if cuda_devices:
            whisper_device = f"CUDA ({cuda_devices} device(s))"
        elif system == "Darwin":
            whisper_device = "CPU (Metal/MPS is not used by CTranslate2)"
        else:
            whisper_device = "CPU"
        ctranslate2_status = _package_version("ctranslate2")
    except (ImportError, OSError, RuntimeError) as error:
        ctranslate2_status = f"failed: {error}"
        whisper_device = "unavailable"
    table.add_row("CTranslate2", ctranslate2_status)
    table.add_row("Whisper device", whisper_device)
    table.add_row("faster-whisper", _package_version("faster-whisper"))
    table.add_row("yt-dlp", _package_version("yt-dlp"))
    console.print(table)


@app.command()
def analyze(
    source: Annotated[str, typer.Argument(help="YouTube video URL.")],
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Run directory root.")
    ] = Path("runs"),
    asr: Annotated[
        AsrMode,
        typer.Option(help="Use YouTube Korean captions when available, or local Whisper."),
    ] = AsrMode.auto,
    model: Annotated[
        str, typer.Option(help="faster-whisper model used for local ASR.")
    ] = "large-v3",
    language: Annotated[
        WhisperLanguage,
        typer.Option(help="Spoken language for Whisper; auto enables language detection."),
    ] = WhisperLanguage.auto,
    sample_fps: Annotated[
        float, typer.Option(min=0.1, max=10.0, help="Frame sample rate.")
    ] = 1.0,
    threshold: Annotated[
        int, typer.Option(min=1, max=64, help="Perceptual hash change threshold.")
    ] = 10,
    min_gap: Annotated[
        float, typer.Option(min=0.0, help="Minimum seconds between saved frames.")
    ] = 2.0,
    force: Annotated[
        bool, typer.Option(help="Redownload source files and regenerate artifacts.")
    ] = False,
) -> None:
    """Create changed-frame and timestamped-transcript context from a YouTube video."""
    console.print(f"[cyan]Analyzing[/] {source}")
    context_path = analyze_youtube(
        source,
        output_root=output,
        asr=asr.value,
        whisper_model=model,
        whisper_language=language.value,
        sample_fps=sample_fps,
        change_threshold=threshold,
        min_gap=min_gap,
        force=force,
    )
    console.print(f"[green]Complete:[/] {context_path.resolve()}")


@app.command()
def pack(
    video_id: Annotated[str, typer.Argument(help="Completed run's YouTube video ID.")],
    runs_root: Annotated[
        Path, typer.Option("--runs-root", "-r", help="Run directory root.")
    ] = Path("runs"),
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Destination ZIP path.")
    ] = None,
    force: Annotated[
        bool, typer.Option(help="Replace an existing archive.")
    ] = False,
) -> None:
    """Package a completed run for analysis in GPT or another multimodal LLM."""
    result = pack_run(
        video_id,
        runs_root=runs_root,
        output_path=output,
        force=force,
    )
    size_mb = result.size_bytes / (1024 * 1024)
    console.print(
        f"[green]Packed[/] {result.frame_count} frames and {result.file_count} files "
        f"({size_mb:.2f} MiB): {result.archive_path}"
    )


if __name__ == "__main__":
    app()
