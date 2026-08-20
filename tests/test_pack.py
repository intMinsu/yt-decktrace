import hashlib
import json
import zipfile

import pytest

from yt_decktrace.pack import pack_run
from yt_decktrace.transcript import Segment, write_transcript
from yt_decktrace.translation import add_translation


def _write_json(path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _make_run(tmp_path):
    run = tmp_path / "runs" / "video_123"
    _write_json(
        run / "manifest.json",
        {
            "video_id": "video_123",
            "source_url": "https://youtu.be/video_123",
            "transcript": {"source": "youtube-automatic"},
        },
    )
    _write_json(
        run / "source" / "metadata.json",
        {"title": "테스트 발표", "source_url": "https://youtu.be/video_123"},
    )
    _write_json(run / "bundle" / "timeline.json", [])
    (run / "bundle" / "context.md").write_text(
        "![frame](../frames/00-00-00.jpg)", encoding="utf-8"
    )
    _write_json(run / "transcript" / "segments.json", {"segments": []})
    (run / "transcript" / "transcript.md").write_text("# Transcript", encoding="utf-8")
    _write_json(run / "frames" / "frames.json", {"frames": []})
    (run / "frames" / "00-00-00.jpg").write_bytes(b"first-frame")
    (run / "frames" / "00-00-10.jpg").write_bytes(b"second-frame")
    (run / "source" / "video.mkv").write_bytes(b"never include video")
    (run / "source" / "captions.ko.json3").write_bytes(b"never include captions")
    return run


def test_pack_run_creates_compact_gpt_archive(tmp_path) -> None:
    run = _make_run(tmp_path)

    result = pack_run("video_123", runs_root=tmp_path / "runs")

    assert result.archive_path == run / "bundle" / "yt-decktrace-video_123.zip"
    assert result.frame_count == 2
    with zipfile.ZipFile(result.archive_path) as archive:
        names = archive.namelist()
        assert names[0] == "START_HERE.md"
        assert "bundle/context.md" in names
        assert "frames/00-00-10.jpg" in names
        assert "source/video.mkv" not in names
        assert "source/captions.ko.json3" not in names
        assert all(item.date_time == (1980, 1, 1, 0, 0, 0) for item in archive.infolist())
        start_here = archive.read("START_HERE.md").decode("utf-8")
        assert "테스트 발표" in start_here
        assert "파일을 실제로 열어" in start_here


def test_pack_run_includes_source_and_registered_translation(tmp_path) -> None:
    run = _make_run(tmp_path)
    (run / "transcript" / "segments.json").unlink()
    (run / "transcript" / "transcript.md").unlink()
    details = {"source": "youtube-automatic", "source_language": "en"}
    artifacts = write_transcript(
        run / "transcript",
        [Segment(1, 2, "Hello")],
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
    translation_input = tmp_path / "translation.ko.json"
    _write_json(
        translation_input,
        {"segments": [{"id": "segment-000001", "text": "안녕하세요"}]},
    )
    add_translation(
        "video_123",
        translation_input,
        language="ko",
        provider="codex",
        model="gpt-test",
        runs_root=tmp_path / "runs",
    )

    result = pack_run("video_123", runs_root=tmp_path / "runs")

    with zipfile.ZipFile(result.archive_path) as archive:
        names = archive.namelist()
        assert "transcript/segments.source.json" in names
        assert "transcript/transcript.source.md" in names
        assert "transcript/segments.ko.json" in names
        assert "transcript/transcript.ko.md" in names
        start_here = archive.read("START_HERE.md").decode("utf-8")
        assert '"source_language": "en"' in start_here
        assert '"translation_languages": [' in start_here
        assert '"ko"' in start_here

    artifacts.segments_path.write_text(
        artifacts.segments_path.read_text(encoding="utf-8").replace("Hello", "Tampered"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="digest"):
        pack_run("video_123", runs_root=tmp_path / "runs", force=True)


def test_pack_run_is_deterministic_and_requires_force(tmp_path) -> None:
    _make_run(tmp_path)
    first = pack_run("video_123", runs_root=tmp_path / "runs")
    first_digest = hashlib.sha256(first.archive_path.read_bytes()).hexdigest()

    with pytest.raises(FileExistsError, match="--force"):
        pack_run("video_123", runs_root=tmp_path / "runs")

    second = pack_run("video_123", runs_root=tmp_path / "runs", force=True)
    second_digest = hashlib.sha256(second.archive_path.read_bytes()).hexdigest()
    assert second_digest == first_digest


def test_pack_run_rejects_unsafe_or_incomplete_runs(tmp_path) -> None:
    with pytest.raises(ValueError, match="video_id"):
        pack_run("../escape", runs_root=tmp_path / "runs")

    (tmp_path / "runs" / "empty").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="missing"):
        pack_run("empty", runs_root=tmp_path / "runs")

    _make_run(tmp_path)
    with pytest.raises(ValueError, match=".zip"):
        pack_run(
            "video_123",
            runs_root=tmp_path / "runs",
            output_path=tmp_path / "not-an-archive.txt",
        )
