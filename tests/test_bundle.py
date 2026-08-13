import json

from yt_decktrace.bundle import build_bundle
from yt_decktrace.frames import ChangedFrame
from yt_decktrace.transcript import Segment


def test_bundle_aligns_transcript_with_frame_intervals(tmp_path) -> None:
    path = build_bundle(
        tmp_path,
        title="Demo",
        source_url="https://youtu.be/video",
        frames=[ChangedFrame(0, "00-00-00.jpg", 0), ChangedFrame(10, "00-00-10.jpg", 20)],
        segments=[Segment(1, 3, "첫 번째"), Segment(11, 13, "두 번째")],
    )

    markdown = path.read_text(encoding="utf-8")
    timeline = json.loads((tmp_path / "timeline.json").read_text(encoding="utf-8"))
    assert "https://youtu.be/video?t=10s" in markdown
    assert "../frames/00-00-10.jpg" in markdown
    assert [item["transcript"][0]["text"] for item in timeline] == ["첫 번째", "두 번째"]


def test_segment_spanning_a_change_is_not_duplicated(tmp_path) -> None:
    build_bundle(
        tmp_path,
        title="Demo",
        source_url="https://youtu.be/video",
        frames=[ChangedFrame(0, "first.jpg", 0), ChangedFrame(10, "second.jpg", 20)],
        segments=[Segment(7, 13, "한 번만")],
    )

    timeline = json.loads((tmp_path / "timeline.json").read_text(encoding="utf-8"))
    assert sum(item["transcript"] != [] for item in timeline) == 1
