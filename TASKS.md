# TASKS.md — Granular Implementation Task Breakdown

Role: Technical Project Manager. Source documents: `AGENTS.md`, `PROJECT_SPEC.md`, `ARCHITECTURE.md`. `BACKEND_ARCHITECTURE.md`, `MILESTONE.md`, `ROADMAP_MVP.md`,  

Rules applied:
- Every task is sized to **< 2 hours** for one engineer.
- Every task lists explicit **Depends On** (task IDs).
- Every task has binary, checkable **Acceptance Criteria**.
- Every task lists its **Testing Requirement** (per AGENTS.md: unit test + error handling + sample file, where applicable).

Task ID format: `[Area]-[Number]`. Areas: `SET` (setup), `DB`, `INF` (infra), `IMG`, `AUD`, `VID`, `SEC`, `API` (cross-cutting routing/schemas), `FE` (frontend), `TEST`, `DOC`.

Note: this file supersedes the earlier high-level milestone version of TASKS.md, which is preserved as `TASKS_v1_roadmap.md` for reference.

---

## SET — Project Setup

| ID | Task | Depends On | Acceptance Criteria | Testing Requirement |
|---|---|---|---|---|
| SET-01 | Create monorepo skeleton (`backend/`, `frontend/`, `docs/`) with empty `README.md` in each | — | Folders exist and are committed | None (structural) |
| SET-02 | Init backend Python project: `requirements.txt`, virtualenv instructions, `app/main.py` returning `{"status":"ok"}` on `/` | SET-01 | `uvicorn app.main:app` runs and `/` returns 200 | Manual curl check documented in README |
| SET-03 | Init frontend Vite+React+TS project, default page renders "mycompress" | SET-01 | `npm run dev` serves a page showing project name | Manual browser check |
| SET-04 | Configure TailwindCSS in frontend | SET-03 | A Tailwind utility class visibly styles an element | Manual visual check |
| SET-05 | Add backend linting (ruff) + formatting (black) configs | SET-02 | `ruff check .` and `black --check .` run clean on skeleton | CI step added (SET-08) |
| SET-06 | Add frontend linting (eslint) + formatting (prettier) configs | SET-03 | `npm run lint` runs clean on skeleton | CI step added (SET-08) |
| SET-07 | Add `pytest` config (`pytest.ini`) + `tests/` folder with one trivial passing test | SET-02 | `pytest` exits 0 | Trivial `test_health.py` asserting `True` |
| SET-08 | Set up CI workflow (GitHub Actions): lint + test for both backend and frontend on push | SET-05, SET-06, SET-07 | CI run is green on a clean push | CI itself is the test |
| SET-09 | Write Dockerfile for backend installing FFmpeg system package + Python deps | SET-02 | `docker build` succeeds; `ffmpeg -version` runs inside container | Manual build + exec check |
| SET-10 | Write `docker-compose.yml` wiring backend + frontend dev servers | SET-04, SET-09 | `docker compose up` serves both apps on expected ports | Manual smoke check |

---

## DB — Persistence Layer

| ID | Task | Depends On | Acceptance Criteria | Testing Requirement |
|---|---|---|---|---|
| DB-01 | Add SQLAlchemy + create `db/database.py` (engine, session factory, SQLite file path from config) | SET-02 | Importing module creates `mycompress.db` file on disk | Unit test: session can be opened/closed without error |
| DB-02 | Define `Job` ORM model per schema in FINAL_ARCHITECTURE §8 | DB-01 | Model class matches all listed columns/types | Unit test: instantiate `Job()`, assert fields settable |
| DB-03 | Define `Metric` ORM model (EAV-style: job_id, metric_name, metric_value) | DB-01 | Model matches schema | Unit test: instantiate, assert FK field present |
| DB-04 | Set up Alembic migrations, generate initial migration for `jobs` + `metrics` tables | DB-02, DB-03 | `alembic upgrade head` creates both tables with correct columns | Manual: inspect SQLite schema via `sqlite3 .schema` |
| DB-05 | Add indices: `jobs(status, expires_at)`, `metrics(job_id)` | DB-04 | Migration includes both indices | Manual: `EXPLAIN QUERY PLAN` shows index usage on a sample query |
| DB-06 | Write `job_repository.py`: `create_job()`, `get_job()`, `update_job_status()` | DB-04 | Each function has type hints + docstring | Unit tests: create→get round-trip; update changes status field |
| DB-07 | Write `metric_repository.py`: `add_metric()`, `get_metrics_for_job()` | DB-04 | Functions work against real SQLite test DB | Unit tests: add 2 metrics, retrieve both, values match |

