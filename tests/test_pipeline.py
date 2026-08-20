import json

from yt_decktrace.frames import ChangedFrame
from yt_decktrace.ingest import CaptionChoice, IngestResult
from yt_decktrace.pipeline import analyze_youtube


def test_pipeline_writes_versioned_source_transcript_manifest(tmp_path, monkeypatch) -> None:
    run = tmp_path / "runs" / "video_123"
    source = run / "source"
    source.mkdir(parents=True)
    video = source / "video.mkv"
    video.write_bytes(b"fixture")
    caption = source / "captions.en-orig.json3"
    caption.write_text(
        json.dumps(
            {
                "events": [
                    {
                        "tStartMs": 1000,
                        "dDurationMs": 1000,
                        "segs": [{"utf8": "Hello"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    ingest = IngestResult(
        video_id="video_123",
        source_url="https://youtu.be/video_123",
        title="Demo",
        duration=10,
        run_dir=run,
        video_path=video,
        metadata_path=source / "metadata.json",
        caption_path=caption,
        caption_choice=CaptionChoice("en-orig", "json3", "automatic", True),
    )
    monkeypatch.setattr("yt_decktrace.pipeline.ingest_youtube", lambda *args, **kwargs: ingest)
    monkeypatch.setattr(
        "yt_decktrace.pipeline.extract_changed_frames",
        lambda *args, **kwargs: [ChangedFrame(0, "00-00-00.jpg", 0)],
    )

    context = analyze_youtube(
        "https://youtu.be/video_123",
        output_root=tmp_path / "runs",
        asr="youtube",
        caption_language="original",
    )

    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    source_segments = json.loads(
        (run / "transcript" / "segments.source.json").read_text(encoding="utf-8")
    )
    assert context == run / "bundle" / "context.md"
    assert manifest["version"] == 2
    assert manifest["transcript"]["source_language"] == "en"
    assert manifest["transcript"]["is_original"] is True
    assert manifest["transcript"]["artifacts"] == {
        "segments": "transcript/segments.source.json",
        "markdown": "transcript/transcript.source.md",
    }
    assert manifest["translations"] == []
    assert source_segments["segments"][0]["id"] == "segment-000001"
    assert not (run / "transcript" / "segments.json").exists()
