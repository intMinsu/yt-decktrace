from PIL import Image, ImageDraw

from yt_decktrace.frames import select_changed_frames


def _pattern(path, orientation: str) -> None:
    image = Image.new("RGB", (160, 90), "white")
    draw = ImageDraw.Draw(image)
    if orientation == "vertical":
        draw.rectangle((10, 5, 60, 85), fill="black")
    else:
        draw.rectangle((5, 10, 155, 40), fill="black")
    image.save(path)


def test_selects_only_stable_changed_frames(tmp_path) -> None:
    candidates = [tmp_path / f"candidate-{index:08d}.jpg" for index in range(4)]
    _pattern(candidates[0], "vertical")
    _pattern(candidates[1], "vertical")
    _pattern(candidates[2], "horizontal")
    _pattern(candidates[3], "horizontal")

    selected = select_changed_frames(
        candidates,
        sample_fps=1.0,
        change_threshold=10,
        min_gap=0,
    )

    assert [path for path, _, _ in selected] == [candidates[0], candidates[3]]
    assert selected[1][1] == 3.0
    assert int(selected[1][2]) == selected[1][2]
