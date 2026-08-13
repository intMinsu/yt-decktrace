from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from yt_decktrace.bundle import build_bundle
from yt_decktrace.frames import extract_changed_frames
from yt_decktrace.ingest import ingest_youtube
from yt_decktrace.transcript import (
    merge_segments,
    parse_subtitle,
    transcribe_with_whisper,
    write_transcript,
)
from yt_decktrace.utils import write_json


def analyze_youtube(
    source_url: str,
    *,
    output_root: Path,
    asr: str = "auto",
    whisper_model: str = "large-v3",
    whisper_language: str = "auto",
    sample_fps: float = 1.0,
    change_threshold: int = 10,
    min_gap: float = 2.0,
    force: bool = False,
) -> Path:
    if asr not in {"auto", "youtube", "whisper"}:
        raise ValueError("asr must be one of: auto, youtube, whisper")

    ingest = ingest_youtube(
        source_url,
        output_root,
        caption_policy=asr,
        force=force,
    )

    if ingest.caption_path is not None and asr != "whisper":
        segments = merge_segments(parse_subtitle(ingest.caption_path))
        choice = ingest.caption_choice
        details = {
            "source": f"youtube-{choice.source}" if choice else "youtube",
            "language": choice.language if choice else "ko",
            "format": ingest.caption_path.suffix.removeprefix("."),
        }
    elif asr == "youtube":
        raise RuntimeError("The selected YouTube caption track was not downloaded")
    else:
        segments, details = transcribe_with_whisper(
            ingest.video_path,
            model_name=whisper_model,
            language=whisper_language,
        )

    transcript_dir = ingest.run_dir / "transcript"
    write_transcript(
        transcript_dir,
        segments,
        source_url=ingest.source_url,
        details=details,
    )
    frames = extract_changed_frames(
        ingest.video_path,
        ingest.run_dir / "frames",
        sample_fps=sample_fps,
        change_threshold=change_threshold,
        min_gap=min_gap,
    )
    context_path = build_bundle(
        ingest.run_dir / "bundle",
        title=ingest.title,
        source_url=ingest.source_url,
        frames=frames,
        segments=segments,
    )
    write_json(
        ingest.run_dir / "manifest.json",
        {
            "version": 1,
            "created_at": datetime.now(UTC).isoformat(),
            "video_id": ingest.video_id,
            "source_url": ingest.source_url,
            "video": str(ingest.video_path.relative_to(ingest.run_dir)),
            "caption": (
                str(ingest.caption_path.relative_to(ingest.run_dir))
                if ingest.caption_path
                else None
            ),
            "transcript": details,
            "frame_count": len(frames),
            "settings": {
                "asr": asr,
                "whisper_model": whisper_model,
                "whisper_language": whisper_language,
                "sample_fps": sample_fps,
                "change_threshold": change_threshold,
                "min_gap": min_gap,
            },
            "frames": [asdict(frame) for frame in frames],
            "context": str(context_path.relative_to(ingest.run_dir)),
        },
    )
    return context_path
