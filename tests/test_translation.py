import json

import pytest

from yt_decktrace.transcript import Segment, write_transcript
from yt_decktrace.translation import add_translation


def _write_json(path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _make_source_run(tmp_path):
    run = tmp_path / "runs" / "video_123"
    details = {"source": "youtube-automatic", "source_language": "en"}
    artifacts = write_transcript(
        run / "transcript",
        [Segment(1, 2, "Hello"), Segment(3, 4, "world")],
        source_url="https://youtu.be/video_123",
        details=details,
    )
    _write_json(
        run / "manifest.json",
        {
            "version": 2,
            "video_id": "video_123",
            "source_url": "https://youtu.be/video_123",
            "transcript": {
                **details,
                "source_digest": artifacts.source_digest,
                "artifacts": {
                    "segments": "transcript/segments.source.json",
                    "markdown": "transcript/transcript.source.md",
                },
            },
            "translations": [],
        },
    )
    return run, artifacts


def test_add_translation_preserves_source_timing_and_records_provenance(tmp_path) -> None:
    run, artifacts = _make_source_run(tmp_path)
    translation_input = tmp_path / "translation.ko.json"
    _write_json(
        translation_input,
        {
            "segments": [
                {"id": "segment-000001", "text": "안녕하세요"},
                {"id": "segment-000002", "text": "세계"},
            ]
        },
    )

    result = add_translation(
        "video_123",
        translation_input,
        language="ko",
        provider="codex",
        model="gpt-test",
        runs_root=tmp_path / "runs",
    )

    payload = json.loads(result.segments_path.read_text(encoding="utf-8"))
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    assert result.source_digest == artifacts.source_digest
    assert [(item["start"], item["end"]) for item in payload["segments"]] == [
        (1.0, 2.0),
        (3.0, 4.0),
    ]
    assert payload["translation"]["provider"] == "codex"
    assert payload["translation"]["model"] == "gpt-test"
    assert manifest["translations"][0]["source_digest"] == artifacts.source_digest
    assert "`segment-000001` 안녕하세요" in result.markdown_path.read_text(encoding="utf-8")


def test_add_translation_rejects_changed_timing_or_missing_segments(tmp_path) -> None:
    _make_source_run(tmp_path)
    changed_timing = tmp_path / "changed.json"
    _write_json(
        changed_timing,
        {
            "segments": [
                {"id": "segment-000001", "start": 99, "text": "안녕하세요"},
                {"id": "segment-000002", "text": "세계"},
            ]
        },
    )
    with pytest.raises(ValueError, match="must not change start"):
        add_translation(
            "video_123",
            changed_timing,
            language="ko",
            provider="codex",
            model="gpt-test",
            runs_root=tmp_path / "runs",
        )

    missing_segment = tmp_path / "missing.json"
    _write_json(
        missing_segment,
        {"segments": [{"id": "segment-000001", "text": "안녕하세요"}]},
    )
    with pytest.raises(ValueError, match="exactly one entry"):
        add_translation(
            "video_123",
            missing_segment,
            language="ko",
            provider="codex",
            model="gpt-test",
            runs_root=tmp_path / "runs",
        )
