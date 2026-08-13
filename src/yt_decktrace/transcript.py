from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

import pysubs2

from yt_decktrace.runtime import register_nvidia_dll_directories
from yt_decktrace.utils import format_timestamp, normalize_text, write_json, youtube_timestamp_url


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str


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


def transcribe_with_whisper(
    media_path: Path,
    *,
    model_name: str,
    device: str = "auto",
) -> tuple[list[Segment], dict[str, str]]:
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

    raw_segments, info = model.transcribe(
        str(media_path),
        language="ko",
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
        "language": info.language,
    }
    return merge_segments(segments), details


def write_transcript(
    directory: Path,
    segments: list[Segment],
    *,
    source_url: str,
    details: dict[str, str],
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    write_json(
        directory / "segments.json",
        {"details": details, "segments": [asdict(segment) for segment in segments]},
    )
    lines = ["# Korean transcript", ""]
    for segment in segments:
        timestamp = format_timestamp(segment.start)
        link = youtube_timestamp_url(source_url, segment.start)
        lines.extend((f"- [{timestamp}]({link}) {segment.text}", ""))
    (directory / "transcript.md").write_text("\n".join(lines), encoding="utf-8")