---

## INF — Infrastructure

| ID | Task | Depends On | Acceptance Criteria | Testing Requirement |
|---|---|---|---|---|
| INF-01 | Implement `infra/file_validation.py::validate_extension()` (whitelist per AGENTS.md supported formats) | SET-02 | Rejects non-whitelisted extensions with `UnsupportedFormatError` | Unit test: valid ext passes, invalid raises |
| INF-02 | Implement `infra/file_validation.py::validate_magic_bytes()` (sniff real file type, not just extension) | INF-01 | Detects mismatched extension vs. content (e.g. .png renamed .txt) | Unit test with a deliberately mislabeled sample fixture |
| INF-03 | Implement `infra/file_validation.py::validate_size()` (100MB cap) | INF-01 | Rejects file > 100MB with clear error, accepts under | Unit test with mocked oversized byte stream |
| INF-04 | Implement `infra/storage.py::save_upload()` (writes to `storage/{job_id}/original.*`) | SET-02 | File written to correct path, returns path string | Unit test: save, assert file exists at expected path |
| INF-05 | Implement `infra/storage.py::save_result()` | INF-04 | Result file written to `storage/{job_id}/result.*` | Unit test: save, assert exists |
| INF-06 | Implement `infra/storage.py::load_file()` and `delete_job_files()` | INF-04 | Load returns bytes; delete removes directory recursively | Unit tests for both paths, incl. deleting nonexistent job (no crash) |
| INF-07 | Implement `infra/cleanup.py::sweep_expired_jobs()` (queries DB for `expires_at < now`, deletes files, marks `expired`) | DB-06, INF-06 | Expired job's files removed, status updated to `expired` | Unit test: insert job with past `expires_at`, run sweep, assert file gone + status changed |
| INF-08 | Wire `sweep_expired_jobs()` into a FastAPI startup background loop (e.g. every hour) | INF-07 | App startup logs confirm scheduler registered | Manual: trigger function directly in test, not via real hour-long wait |
| INF-09 | Implement `infra/ffmpeg_runner.py::run_ffmpeg()` — list-args subprocess wrapper with timeout + kill on timeout | SET-09 | Raises `FFmpegTimeoutError` on forced timeout test; returns stdout/stderr on success | Unit test: run trivial ffmpeg command (e.g. `-version`) and assert success path; separate test forces timeout via short limit |
| INF-10 | Add storage quota check (`infra/storage.py::check_quota()`) before accepting new uploads | INF-04 | Returns `False`/raises when total storage dir exceeds configured cap | Unit test with mocked directory size over/under cap |

---

## API — Cross-Cutting (Schemas, Middleware, Health, Jobs Router)

| ID | Task | Depends On | Acceptance Criteria | Testing Requirement |
|---|---|---|---|---|
| API-01 | Define `schemas/common.py`: `ErrorResponse`, `JobStatusResponse` Pydantic models | SET-02 | Models match envelope shape in FINAL_ARCHITECTURE §7 | Unit test: instantiate + serialize to expected JSON keys |
| API-02 | Implement `utils/exceptions.py` custom exception classes (`UnsupportedFormatError`, `CapacityExceededError`, `FFmpegTimeoutError`, `DecryptionError`) | SET-02 | All exceptions subclass a common `AppError` with `code` + `message` attrs | Unit test: raise each, assert attrs present |
| API-03 | Implement `middleware/error_handler.py` mapping `AppError` subclasses → HTTP status + `ErrorResponse` body | API-01, API-02 | Raising `CapacityExceededError` in a route returns `400` with correct envelope | Integration test: hit a deliberately-erroring test route, assert response shape |
| API-04 | Implement `routes_health.py::GET /api/v1/health` | API-03 | Returns `200 {"status":"ok"}` | Integration test via `TestClient` |
| API-05 | Implement `services/job_service.py::create_job()`, `get_job_status()` (wraps DB-06) | DB-06 | Functions callable from a route without FastAPI imports inside | Unit test mirrors DB-06 but through service layer |
| API-06 | Implement `routes_jobs.py::GET /api/v1/jobs/{job_id}` | API-05 | Returns job status JSON; 404 for unknown id | Integration test: known id → 200, unknown id → 404 |
| API-07 | Implement `routes_jobs.py::GET /api/v1/jobs/{job_id}/download` (streams `result_path`) | INF-06, API-06 | Returns binary stream with correct content-type; 404 if no result yet | Integration test: download after a fake job marked done with a sample file |
| API-08 | Implement `routes_jobs.py::DELETE /api/v1/jobs/{job_id}` | INF-06, API-06 | Deletes files + marks DB row deleted; returns 204 | Integration test: delete, then confirm file gone and status reflects deletion |
| API-09 | Implement `routes_jobs.py::GET /api/v1/jobs?limit=&offset=` (list, paginated) | API-05 | Returns paginated list respecting `limit`/`offset` | Integration test with 3 seeded jobs, limit=2 returns 2 |
| API-10 | Register CORS middleware with explicit dev origin allowlist | SET-02 | OPTIONS preflight from Vite origin succeeds | Manual: browser dev console check, or integration test asserting CORS headers present |

