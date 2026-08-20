from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from yt_decktrace.utils import (
    format_timestamp,
    normalize_text,
    write_json,
    youtube_timestamp_url,
)


@dataclass(frozen=True)
class TranslationResult:
    language: str
    segments_path: Path
    markdown_path: Path
    segment_count: int
    source_digest: str


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"Expected a JSON object in {path}")
    return value


def source_transcript_artifacts(manifest: dict[str, Any]) -> tuple[str, str]:
    """Return source transcript artifact paths, including legacy manifest support."""
    transcript = manifest.get("transcript")
    if isinstance(transcript, dict):
        artifacts = transcript.get("artifacts")
        if isinstance(artifacts, dict):
            segments = artifacts.get("segments")
            markdown = artifacts.get("markdown")
            if isinstance(segments, str) and isinstance(markdown, str):
                return segments, markdown
    return "transcript/segments.json", "transcript/transcript.md"


def resolve_run_artifact(
    run_dir: Path,
    relative: str,
    *,
    directory: str | None = None,
) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Artifact path must stay inside the run directory: {relative}")
    if directory is not None and (not path.parts or path.parts[0] != directory):
        raise ValueError(f"Artifact path must stay inside {directory}/: {relative}")
    resolved_run = run_dir.resolve()
    resolved = (resolved_run / path).resolve()
    if not resolved.is_relative_to(resolved_run):
        raise ValueError(f"Artifact path resolves outside the run directory: {relative}")
    return resolved


def source_digest(path: Path) -> str:
    return f"sha256:{sha256(path.read_bytes()).hexdigest()}"


def _source_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = payload.get("segments")
    if not isinstance(records, list):
        raise TypeError("Source transcript must contain a segments list")
    for record in records:
        if not isinstance(record, dict):
            raise TypeError("Every source transcript segment must be a JSON object")
        if not isinstance(record.get("id"), str):
            raise TypeError(
                "Source transcript segments do not have stable ids; rerun analyze before translation"
            )
    return records


def validate_translation_segments(
    source_payload: dict[str, Any],
    translation_payload: dict[str, Any],
) -> list[dict[str, object]]:
    """Validate translated text and copy timing exclusively from the source transcript."""
    source_records = _source_records(source_payload)
    translated = translation_payload.get("segments")
    if not isinstance(translated, list):
        raise TypeError("Translation input must contain a segments list")
    if len(translated) != len(source_records):
        raise ValueError(
            "Translation must contain exactly one entry for every source transcript segment"
        )

    canonical: list[dict[str, object]] = []
    seen: set[str] = set()
    for source, candidate in zip(source_records, translated, strict=True):
        if not isinstance(candidate, dict):
            raise TypeError("Every translated segment must be a JSON object")
        identifier = candidate.get("id")
        if not isinstance(identifier, str) or identifier != source["id"]:
            raise ValueError(
                "Translation segment ids and ordering must exactly match the source transcript"
            )
        if identifier in seen:
            raise ValueError(f"Duplicate translation segment id: {identifier}")
        seen.add(identifier)

        for field in ("start", "end"):
            if field in candidate and float(candidate[field]) != float(source[field]):
                raise ValueError(f"Translation must not change {field} for {identifier}")
        text = candidate.get("text")
        if not isinstance(text, str) or not normalize_text(text):
            raise ValueError(f"Translation text is empty for {identifier}")
        canonical.append(
            {
                "id": identifier,
                "start": float(source["start"]),
                "end": float(source["end"]),
                "text": normalize_text(text),
            }
        )
    return canonical


