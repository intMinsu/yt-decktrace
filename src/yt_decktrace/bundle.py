from __future__ import annotations

from pathlib import Path

from yt_decktrace.frames import ChangedFrame
from yt_decktrace.transcript import Segment, assign_segment_ids
from yt_decktrace.utils import format_timestamp, write_json, youtube_timestamp_url


def build_bundle(
    directory: Path,
    *,
    title: str,
    source_url: str,
    frames: list[ChangedFrame],
    segments: list[Segment],
    transcript_language: str = "unknown",
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    identified_segments = assign_segment_ids(segments)
    timeline: list[dict[str, object]] = []
    lines = [
        f"# {title}",
        "",
        f"Source: [{source_url}]({source_url})",
        "",
        f"Transcript evidence: source ({transcript_language})",
        "",
    ]

    for index, frame in enumerate(frames):
        next_timestamp = frames[index + 1].timestamp if index + 1 < len(frames) else float("inf")
        active = [
            segment
            for segment in identified_segments
            if frame.timestamp <= (segment.start + segment.end) / 2 < next_timestamp
        ]
        timestamp = format_timestamp(frame.timestamp)
        link = youtube_timestamp_url(source_url, frame.timestamp)
        image_path = f"../frames/{frame.file}"
        lines.extend(
            [
                f"## {timestamp}",
                "",
                f"[Open on YouTube]({link})",
                "",
                f"![Changed frame at {timestamp}]({image_path})",
                "",
            ]
        )
        if active:
            lines.extend(segment.text for segment in active)
        else:
            lines.append("_No transcript segment was aligned to this interval._")
        lines.append("")
        timeline.append(
            {
                "timestamp": frame.timestamp,
                "youtube_url": link,
                "frame": image_path,
                "transcript": [
                    {
                        "id": segment.id,
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text,
                    }
                    for segment in active
                ],
            }
        )

    context_path = directory / "context.md"
    context_path.write_text("\n".join(lines), encoding="utf-8")
    write_json(directory / "timeline.json", timeline)
    return context_path