---

## IMG — Image Module

| ID | Task | Depends On | Acceptance Criteria | Testing Requirement |
|---|---|---|---|---|
| IMG-01 | Define `core/compression/base.py::CompressionCodec` ABC (`compress(bytes)->bytes`, `decompress(bytes)->bytes`) | SET-02 | ABC raises `NotImplementedError` on direct instantiation calls | Unit test: subclass without implementing raises `TypeError` |
| IMG-02 | Implement `core/compression/image_rle.py` (RLE compress) | IMG-01 | Compressing a flat-color test image produces smaller byte output | Unit test with sample PNG fixture; assert output size < input |
| IMG-03 | Implement RLE decompress | IMG-02 | Decompressing IMG-02's output reproduces exact original bytes | Unit test: round-trip equality on sample fixture |
| IMG-04 | RLE error handling: malformed/corrupt compressed input | IMG-03 | Raises a clear `AppError` subclass, not a raw exception | Unit test: feed garbage bytes, assert specific exception type |
| IMG-05 | Implement `core/compression/image_huffman.py` — tree-building + canonical codes (encode side) | IMG-01 | Encoding a sample image produces a valid bitstream + header (symbol table) | Unit test: encode known small byte sequence, manually verify expected code lengths |
| IMG-06 | Implement Huffman decode side | IMG-05 | Decoding reproduces exact original bytes | Unit test: round-trip on sample fixture |
| IMG-07 | Huffman edge cases: empty input, single unique byte value | IMG-06 | Both cases handled without crash, round-trip still exact | Unit tests for both specific edge cases |
| IMG-08 | Implement `core/compression/registry.py` style dispatch (`get_codec("rle"|"huffman")`) | IMG-03, IMG-06 | Returns correct codec instance per string key; unknown key raises `UnsupportedFormatError` | Unit test for both valid and invalid keys |
| IMG-09 | Define `core/steganography/base.py::StegoCodec` ABC (`embed`, `extract`, `capacity`) | SET-02 | Same pattern as IMG-01 | Unit test: abstract instantiation fails |
| IMG-10 | Implement `core/steganography/image_lsb.py::capacity()` (max bits embeddable) | IMG-09 | Returns correct bit count for a known image size | Unit test against hand-calculated value for a small fixture |
| IMG-11 | Implement `image_lsb.py::embed()` | IMG-10 | Embedding alters only least-significant bits; image dimensions unchanged | Unit test: embed known message, inspect pixel diffs are ≤1 per channel |
| IMG-12 | Implement `image_lsb.py::extract()` | IMG-11 | Extracting from IMG-11's output reproduces exact original message | Unit test: embed→extract round-trip |
| IMG-13 | Capacity-exceeded error handling | IMG-10, IMG-11 | Embedding a message larger than capacity raises `CapacityExceededError` before corrupting the image | Unit test: oversized message, assert exception and that no file was written |
| IMG-14 | Implement `core/metrics/image_metrics.py::psnr()`, `ssim()`, `mse()` via scikit-image | SET-02 | Functions return expected metric type (float) on two sample arrays | Unit test: identical images → PSNR=inf or very high, SSIM=1.0, MSE=0 |
| IMG-15 | Implement `core/metrics/common_metrics.py::compression_ratio()`, `processing_time()` (`@timed` decorator from `utils/timing.py`) | SET-02 | Ratio = original_size/compressed_size; timing decorator records elapsed ms | Unit test on known byte sizes; timing test on a sleep(0.01) dummy function |
| IMG-16 | Implement `utils/timing.py::@timed` decorator | SET-02 | Decorated function's return value unchanged; elapsed time captured separately (e.g. via context or side-channel) | Unit test asserting captured time ≥ expected sleep duration |
| IMG-17 | Implement `services/image_service.py::compress_image()` orchestration (validate→codec→metrics→save→job record) | IMG-08, IMG-15, INF-04, INF-05, DB-06 | Calling the service end-to-end with a sample PNG produces a `done` job with result file + metrics rows | Integration-style unit test using temp dir + test DB |
| IMG-18 | Implement `services/image_service.py::decompress_image()` | IMG-17 | Round-trips a compress-job's output back to original | Unit test chaining compress then decompress service calls |
| IMG-19 | Implement `services/image_service.py::embed_message()` | IMG-12, IMG-13, INF-04, DB-06 | End-to-end embed produces `done` job with stego result file | Unit test with sample fixture + short message |
| IMG-20 | Implement `services/image_service.py::extract_message()` | IMG-19 | Extracts exact message from a job created by IMG-19 | Unit test chaining embed then extract |
| IMG-21 | Define `schemas/image.py` request/response Pydantic models | API-01 | Models validate required fields (`file`, `algorithm`, etc.) | Unit test: missing required field raises `ValidationError` |
| IMG-22 | Implement `POST /api/v1/image/compress` route | IMG-17, IMG-21, API-03 | Multipart upload returns `202` + `job_id`; invalid file returns `400` | Integration test: valid PNG → 202; .txt file → 400 |
| IMG-23 | Implement `POST /api/v1/image/decompress` route | IMG-18, IMG-21 | Given prior job_id or re-uploaded artifact, returns `202` + job_id | Integration test using a job_id from IMG-22's test |
| IMG-24 | Implement `POST /api/v1/image/embed` route | IMG-19, IMG-21 | Returns `202`; oversized message returns `400 CAPACITY_EXCEEDED` | Integration test: normal message → 202; huge message → 400 |
| IMG-25 | Implement `POST /api/v1/image/extract` route | IMG-20, IMG-21 | Returns `200` with message; wrong/no hidden data returns appropriate error | Integration test: valid stego file → 200 + correct message |
| IMG-26 | Implement `GET /api/v1/image/{job_id}/compare` route | IMG-17, IMG-19, DB-07 | Returns metrics object + original/result URLs for a completed job | Integration test against a seeded done job |
| IMG-27 | Add sample test fixtures: small PNG, small JPG (flat color + noisy) | — | Fixtures committed under `tests/fixtures/` | N/A (fixture creation task itself) |

