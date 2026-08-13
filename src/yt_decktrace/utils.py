from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS, rounding down to the active second."""
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def timestamp_slug(seconds: float) -> str:
    return format_timestamp(seconds).replace(":", "-")


def youtube_timestamp_url(url: str, seconds: float) -> str:
    """Return a URL with a canonical whole-second YouTube time parameter."""
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query) if key not in {"t", "start"}]
    query.append(("t", f"{max(0, int(seconds))}s"))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
