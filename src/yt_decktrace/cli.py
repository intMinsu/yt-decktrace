from __future__ import annotations

import importlib.util
import shutil

import typer
from rich.console import Console
from rich.table import Table

from yt_decktrace import __version__

app = typer.Typer(no_args_is_help=True, help="Prepare YouTube presentations for LLM analysis.")
console = Console()


@app.command()
def doctor() -> None:
    """Check the local video and CUDA runtime prerequisites."""
    table = Table(title=f"yt-decktrace {__version__}")
    table.add_column("Component")
    table.add_column("Status")

    ffmpeg = shutil.which("ffmpeg")
    nvidia_smi = shutil.which("nvidia-smi")
    table.add_row("FFmpeg", ffmpeg or "not found")
    table.add_row("NVIDIA driver", nvidia_smi or "not found")

    cuda_status = "faster-whisper not installed"
    if importlib.util.find_spec("ctranslate2") is not None:
        import ctranslate2

        cuda_status = f"{ctranslate2.get_cuda_device_count()} CUDA device(s)"
    table.add_row("CTranslate2", cuda_status)
    console.print(table)


@app.command()
def analyze(
    source: str = typer.Argument(..., help="YouTube URL."),
    asr: str = typer.Option("auto", help="Caption policy: auto, youtube, or whisper."),
) -> None:
    """Analyze a YouTube presentation (pipeline implementation follows next)."""
    console.print(f"[yellow]Pipeline scaffold ready:[/] source={source!r}, asr={asr!r}")
    raise typer.Exit(code=2)