---

## AUD — Audio Module

| ID | Task | Depends On | Acceptance Criteria | Testing Requirement |
|---|---|---|---|---|
| AUD-01 | Implement `core/compression/audio_bitrate.py::compress()` wrapping `infra/ffmpeg_runner.py` for bitrate reduction | INF-09 | Output WAV/MP3 file size smaller at lower target bitrate | Unit test using sample WAV fixture, assert output size < input |
| AUD-02 | Audio compress error handling (invalid bitrate param, corrupt input file) | AUD-01 | Raises clear `AppError`, doesn't leave partial/corrupt output file | Unit tests for both error cases |
| AUD-03 | Implement `core/steganography/audio_lsb.py::capacity()` for WAV samples | IMG-09 (reuse ABC) | Correct bit count for known WAV sample count | Unit test against hand-calculated value |
| AUD-04 | Implement `audio_lsb.py::embed()` (WAV only) | AUD-03 | Embeds without altering WAV header/sample count | Unit test: embed, verify sample count unchanged, audio still valid WAV |
| AUD-05 | Implement `audio_lsb.py::extract()` | AUD-04 | Exact message round-trip | Unit test: embed→extract |
| AUD-06 | Audio capacity-exceeded handling | AUD-03, AUD-04 | Raises `CapacityExceededError` before corrupting file | Unit test: oversized message |
| AUD-07 | Reject MP3 for embed at the core/service layer (per spec: WAV-only stego) | AUD-04 | Attempting embed on MP3 input raises `UnsupportedFormatError` | Unit test feeding MP3 fixture to embed function |
| AUD-08 | Implement `core/metrics/common_metrics.py` reuse for audio (ratio, time, capacity) — confirm no audio-specific fidelity metric per architecture decision | AUD-01, AUD-04 | Metrics dict contains exactly `compression_ratio`, `processing_time_ms`, `hidden_capacity_bits` | Unit test asserting dict keys |
| AUD-09 | Implement `services/audio_service.py::compress_audio()` | AUD-01, AUD-08, INF-04/05, DB-06 | End-to-end compress on sample WAV/MP3 produces `done` job | Unit test per media |
| AUD-10 | Implement `services/audio_service.py::decompress_audio()` | AUD-09 | Round-trip job chain works | Unit test |
| AUD-11 | Implement `services/audio_service.py::embed_message()` | AUD-05, AUD-06, AUD-07 | End-to-end embed on WAV produces `done` job; MP3 input rejected with clear error | Unit tests: WAV success, MP3 rejection |
| AUD-12 | Implement `services/audio_service.py::extract_message()` | AUD-11 | Extracts exact message from AUD-11 job | Unit test chaining embed→extract |
| AUD-13 | Define `schemas/audio.py` models | API-01 | Validates required fields | Unit test for missing-field rejection |
| AUD-14 | Implement `POST /api/v1/audio/compress` route | AUD-09, AUD-13 | Valid file → 202; invalid → 400 | Integration test both paths |
| AUD-15 | Implement `POST /api/v1/audio/decompress` route | AUD-10, AUD-13 | 202 on valid job_id/file | Integration test |
| AUD-16 | Implement `POST /api/v1/audio/embed` route | AUD-11, AUD-13 | WAV → 202; MP3 → 400 with clear error code | Integration test both paths |
| AUD-17 | Implement `POST /api/v1/audio/extract` route | AUD-12, AUD-13 | Valid stego WAV → 200 + message | Integration test |
| AUD-18 | Implement `GET /api/v1/audio/{job_id}/compare` route | AUD-09, AUD-11, DB-07 | Returns metrics + URLs for completed job | Integration test |
| AUD-19 | Add sample fixtures: short WAV, short MP3 | — | Fixtures committed | N/A |

