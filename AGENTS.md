# Repository instructions

## Dependency policy

- Use Pixi as the environment runner and lock-file manager.
- Keep conda dependencies minimal. The only default conda dependency should be
  the Python interpreter unless a package is demonstrably unavailable on PyPI.
- Add application, development, and GPU runtime packages through
  `[project.dependencies]` or `[project.optional-dependencies]` so Pixi resolves
  them from PyPI.
- Do not add FFmpeg, CUDA, cuBLAS, cuDNN, OpenCV, or other runtime libraries to
  `[tool.pixi.dependencies]` when a maintained PyPI wheel or an explicitly
  external binary is used by the project.
- Keep CUDA dependencies in the `cuda` optional-dependency group. On Windows,
  register DLL directories from the installed NVIDIA wheels before importing
  CTranslate2.
- Run `pixi lock` after dependency changes and commit `pixi.lock`.

## Generated files

- Never commit downloaded videos, audio, model weights, captured frames,
  transcripts, or files below generated `runs/<video-id>/` directories.
- Tests should use small generated fixtures or metadata fixtures instead of
  copyrighted media.

## Transcript and translation policy

- Preserve the original-language transcript as immutable source evidence.
- Never replace source transcript files with translated text.
- Keep source segment IDs and timestamps unchanged during translation.
- Store translations as separate derived artifacts and record their language,
  provider, model, creation time, and source digest in `manifest.json`.
- Bundle the source transcript unconditionally and registered translations only
  when their source digest and segment alignment validate.
- Keep user-facing workflow details in `docs/source-first-translation.md`; this
  file defines contributor invariants rather than replacing user documentation.

## Validation

- Run `pixi run lint` and `pixi run test` for code changes.
- Keep the Windows CPU path usable even when the optional CUDA runtime cannot be
  loaded.
- Add fixture-based tests whenever transcript, translation, manifest, or bundle
  schemas change.
