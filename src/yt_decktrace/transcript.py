from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import pysubs2

from yt_decktrace.runtime import register_nvidia_dll_directories
from yt_decktrace.utils import format_timestamp, normalize_text, write_json, youtube_timestamp_url


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str
    id: str | None = None


@dataclass(frozen=True)
class TranscriptArtifacts:
    segments_path: Path
    markdown_path: Path
    source_digest: str
    segment_count: int


def parse_json3(path: Path) -> list[Segment]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    segments: list[Segment] = []
    for event in payload.get("events", []):
        text = normalize_text("".join(part.get("utf8", "") for part in event.get("segs", [])))
        if not text:
            continue
        start = float(event.get("tStartMs", 0)) / 1000
        duration = float(event.get("dDurationMs", 0)) / 1000
        segments.append(Segment(start=start, end=start + duration, text=text))
    return segments


def parse_subtitle(path: Path) -> list[Segment]:
    if path.suffix.lower() == ".json3":
        return parse_json3(path)
    subtitles = pysubs2.load(str(path), encoding="utf-8")
    return [
        Segment(
            start=line.start / 1000,
            end=line.end / 1000,
            text=normalize_text(line.plaintext),
        )
        for line in subtitles
        if normalize_text(line.plaintext)
    ]


def merge_segments(
    segments: Iterable[Segment],
    *,
    max_gap: float = 0.8,
    max_duration: float = 14.0,
    max_characters: int = 140,
) -> list[Segment]:
    """Merge adjacent caption fragments into compact, timestamped utterances."""
    merged: list[Segment] = []
    for item in sorted(segments, key=lambda segment: segment.start):
        if not merged:
            merged.append(item)
            continue
        previous = merged[-1]
        combined_text = normalize_text(f"{previous.text} {item.text}")
        can_merge = (
            item.start - previous.end <= max_gap
            and item.end - previous.start <= max_duration
            and len(combined_text) <= max_characters
        )
        if can_merge:
            if item.text == previous.text:
                combined_text = previous.text
            merged[-1] = Segment(previous.start, max(previous.end, item.end), combined_text)
        else:
            merged.append(item)
    return merged


def assign_segment_ids(segments: Iterable[Segment]) -> list[Segment]:
    """Return segments with deterministic identifiers suitable for translation alignment."""
    assigned: list[Segment] = []
    used: set[str] = set()
    for index, segment in enumerate(segments, start=1):
        identifier = segment.id or f"segment-{index:06d}"
        if identifier in used:
            raise ValueError(f"Duplicate transcript segment id: {identifier}")
        used.add(identifier)
        assigned.append(Segment(segment.start, segment.end, segment.text, identifier))
    return assigned


def segment_record(segment: Segment) -> dict[str, object]:
    if segment.id is None:
        raise ValueError("Transcript segments must have identifiers before serialization")
    return {
        "id": segment.id,
        "start": segment.start,
        "end": segment.end,
        "text": segment.text,
    }


def transcribe_with_whisper(
    media_path: Path,
    *,
    model_name: str,
    device: str = "auto",
    language: str = "auto",
) -> tuple[list[Segment], dict[str, object]]:
    register_nvidia_dll_directories()
    import ctranslate2
    from faster_whisper import WhisperModel

    selected_device = device
    if selected_device == "auto":
        selected_device = "cuda" if ctranslate2.get_cuda_device_count() else "cpu"
    compute_type = "int8_float16" if selected_device == "cuda" else "int8"

    try:
        model = WhisperModel(model_name, device=selected_device, compute_type=compute_type)
    except Exception:
        if device != "auto" or selected_device == "cpu":
            raise
        selected_device = "cpu"
        compute_type = "int8"
        model = WhisperModel(model_name, device=selected_device, compute_type=compute_type)

    language_code = resolve_whisper_language(language)
    raw_segments, info = model.transcribe(
        str(media_path),
        language=language_code,
        vad_filter=True,
        condition_on_previous_text=True,
    )
    segments = [
        Segment(float(segment.start), float(segment.end), normalize_text(segment.text))
        for segment in raw_segments
        if normalize_text(segment.text)
    ]
    details = {
        "source": "whisper",
        "model": model_name,
        "device": selected_device,
        "compute_type": compute_type,
        "source_language": info.language,
        "requested_language": language,
        "is_original": True,
    }
    return merge_segments(segments), details


def write_transcript(
    directory: Path,
    segments: list[Segment],
    *,
    source_url: str,
    details: dict[str, object],
) -> TranscriptArtifacts:
    """Write immutable source transcript artifacts with stable segment identifiers."""
    directory.mkdir(parents=True, exist_ok=True)
    identified = assign_segment_ids(segments)
    segments_path = directory / "segments.source.json"
    write_json(
        segments_path,
        {
            "version": 1,
            "role": "source",
            "language": details.get("source_language", "unknown"),
            "details": details,
            "segments": [segment_record(segment) for segment in identified],
        },
    )
    language = str(details.get("source_language", "unknown"))
    lines = [f"# Source transcript ({language})", ""]
    for segment in identified:
        timestamp = format_timestamp(segment.start)
        link = youtube_timestamp_url(source_url, segment.start)
        lines.extend((f"- [{timestamp}]({link}) `{segment.id}` {segment.text}", ""))
    markdown_path = directory / "transcript.source.md"
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    digest = f"sha256:{sha256(segments_path.read_bytes()).hexdigest()}"
    return TranscriptArtifacts(
        segments_path=segments_path,
        markdown_path=markdown_path,
        source_digest=digest,
        segment_count=len(identified),
    )


def resolve_whisper_language(language: str) -> str | None:
    supported = {"auto": None, "ko": "ko", "en": "en"}
    try:
        return supported[language]
    except KeyError as error:
        raise ValueError("language must be one of: auto, ko, en") from error