---

## VID — Video Module

| ID | Task | Depends On | Acceptance Criteria | Testing Requirement |
|---|---|---|---|---|
| VID-01 | Implement `core/compression/video_transcode.py::compress()` (FFmpeg transcode, CRF/bitrate param) | INF-09 | Output MP4 plays correctly and is smaller at lower target bitrate | Unit test on short sample MP4, assert output size < input and file is a valid MP4 (e.g. via ffprobe check) |
| VID-02 | Video compress error handling (timeout, corrupt input, unsupported codec) | VID-01, INF-09 | Raises clear `AppError`, no orphaned ffmpeg process left running | Unit test forcing a short timeout; manual process-list check during dev |
| VID-03 | Implement frame extraction utility (`core/steganography/video_frame_embed.py::_extract_frames()`) via OpenCV | SET-02 | Extracts N raw frames from sample MP4 as arrays | Unit test: extract known frame count from short fixture |
| VID-04 | Implement lossless remux utility (`_remux_frames_lossless()`) | VID-03 | Re-muxed output from unmodified extracted frames is pixel-identical to original frames | Unit test: extract→remux round-trip, compare frame arrays exactly |
| VID-05 | Implement `video_frame_embed.py::capacity()` for chosen frame count | VID-03 | Correct bit count given frame dimensions × frame count | Unit test against hand-calculated value |
| VID-06 | Implement `video_frame_embed.py::embed()` (LSB on selected frames + lossless remux output) | VID-04, VID-05 | Output video frame-count and dimensions match original; message recoverable | Unit test: embed, verify file is valid MP4 via ffprobe |
| VID-07 | Implement `video_frame_embed.py::extract()` | VID-06 | Exact message round-trip from VID-06's output | Unit test: embed→extract |
| VID-08 | Video capacity-exceeded + corrupt-input error handling | VID-05, VID-06, VID-07 | Clear `AppError` raised in both cases, no partial files left | Unit tests for both |
| VID-09 | Implement video metrics (ratio, time, capacity) — confirm compress and embed are tracked as separate artifacts (per architecture §4.3) | VID-01, VID-06 | Metrics dict for embed job does NOT include a "compressed size" field conflated with the compress job's | Unit test asserting separate metric sets per operation type |
| VID-10 | Implement `services/video_service.py::compress_video()` using `BackgroundTasks` pattern | VID-01, VID-09, INF-04/05, DB-06 | Job created as `pending`→`processing`→`done` asynchronously | Unit test simulating background task execution against test DB |
| VID-11 | Implement `services/video_service.py::embed_message()` (async) | VID-06, VID-08 | Job lifecycle correct; output is a lossless stego artifact, not transcoded | Unit test |
| VID-12 | Implement `services/video_service.py::extract_message()` (async) | VID-07 | Returns extracted message once job done | Unit test |
| VID-13 | Define `schemas/video.py` models | API-01 | Validates required fields (`frame_count`, etc.) | Unit test for missing-field rejection |
| VID-14 | Implement `POST /api/v1/video/compress` route (returns 202 immediately, runs via BackgroundTasks) | VID-10, VID-13 | Returns 202 quickly even before processing finishes; job pollable afterward | Integration test: assert response time is fast, then poll job to `done` |
| VID-15 | Implement `POST /api/v1/video/embed` route (async) | VID-11, VID-13 | 202 returned; oversized message → 400 on validation before job starts (pre-check using `capacity()`) | Integration test both paths |
| VID-16 | Implement `POST /api/v1/video/extract` route (async) | VID-12, VID-13 | 202 returned, job result contains message when polled | Integration test |
| VID-17 | Implement `GET /api/v1/video/{job_id}/compare` route | VID-10, VID-11, DB-07 | Returns metrics + URLs once done | Integration test |
| VID-18 | Add sample fixture: short (~2s) low-res MP4 | — | Fixture committed, small enough for fast CI runs | N/A |

