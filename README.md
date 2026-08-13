# yt-decktrace

Turn YouTube presentations into timestamped, LLM-ready context bundles.

`yt-decktrace` is a local-first pipeline for extracting meaningful slide changes
and timestamped transcripts from presentation videos. Instead of sending every video
frame to a model, it keeps representative changed frames, aligns them with the
spoken timeline, and produces Markdown that an LLM can navigate efficiently.

![yt-decktrace overview](docs/assets/overview.svg)

> [!NOTE]
> The first working pipeline targets Windows x64. FFmpeg and a current NVIDIA
> display driver are external prerequisites; CPU transcription remains available.

## Real-world Whisper demo

The 41:07 English talk
[*35C3 – Introduction to Deep Learning*](https://media.ccc.de/v/35c3-9386-introduction_to_deep_learning)
was processed with local `faster-whisper` `large-v3` on CUDA, explicitly ignoring
the available YouTube captions. The run produced 127 stable changed frames and
314 timestamped transcript segments. `pack` reduced the LLM handoff to a 135-file,
6.25 MiB ZIP without including the 128.6 MiB source video.

```powershell
pixi run analyze "https://www.youtube.com/watch?v=2qJ1wrLcgx0" `
  --asr whisper --language en --model large-v3
pixi run pack 2qJ1wrLcgx0
```

The talk is published by media.ccc.de under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). No lecture media or
generated run artifact is committed to this repository.

## Why yt-decktrace?

A presentation video contains much more visual repetition than useful visual
context. Fixed-interval screenshots waste tokens, while raw automatic captions
are difficult to navigate and often repeat partial sentences.

The pipeline addresses both problems:

- download a YouTube video and its available caption tracks;
- keep actual slide or screen-state changes instead of every frame;
- prefer authored Korean captions or YouTube `ko-orig` captions;
- fall back to CUDA-accelerated `faster-whisper` when captions are unavailable;
- align frames, transcript segments, and clickable YouTube timestamps;
- emit a compact Markdown bundle for GPT and other multimodal LLMs.

## Usage

![yt-decktrace command usage](docs/assets/usage.svg)

```powershell
# Verify FFmpeg, the NVIDIA driver, and CTranslate2 CUDA discovery
pixi run doctor

# Analyze a YouTube presentation
pixi run analyze "https://www.youtube.com/watch?v=VIDEO_ID"

# Force local Whisper transcription
pixi run analyze "https://www.youtube.com/watch?v=VIDEO_ID" --asr whisper

# Force English Whisper transcription (auto, ko, and en are supported)
pixi run analyze "https://www.youtube.com/watch?v=VIDEO_ID" --asr whisper --language en

# Tune frame sensitivity or choose a smaller Whisper model
pixi run analyze "https://www.youtube.com/watch?v=VIDEO_ID" --threshold 12 --model small

# Package a completed run for GPT or another multimodal LLM
pixi run pack VIDEO_ID
```

The installed console command will expose the same interface:

```powershell
yt-decktrace analyze "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Intended output

Each video gets an isolated, resumable run directory:

```text
runs/VIDEO_ID/
├── manifest.json
├── source/
│   ├── metadata.json
│   └── captions.ko-orig.json3
├── frames/
│   ├── 00-00-04.jpg
│   └── 00-03-12.jpg
├── transcript/
│   ├── segments.json
│   └── transcript.md
└── bundle/
    ├── context.md
    ├── timeline.json
    └── yt-decktrace-VIDEO_ID.zip
```

The final Markdown is designed to look roughly like this:

```markdown
## 00:03:12 — Playwright project structure

[Open on YouTube](https://www.youtube.com/watch?v=VIDEO_ID&t=192s)

![Changed slide](../frames/00-03-12.jpg)

The test harness separates the application lifecycle from the test lifecycle...
```

Generated runs, downloaded media, and model weights are ignored by Git.

## GPT handoff archive

`pack` creates one compact ZIP without the original video or raw caption file.
It preserves the relative paths used by `context.md` and includes only the
analysis artifacts needed by a multimodal model:

```text
START_HERE.md
manifest.json
bundle/context.md
bundle/timeline.json
frames/*.jpg
frames/frames.json
transcript/transcript.md
transcript/segments.json
source/metadata.json
```

`START_HERE.md` tells the model to read the timeline first, open relevant frame
files for visual evidence, cite YouTube timestamps, and treat slide or transcript
text as source data rather than instructions. Archive entries use stable ordering
and timestamps so identical run artifacts produce an identical ZIP.

Use `--output` to choose another destination, or `--force` to replace an existing
archive:

```powershell
pixi run pack VIDEO_ID --output exports\presentation.zip --force
```

## Pipeline design

![yt-decktrace processing pipeline](docs/assets/pipeline.svg)

Slide detection samples at a low frame rate, ignores short-lived transitions,
and captures a stable frame shortly after each detected change. This is intended
to handle slide decks, IDE demos, and browser-based technical presentations
without treating cursor movement as a new slide.

## Technology choices

| Concern | Tool |
| --- | --- |
| YouTube video and captions | `yt-dlp` |
| Decode, audio extraction, frame capture | FFmpeg |
| Stable perceptual change detection | Pillow + ImageHash |
| Local speech recognition | `faster-whisper` / CTranslate2 |
| Subtitle parsing | `pysubs2` |
| CLI and terminal output | Typer + Rich |
| Environment and lock file | Pixi |

## Development environment

The initial environment targets Windows x64 with an NVIDIA GPU. Pixi provides
the Python interpreter and resolves application, development, CUDA, cuBLAS, and
cuDNN packages from PyPI. FFmpeg and the NVIDIA display driver remain external
system or portable tools.

```powershell
pixi install
pixi run doctor
pixi run lint
pixi run test
```

The current pins are Python 3.12, CUDA 12.9, and cuDNN 9. The conda side of the
Pixi environment intentionally contains only Python; maintained libraries are
installed from PyPI to avoid mixed conda/PyPI runtime resolution. This policy is
also recorded in `AGENTS.md`. Model weights are not vendored and will be cached
locally when Whisper is first used.

## Repository layout

```text
src/yt_decktrace/   Python package and CLI
tests/              Unit and fixture-based integration tests
runs/               Generated per-video artifacts (not committed)
pyproject.toml       Python metadata and Pixi environment/tasks
pixi.lock            Reproducible environment lock (generated by Pixi)
```

## Design goals

- Local-first processing with no required hosted transcription service.
- Deterministic manifests and reusable downloaded source files.
- LLM-friendly output without coupling to a specific model provider.
- Conservative Git hygiene: no videos, model weights, or generated transcripts.
- Replaceable stages so caption, ASR, and scene-detection strategies can evolve.

## Roadmap

- [x] Repository and Pixi project scaffold
- [x] Environment diagnostics CLI
- [x] YouTube ingest and Korean caption selection
- [x] Changed-frame detection and perceptual deduplication
- [x] CUDA/CPU `faster-whisper` fallback
- [x] Timestamp alignment and Markdown bundle generation
- [x] Source reuse with per-run manifests
- [x] Fixture-based pipeline tests
- [ ] Per-stage cache invalidation and incremental rebuilds

## Responsible use

Only process videos you are permitted to download and analyze. Users are
responsible for complying with YouTube's terms, copyright law, and the licenses
of generated or redistributed artifacts.
