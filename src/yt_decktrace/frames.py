from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

import imagehash
from PIL import Image

from yt_decktrace.runtime import find_ffmpeg
from yt_decktrace.utils import timestamp_slug, write_json


@dataclass(frozen=True)
class ChangedFrame:
    timestamp: float
    file: str
    distance: int


def select_changed_frames(
    candidates: list[Path],
    *,
    sample_fps: float,
    change_threshold: int,
    stable_threshold: int = 4,
    stable_samples: int = 2,
    min_gap: float = 2.0,
) -> list[tuple[Path, float, int]]:
    if not candidates:
        return []

    hashes = []
    for path in candidates:
        with Image.open(path) as image:
            hashes.append(imagehash.phash(image.convert("RGB")))

    selected: list[tuple[Path, float, int]] = [(candidates[0], 0.0, 0)]
    baseline = hashes[0]
    pending_hash = None
    pending_count = 0

    for index in range(1, len(candidates)):
        current_hash = hashes[index]
        timestamp = index / sample_fps
        distance = current_hash - baseline
        if distance < change_threshold:
            pending_hash = None
            pending_count = 0
            continue

        if pending_hash is not None and current_hash - pending_hash <= stable_threshold:
            pending_count += 1
        else:
            pending_hash = current_hash
            pending_count = 1

        if pending_count < stable_samples or timestamp - selected[-1][1] < min_gap:
            continue

        selected.append((candidates[index], timestamp, distance))
        baseline = current_hash
        pending_hash = None
        pending_count = 0
    return selected


def extract_changed_frames(
    video_path: Path,
    output_dir: Path,
    *,
    sample_fps: float = 1.0,
    change_threshold: int = 10,
    min_gap: float = 2.0,
) -> list[ChangedFrame]:
    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        raise RuntimeError(
            "FFmpeg was not found. Add it to PATH or set YT_DECKTRACE_FFMPEG_DIR."
        )
    if sample_fps <= 0:
        raise ValueError("sample_fps must be greater than zero")

    output_dir.mkdir(parents=True, exist_ok=True)
    for old_frame in output_dir.glob("*.jpg"):
        old_frame.unlink()

    with tempfile.TemporaryDirectory(prefix="yt-decktrace-frames-") as temporary:
        candidate_dir = Path(temporary)
        pattern = candidate_dir / "candidate-%08d.jpg"
        subprocess.run(
            [
                str(ffmpeg),
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(video_path),
                "-vf",
                f"fps={sample_fps},scale=1280:-2:force_original_aspect_ratio=decrease",
                "-q:v",
                "3",
                "-start_number",
                "0",
                str(pattern),
            ],
            check=True,
        )
        candidates = sorted(candidate_dir.glob("candidate-*.jpg"))
        selected = select_changed_frames(
            candidates,
            sample_fps=sample_fps,
            change_threshold=change_threshold,
            min_gap=min_gap,
        )

        frames: list[ChangedFrame] = []
        used_names: set[str] = set()
        for source, timestamp, distance in selected:
            base = timestamp_slug(timestamp)
            filename = f"{base}.jpg"
            suffix = 2
            while filename in used_names:
                filename = f"{base}-{suffix}.jpg"
                suffix += 1
            used_names.add(filename)
            shutil.copy2(source, output_dir / filename)
            frames.append(ChangedFrame(timestamp, filename, int(distance)))

    write_json(
        output_dir / "frames.json",
        {
            "settings": {
                "sample_fps": sample_fps,
                "change_threshold": change_threshold,
                "min_gap": min_gap,
            },
            "frames": [asdict(frame) for frame in frames],
        },
    )
    return frames