---

## SEC — Security (AES, Optional Layer)

| ID | Task | Depends On | Acceptance Criteria | Testing Requirement |
|---|---|---|---|---|
| SEC-01 | Implement `core/security/aes_cipher.py::derive_key(password, salt)` | SET-02 | Deterministic key for same password+salt; different salt → different key | Unit test: same inputs → same key, different salt → different key |
| SEC-02 | Implement `aes_cipher.py::encrypt_bytes()` (AES-GCM) | SEC-01 | Output includes nonce/tag needed for decryption; ciphertext differs from plaintext | Unit test: encrypt, assert output ≠ input, length sane |
| SEC-03 | Implement `aes_cipher.py::decrypt_bytes()` | SEC-02 | Decrypting with correct key/password reproduces exact plaintext | Unit test: encrypt→decrypt round-trip |
| SEC-04 | Decryption failure handling (wrong password/key) | SEC-03 | Raises `DecryptionError`, never returns garbage silently | Unit test: wrong password raises specific exception |
| SEC-05 | Wire optional encryption into `image_service.py::embed_message()` (encrypt before LSB embed) | SEC-02, IMG-19 | `encrypt=True` + password produces a job whose extracted-then-decrypted message matches original | Unit test: embed encrypted → extract → decrypt → compare |
| SEC-06 | Wire optional decryption into `image_service.py::extract_message()` | SEC-03, SEC-04, IMG-20 | Correct password decrypts; wrong password returns clear `400` error, not corrupted text | Unit tests both paths |
| SEC-07 | Wire encryption/decryption into `audio_service.py` embed/extract | SEC-02, SEC-03, AUD-11, AUD-12 | Same round-trip guarantee as SEC-05/06 for audio | Unit tests both paths |
| SEC-08 | Wire encryption/decryption into `video_service.py` embed/extract | SEC-02, SEC-03, VID-11, VID-12 | Same round-trip guarantee for video | Unit tests both paths |
| SEC-09 | Confirm salt is persisted on `jobs.salt`, password/key are never logged or persisted (code review checklist task) | SEC-05–08, DB-02 | Grep codebase confirms no `password` or derived key appears in any log statement or DB column | Manual review + a unit test asserting `Job` model has no plaintext-password field |

---

## FE — Frontend

