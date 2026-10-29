# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). No release has been tagged yet.

## [Unreleased]

### Fixed
- Tests import app modules the way the app does (#1).
- `src/datasets` renamed to `src/dataset_versioning` so it no longer shadows Hugging Face `datasets` (#2).
- `fine_tuning.jobs.create` called with the Mistral SDK 1.x schema (#3).
- Dataset upload: uuid file names, 100 MB cap, `.jsonl` only (#4).
- Frontend `lib/` committed so the frontend builds (#6).
- One job status enum shared by API, poller, worker, CLI and frontend; cancel also cancels the job on Mistral (#7).

### Changed
- README, model card and license aligned with the actual state (#5).
- Requirements split into `requirements-api.txt` and `requirements-train.txt`; `requirements.txt` installs both.
- CI: Python 3.10-3.12 matrix, coverage report, actions pinned by SHA, read-only token; Black removed (Ruff only); lint gates on runtime errors only for now.

### Added
- `SECURITY.md`, `CHANGELOG.md`, Dependabot, pre-commit (Ruff).
- Slow CPU test: LoRA train, save/load and merge on a tiny Mistral (#8).
- `docs/THEORY.md`: LoRA, QLoRA and VRAM estimate (#9).

## 2025-12-19 (untagged)
- `9e21c37` PostgreSQL, Celery, S3, auth, Docker and test suite.
- `e4bff02` Frontend redesign.
- `7053d85` Initial commit.