def add_translation(
    video_id: str,
    input_path: Path,
    *,
    language: str,
    provider: str,
    model: str,
    runs_root: Path = Path("runs"),
    force: bool = False,
) -> TranslationResult:
    """Register a translated segment list without allowing source timing to change."""
    if re.fullmatch(r"[A-Za-z0-9_-]+", video_id) is None:
        raise ValueError("video_id may contain only letters, numbers, underscores, and hyphens")
    normalized_language = language.lower().replace("_", "-")
    if re.fullmatch(r"[a-z]{2,3}(?:-[a-z0-9]+)*", normalized_language) is None:
        raise ValueError("language must be a BCP-47-like code such as ko or pt-br")
    if not provider.strip() or not model.strip():
        raise ValueError("provider and model must not be empty")

    run_dir = (runs_root.resolve() / video_id).resolve()
    if run_dir.parent != runs_root.resolve() or not run_dir.is_dir():
        raise FileNotFoundError(f"Run directory does not exist: {run_dir}")
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Run manifest does not exist: {manifest_path}")
    manifest = _load_object(manifest_path)

    source_relative, _ = source_transcript_artifacts(manifest)
    source_path = resolve_run_artifact(run_dir, source_relative, directory="transcript")
    if not source_path.is_file():
        raise FileNotFoundError(f"Source transcript does not exist: {source_path}")
    source_payload = _load_object(source_path)
    digest = source_digest(source_path)
    transcript_details = manifest.get("transcript")
    expected_digest = (
        transcript_details.get("source_digest")
        if isinstance(transcript_details, dict)
        else None
    )
    if isinstance(expected_digest, str) and expected_digest != digest:
        raise ValueError("Source transcript digest no longer matches manifest.json")

    input_payload = _load_object(input_path.resolve())
    translated = validate_translation_segments(source_payload, input_payload)
    created_at = datetime.now(UTC).isoformat()
    source_language = str(
        transcript_details.get("source_language", source_payload.get("language", "unknown"))
        if isinstance(transcript_details, dict)
        else source_payload.get("language", "unknown")
    )

    segments_relative = f"transcript/segments.{normalized_language}.json"
    markdown_relative = f"transcript/transcript.{normalized_language}.md"
    segments_path = resolve_run_artifact(run_dir, segments_relative, directory="transcript")
    markdown_path = resolve_run_artifact(run_dir, markdown_relative, directory="transcript")
    if (segments_path.exists() or markdown_path.exists()) and not force:
        raise FileExistsError(
            f"Translation for {normalized_language} already exists. Use --force to replace it."
        )

    translation_details = {
        "provider": provider.strip(),
        "model": model.strip(),
        "created_at": created_at,
    }
    write_json(
        segments_path,
        {
            "version": 1,
            "role": "translation",
            "language": normalized_language,
            "source_language": source_language,
            "source_digest": digest,
            "translation": translation_details,
            "segments": translated,
        },
    )

    source_url = str(manifest.get("source_url") or "")
    lines = [
        f"# Translation ({normalized_language})",
        "",
        f"Source language: {source_language}",
        "",
        f"Source digest: `{digest}`",
        "",
    ]
    for segment in translated:
        timestamp = format_timestamp(float(segment["start"]))
        link = youtube_timestamp_url(source_url, float(segment["start"]))
        lines.extend((f"- [{timestamp}]({link}) `{segment['id']}` {segment['text']}", ""))
    markdown_path.write_text("\n".join(lines), encoding="utf-8")

    entry = {
        "language": normalized_language,
        "provider": provider.strip(),
        "model": model.strip(),
        "created_at": created_at,
        "source_digest": digest,
        "artifacts": {
            "segments": segments_relative,
            "markdown": markdown_relative,
        },
    }
    translations = manifest.get("translations")
    registered = [item for item in translations if isinstance(item, dict)] if isinstance(
        translations, list
    ) else []
    registered = [item for item in registered if item.get("language") != normalized_language]
    registered.append(entry)
    registered.sort(key=lambda item: str(item.get("language", "")))
    manifest["translations"] = registered
    write_json(manifest_path, manifest)

    return TranslationResult(
        language=normalized_language,
        segments_path=segments_path,
        markdown_path=markdown_path,
        segment_count=len(translated),
        source_digest=digest,
    )