| ID | Task | Depends On | Acceptance Criteria | Testing Requirement |
|---|---|---|---|---|
| FE-01 | Implement `api/client.ts` base fetch wrapper with error envelope normalization | SET-03 | Throws a typed error object matching backend's `ErrorResponse` shape on non-2xx | Unit test (vitest) mocking a 400 response, asserting thrown error shape |
| FE-02 | Define TypeScript types in `types/job.ts`, `types/metrics.ts`, `types/media.ts` matching backend schemas | API-01, IMG-21, AUD-13, VID-13 | Types compile and match field names exactly | Type-check via `tsc --noEmit` |
| FE-03 | Implement `api/imageApi.ts` (compress/decompress/embed/extract/compare calls) | FE-01, FE-02, IMG-22–26 | Each function returns typed response, hits correct endpoint | Unit test mocking fetch, asserting correct URL/method per call |
| FE-04 | Implement `api/audioApi.ts` | FE-01, FE-02, AUD-14–18 | Same as FE-03 for audio | Unit test mocking fetch |
| FE-05 | Implement `api/videoApi.ts` | FE-01, FE-02, VID-14–17 | Same as FE-03 for video | Unit test mocking fetch |
| FE-06 | Implement `api/jobsApi.ts` (status/download/list) | FE-01, FE-02, API-06–09 | Functions hit correct job endpoints | Unit test mocking fetch |
| FE-07 | Implement `hooks/useJobPolling.ts` (polls until done/error, configurable interval) | FE-06 | Hook stops polling once status is `done` or `error`; exposes latest status to component | Unit test (vitest + fake timers): simulate 3 polls, assert stop condition |
| FE-08 | Implement `hooks/useFileUpload.ts` (handles file selection + multipart submission state) | FE-01 | Exposes `progress`, `error`, `result` state correctly across a mocked upload | Unit test with mocked upload function |
| FE-09 | Build `components/common/Button.tsx`, `ErrorBanner.tsx`, `LoadingSpinner.tsx` | SET-04 | Each renders correctly with required props; ErrorBanner shows passed message | Component render test (React Testing Library) for each |
| FE-10 | Build `components/upload/UploadDropzone.tsx` | FE-09 | Drag-drop and click-to-browse both trigger file-selected callback | RTL test: simulate file drop, assert callback fired with file |
| FE-11 | Build `components/upload/UploadProgress.tsx` | FE-09 | Renders percentage/progress bar from a numeric prop | RTL test: prop=50 renders 50% indicator |
| FE-12 | Build `components/jobs/JobStatusBadge.tsx` | FE-09 | Renders correct color/label per status enum value | RTL test: one assertion per status value |
| FE-13 | Build `components/stego/MessageInput.tsx` | FE-09 | Textarea bound to value/onChange; shows char count | RTL test: typing updates char count |
| FE-14 | Build `components/stego/EncryptionToggle.tsx` (checkbox + conditional password field) | FE-09 | Password field only renders when toggle is on | RTL test: toggle on reveals password input |
| FE-15 | Build `components/stego/CapacityIndicator.tsx` | FE-09 | Shows warning state when message length exceeds capacity prop | RTL test: over-capacity props render warning class/text |
| FE-16 | Build `components/metrics/MetricsTable.tsx` | FE-09 | Renders a row per metric key/value from props | RTL test with sample metrics object |
| FE-17 | Build `components/metrics/MetricsChart.tsx` (recharts bar/line for ratio/time) | FE-16 | Renders chart container without crashing given sample data | RTL smoke test (renders without throwing) |
| FE-18 | Build `components/comparison/ImageCompareView.tsx` (before/after slider or side-by-side) | FE-09 | Displays both `original_url` and `result_url` images | RTL test: both img src attributes present |
| FE-19 | Build `components/comparison/AudioCompareView.tsx` (A/B audio players) | FE-09 | Two `<audio>` elements with correct `src` props | RTL test |
| FE-20 | Build `components/comparison/VideoCompareView.tsx` (A/B video players) | FE-09 | Two `<video>` elements with correct `src` props | RTL test |
| FE-21 | Build `pages/ImagePage.tsx` wiring upload → embed/compress choice → job polling → compare view | FE-03, FE-07, FE-10, FE-13–15, FE-18 | Full manual flow: upload sample PNG, compress, see result + metrics | Integration/E2E-lite test mocking imageApi, asserting page reaches "done" state |
| FE-22 | Build `pages/AudioPage.tsx` (mirrors FE-21 for audio) | FE-04, FE-07, FE-10, FE-13–15, FE-19 | Same manual flow for WAV | Mocked integration test |
| FE-23 | Build `pages/VideoPage.tsx` (mirrors FE-21 for video, shows async progress clearly) | FE-05, FE-07, FE-10, FE-13–15, FE-20 | Same manual flow for MP4, with visible "processing" state during polling | Mocked integration test incl. pending→done transition |
| FE-24 | Build `pages/HomePage.tsx` (media-type selector) | SET-04 | Three links/cards route to Image/Audio/Video pages | RTL test: clicking each card navigates correctly |
| FE-25 | Build `pages/JobHistoryPage.tsx` (optional, lists recent jobs) | FE-06 | Renders a list from `GET /jobs`, shows status badges | RTL test with mocked job list |
| FE-26 | Wire `router.tsx` with all routes | FE-21–25 | All routes resolve to correct page components | RTL test: navigate to each path, assert correct heading rendered |
| FE-27 | Responsive layout pass (Tailwind breakpoints on upload/compare views) | FE-18–20 | Pages usable at mobile width (375px) without horizontal scroll/overlap | Manual check at 375px/768px/1280px viewports |

