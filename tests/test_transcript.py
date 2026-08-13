import json

import pytest

from yt_decktrace.transcript import (
    Segment,
    merge_segments,
    parse_json3,
    resolve_whisper_language,
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
