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
    is_original: bool = False


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


def _language_base(language: str) -> str:
    normalized = language.lower().replace("_", "-")
    if normalized.endswith("-orig"):
        normalized = normalized.removesuffix("-orig")
    return normalized.split("-", maxsplit=1)[0]


def caption_language_code(language: str) -> str:
    """Return a normalized language code without yt-dlp's ``-orig`` suffix."""
    normalized = language.replace("_", "-")
    return normalized.removesuffix("-orig")


def _supported_tracks(tracks: dict[str, list[dict[str, Any]]]) -> list[str]:
    return [language for language, formats in tracks.items() if _pick_format(formats)]


def _ordered_language_matches(languages: list[str], requested: str) -> list[str]:
    requested_normalized = requested.lower().replace("_", "-")
    requested_base = _language_base(requested_normalized)
    exact = [item for item in languages if item.lower() == requested_normalized]
    base_exact = [
        item
        for item in languages
        if item not in exact and item.lower() == requested_base
    ]
    regional = [
        item
        for item in languages
        if item not in exact
        and item not in base_exact
        and _language_base(item) == requested_base
    ]
    return exact + base_exact + regional


def _make_choice(
    tracks: dict[str, list[dict[str, Any]]],
    language: str,
    *,
    source: str,
    original_language: str | None,
) -> CaptionChoice | None:
    extension = _pick_format(tracks[language])
    if extension is None:
        return None
    is_original = language.lower().endswith("-orig") or (
        original_language is not None
        and _language_base(language) == _language_base(original_language)
    )
    return CaptionChoice(language, extension, source, is_original)


def choose_caption(
    info: dict[str, Any],
    requested_language: str = "original",
) -> CaptionChoice | None:
    """Choose an authored or automatic caption track with explicit provenance."""
    if requested_language not in {"original", "ko", "en"}:
        raise ValueError("caption language must be one of: original, ko, en")

    authored = info.get("subtitles") or {}
    automatic = info.get("automatic_captions") or {}
    original_language = info.get("language")
    authored_languages = _supported_tracks(authored)
    automatic_languages = _supported_tracks(automatic)

    if requested_language == "original":
        if isinstance(original_language, str) and original_language:
            for language in _ordered_language_matches(authored_languages, original_language):
                choice = _make_choice(
                    authored,
                    language,
                    source="authored",
                    original_language=original_language,
                )
                if choice:
                    return choice

        original_automatic = [
            language for language in automatic_languages if language.lower().endswith("-orig")
        ]
        if isinstance(original_language, str) and original_language:
            matching_original = _ordered_language_matches(
                original_automatic,
                original_language,
            )
            original_automatic = matching_original + [
                language for language in original_automatic if language not in matching_original
            ]
        for language in original_automatic:
            choice = _make_choice(
                automatic,
                language,
                source="automatic",
                original_language=original_language,
            )
            if choice:
                return choice

        if isinstance(original_language, str) and original_language:
            for language in _ordered_language_matches(automatic_languages, original_language):
                choice = _make_choice(
                    automatic,
                    language,
                    source="automatic",
                    original_language=original_language,
                )
                if choice:
                    return choice

        if len(authored_languages) == 1:
            return _make_choice(
                authored,
                authored_languages[0],
                source="authored",
                original_language=original_language,
            )
        return None

    original_base = (
        _language_base(original_language)
        if isinstance(original_language, str) and original_language
        else None
    )
    for language in _ordered_language_matches(authored_languages, requested_language):
        choice = _make_choice(
            authored,
            language,
            source="authored",
            original_language=original_language,
        )
        if choice:
            return choice

    automatic_matches = _ordered_language_matches(automatic_languages, requested_language)
    if original_base == requested_language:
        originals = [item for item in automatic_matches if item.lower().endswith("-orig")]
        automatic_matches = originals + [item for item in automatic_matches if item not in originals]
    for language in automatic_matches:
        choice = _make_choice(
            automatic,
            language,
            source="automatic",
            original_language=original_language,
        )
        if choice:
            return choice
    return None


def choose_korean_caption(info: dict[str, Any]) -> CaptionChoice | None:
    """Backward-compatible wrapper for callers selecting Korean captions."""
    return choose_caption(info, "ko")


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
    caption_language: str = "original",
    force: bool = False,
) -> IngestResult:
    info = inspect_youtube(url)
    video_id = str(info["id"])
    run_dir = output_root.resolve() / video_id
    source_dir = run_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = source_dir / "metadata.json"

    choice = (
        None
        if caption_policy == "whisper"
        else choose_caption(info, requested_language=caption_language)
    )
    if caption_policy == "youtube" and choice is None:
        raise RuntimeError(
            f"No {caption_language} authored or automatic YouTube caption track was found"
        )

    video_candidates = _video_candidates(source_dir)
    caption_candidates = _caption_candidates(source_dir, choice)
    needs_video = force or not video_candidates
    needs_caption = choice is not None and (force or not caption_candidates)
    if needs_video or needs_caption:
        options: dict[str, Any] = {
            "quiet": False,
            "noplaylist": True,
            "retries": 10,
            "fragment_retries": 10,
            "format": "bestvideo*+bestaudio[ext=m4a]/bestvideo*+bestaudio/best",
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
