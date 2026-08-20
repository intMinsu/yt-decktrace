import json
from hashlib import sha256

import pytest

from yt_decktrace.transcript import (
    Segment,
    assign_segment_ids,
    merge_segments,
    parse_json3,
    resolve_whisper_language,
    write_transcript,
)


def test_parse_and_merge_json3(tmp_path) -> None:
    caption = tmp_path / "captions.json3"
    caption.write_text(
        json.dumps(
            {
                "events": [
                    {"tStartMs": 1000, "dDurationMs": 1000, "segs": [{"utf8": "안녕"}]},
                    {"tStartMs": 2100, "dDurationMs": 1000, "segs": [{"utf8": "하세요"}]},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    parsed = parse_json3(caption)

    assert parsed == [Segment(1.0, 2.0, "안녕"), Segment(2.1, 3.1, "하세요")]
    assert merge_segments(parsed) == [Segment(1.0, 3.1, "안녕 하세요")]


def test_resolve_whisper_language() -> None:
    assert resolve_whisper_language("auto") is None
    assert resolve_whisper_language("ko") == "ko"
    assert resolve_whisper_language("en") == "en"
    with pytest.raises(ValueError, match="auto, ko, en"):
        resolve_whisper_language("fr")


def test_source_transcript_has_stable_ids_and_digest(tmp_path) -> None:
    artifacts = write_transcript(
        tmp_path,
        [Segment(1, 2, "Hello"), Segment(3, 4, "world")],
        source_url="https://youtu.be/video",
        details={"source": "youtube-automatic", "source_language": "en"},
    )

    payload = json.loads(artifacts.segments_path.read_text(encoding="utf-8"))
    assert artifacts.segments_path.name == "segments.source.json"
    assert artifacts.markdown_path.name == "transcript.source.md"
    assert [item["id"] for item in payload["segments"]] == [
        "segment-000001",
        "segment-000002",
    ]
    assert artifacts.source_digest == (
        f"sha256:{sha256(artifacts.segments_path.read_bytes()).hexdigest()}"
    )
    assert "`segment-000001` Hello" in artifacts.markdown_path.read_text(encoding="utf-8")


def test_assign_segment_ids_preserves_existing_ids_and_rejects_duplicates() -> None:
    assigned = assign_segment_ids([Segment(1, 2, "Hello", "custom")])
    assert assigned == [Segment(1, 2, "Hello", "custom")]

    with pytest.raises(ValueError, match="Duplicate"):
        assign_segment_ids(
            [Segment(1, 2, "one", "duplicate"), Segment(3, 4, "two", "duplicate")]
        )