---

## TEST — Cross-Cutting Test & Hardening Tasks

| ID | Task | Depends On | Acceptance Criteria | Testing Requirement |
|---|---|---|---|---|
| TEST-01 | Integration test: full image compress→download round-trip via `TestClient` | IMG-22, API-07 | Test passes in CI | Self-describing |
| TEST-02 | Integration test: full audio embed→extract round-trip via `TestClient` | AUD-16, AUD-17 | Test passes in CI | Self-describing |
| TEST-03 | Integration test: full video compress job lifecycle (pending→done) via `TestClient` + background task execution | VID-14 | Test passes in CI | Self-describing |
| TEST-04 | Security test: FFmpeg runner rejects shell-metacharacter-laden filenames (injection attempt) | INF-09 | Malicious filename input does not reach a shell; raises validation error instead | Unit test with a crafted filename string |
| TEST-05 | Load/perf sanity check: time a "normal" sample video compress job, record actual duration vs. 30s NFR | VID-10 | Result documented in `docs/perf_notes.md`, not asserted as a hard CI gate | Manual timing run, recorded not enforced |
| TEST-06 | Quota test: simulate storage dir near cap, confirm new upload rejected with `507` | INF-10 | Test passes in CI | Self-describing |
| TEST-07 | Cleanup sweep test: seed an expired job, run sweep, confirm files removed and status updated | INF-07 | Test passes in CI | Self-describing |

---

## DOC — Documentation & Delivery

| ID | Task | Depends On | Acceptance Criteria | Testing Requirement |
|---|---|---|---|---|
| DOC-01 | Auto-generate + review FastAPI OpenAPI docs (`/docs`) match FINAL_ARCHITECTURE §7 | All API/IMG/AUD/VID routes done | `/docs` page lists all endpoints with correct request/response shapes | Manual review against spec doc |
| DOC-02 | Write backend `README.md` (setup, run, test, env vars) | SET-02, SET-09 | A new developer can follow it to run the app from scratch | Manual: have someone else follow it |
| DOC-03 | Write frontend `README.md` (setup, run, test) | SET-03 | Same standard as DOC-02 | Manual follow-through |
| DOC-04 | Write technical report covering architecture, algorithms, metrics analysis, known limitations (JPG boundary, video stego/compress split, 30s NFR caveat) | TEST-05, all modules | Report addresses each flagged architectural decision explicitly | Peer review |
| DOC-05 | Record presentation/demo video covering all three media types + steganography + metrics | All FE/BE feature tasks | Video demonstrates each required feature from AGENTS.md | Peer review against feature checklist |

---

## Summary

- **Total tasks:** ~140, each scoped to fit under 2 hours.
- **Critical path:** `SET -> DB/INF -> API (cross-cutting) -> IMG -> (AUD, VID in parallel) -> SEC -> FE -> TEST/DOC`.
- **Parallelization opportunity:** Once `API-*` and `INF-*` foundations are done, `IMG-*`, `AUD-*`, and `VID-*` tracks can be worked simultaneously by separate engineers, since each only depends on shared infra/db/schema tasks, not on each other.
- **Highest risk-concentration tasks:** `VID-04`/`VID-06` (lossless remux correctness), `IMG-05`-`IMG-07` (Huffman correctness), `SEC-09` (security review), `INF-09`/`TEST-04` (FFmpeg safety).