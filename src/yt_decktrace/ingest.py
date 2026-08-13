from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL

from yt_decktrace.runtime import find_ffmpeg
from yt_decktrace.utils import write_json

MEDIA_EXTENSIONS = {".m4v", ".mkv", ".mov", ".mp4", ".webm"}


@dataclass(frozen=True)
class CaptionChoice:
    language: str
    extension: str
    source: str


@dataclass(frozen=True)
class IngestResult:
    video_id: str
    source_url: str
    title: str
    duration: float
    run_dir: Path
    video_path: Path
    metadata_path: Path
    caption_path: Path | None
    caption_choice: CaptionChoice | None


def _pick_format(formats: list[dict[str, Any]]) -> str | None:
    available = {item.get("ext") for item in formats}
    for extension in ("json3", "vtt", "srt"):
        if extension in available:
            return extension
    return None


def _video_candidates(source_dir: Path) -> list[Path]:
    return [
        path
        for path in source_dir.glob("video.*")
        if path.suffix.lower() in MEDIA_EXTENSIONS
        and re.search(r"\.f\d+\.", path.name, flags=re.IGNORECASE) is None
    ]


def _caption_candidates(source_dir: Path, choice: CaptionChoice | None) -> list[Path]:
    if choice is None:
        return []
    return list(source_dir.glob(f"*.{choice.language}.{choice.extension}"))


def choose_korean_caption(info: dict[str, Any]) -> CaptionChoice | None:
    """Prefer authored Korean captions, then YouTube's original Korean ASR track."""
    authored = info.get("subtitles") or {}
    automatic = info.get("automatic_captions") or {}
    language_order = ("ko", "ko-KR", "ko-orig")

    for source_name, tracks in (("authored", authored), ("automatic", automatic)):
        keys = list(tracks)
        ordered = [key for key in language_order if key in tracks]
        ordered.extend(key for key in keys if key.startswith("ko") and key not in ordered)
        for language in ordered:
            extension = _pick_format(tracks[language])
            if extension:
                return CaptionChoice(language, extension, source_name)
    return None


def inspect_youtube(url: str) -> dict[str, Any]:
    options = {"quiet": True, "no_warnings": True, "noplaylist": True}
    with YoutubeDL(options) as downloader:
        info = downloader.extract_info(url, download=False)
    if info is None or info.get("_type") == "playlist":
        raise ValueError("Expected a single YouTube video URL")
    return info


def _metadata(info: dict[str, Any], source_url: str, choice: CaptionChoice | None) -> dict[str, Any]:
    return {
        "id": info["id"],
        "title": info.get("title") or info["id"],
        "source_url": info.get("webpage_url") or source_url,
        "channel": info.get("channel") or info.get("uploader"),
        "duration": float(info.get("duration") or 0),
        "upload_date": info.get("upload_date"),
        "description": info.get("description"),
        "chapters": info.get("chapters") or [],
        "caption": asdict(choice) if choice else None,
    }


def ingest_youtube(
    url: str,
    output_root: Path,
    *,
    caption_policy: str = "auto",
    force: bool = False,
) -> IngestResult:
    info = inspect_youtube(url)
    video_id = str(info["id"])
    run_dir = output_root.resolve() / video_id
    source_dir = run_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = source_dir / "metadata.json"

    choice = None if caption_policy == "whisper" else choose_korean_caption(info)
    if caption_policy == "youtube" and choice is None:
        raise RuntimeError("No Korean authored or automatic YouTube caption track was found")

    video_candidates = _video_candidates(source_dir)
    caption_candidates = _caption_candidates(source_dir, choice)
    needs_video = force or not video_candidates
    needs_caption = choice is not None and (force or not caption_candidates)
    if needs_video or needs_caption:
        options: dict[str, Any] = {
            "quiet": False,
            "noplaylist": True,
            "format": "bestvideo*+bestaudio/best",
            "merge_output_format": "mkv",
            "overwrites": force,
            "skip_download": not needs_video,
            "outtmpl": {
                "default": str(source_dir / "video.%(ext)s"),
                "subtitle": str(source_dir / "captions.%(ext)s"),
            },
        }
        if needs_video:
            ffmpeg = find_ffmpeg()
            if ffmpeg is None:
                raise RuntimeError(
                    "FFmpeg was not found. Add it to PATH or set YT_DECKTRACE_FFMPEG_DIR."
                )
            options["ffmpeg_location"] = str(ffmpeg.parent)
        if needs_caption and choice:
            options.update(
                {
                    "writesubtitles": choice.source == "authored",
                    "writeautomaticsub": choice.source == "automatic",
                    "subtitleslangs": [choice.language],
                    "subtitlesformat": choice.extension,
                }
            )
        with YoutubeDL(options) as downloader:
            downloader.download([url])

    video_candidates = _video_candidates(source_dir)
    if not video_candidates:
        raise RuntimeError("yt-dlp finished without producing a video file")
    video_path = max(video_candidates, key=lambda path: path.stat().st_size)

    caption_path = None
    if choice:
        caption_candidates = _caption_candidates(source_dir, choice)
        if caption_candidates:
            caption_path = max(caption_candidates, key=lambda path: path.stat().st_mtime)

    metadata = _metadata(info, url, choice)
    write_json(metadata_path, metadata)
    return IngestResult(
        video_id=video_id,
        source_url=metadata["source_url"],
        title=metadata["title"],
        duration=metadata["duration"],
        run_dir=run_dir,
        video_path=video_path,
        metadata_path=metadata_path,
        caption_path=caption_path,
        caption_choice=choice,
    )
