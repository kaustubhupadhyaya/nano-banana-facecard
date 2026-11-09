# nano-banana-facecard

Identity-consistent photo generation through the Gemini web app, followed by optional FaceFusion restoration and ArcFace identity scoring.

This public repository contains the pipeline code, architecture notes and measured benchmark. Personal recipes, review logs, character sheets and reference photos are not included.

## Heads up

The pipeline drives `gemini.google.com` outside Google's official developer API. Google can rate-limit or flag heavy automated use, and the web UI can change without notice.

## What is here

- the staged recipe runner
- Gemini web session handling through the local credential vault
- optional FaceFusion restoration
- ArcFace identity scoring
- core pipeline modules
- architecture and benchmark documentation

## What is not here

- personal photos or face images
- personal recipes or prompt inventories
- personal review logs, feedback ledgers or character sheets
- account cookies or local machine paths

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe facecard.py check
```

The pipeline expects a Gemini web session. Store the session cookies in the local DPAPI vault used by the `secure-vault` skill. Values are read in-process and are never printed, logged or written to the repository.

## Configuration

Every external path resolves from an environment variable, then an optional `facecard.json`, then a portable default under the home folder.

| Location | Environment variable | Portable default |
|---|---|---|
| Reference photos | `FACECARD_REFS_DIR` | `~/Downloads/FaceCard_Originals` |
| Blob store | `FACECARD_BLOBS_DIR` | `~/FacecardData/blobs` |
| Run reports | `FACECARD_REVIEW_DIR` | `~/FacecardReview` |
| Passed pictures | `FACECARD_RESULTS_DIR` | `~/FacecardResults` |
| YOLO interpreter | `FACECARD_YOLO_PYTHON` | `~/VisionModels/yolo/.venv/Scripts/python.exe` |
| FaceFusion clone | `FACEFUSION_DIR` | `../facefusion` |
| secure-vault skill | `SECURE_VAULT_DIR` | `~/.agents/skills/secure-vault` |

## Method

Gemini's image model cannot be seeded, so the same request produces a different image each time. The repository keeps the method stable:

- a recipe records the goal, the reference files, the prompt and the model
- a run goes through method, inputs, request, credits, generation, measurement, review and result
- every run writes its own evidence folder
- a passing result is exported; a failed result stays in the review folder

The architecture and failure paths are in [`docs/architecture.md`](docs/architecture.md).

## Measured benchmark

The public numbers come from one Windows laptop. They describe that machine, not a general performance promise.

| Step | Time | Memory |
|---|---:|---:|
| FaceFusion restore, one image | 168.82 s | 3.05 GB |
| ArcFace, embed five reference photos | 12.88 s | 1.29 GB |
| ArcFace, raw sample | 0.40 s | same process |
| ArcFace, restored sample | 0.58 s | same process |

Sanity values from the same run, not a quality claim: raw ArcFace 0.6523, restored 0.8768, threshold 0.60.

The full run log and reproduction command are in [`docs/benchmark.md`](docs/benchmark.md).

## Limits

- The Gemini web route is not an official API and can break or be rate-limited.
- FaceFusion and ArcFace are local checks. They do not prove likeness quality.
- The benchmark is a single-machine measurement.
- The public repository does not include the private recipes or review corpus used to develop the pipeline.

## License

Licensed under either of [MIT](LICENSE-MIT) or [Apache License, Version 2.0](LICENSE-APACHE) at your option.
