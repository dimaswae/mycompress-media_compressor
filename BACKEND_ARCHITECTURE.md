# BACKEND_ARCHITECTURE.md — `mycompress` FastAPI Backend

Design follows AGENTS.md's clean-architecture rule: **API layer ⟂ business logic ⟂ I/O**, composition over large classes, type hints + docstrings everywhere.

---

## 1. Layering Model

```
Router (HTTP concerns only)
   │  parses request, calls service, formats response
   ▼
Service (orchestration / use-case logic)
   │  e.g. "compress image": validate → call codec → call metrics → persist
   ▼
Core / Domain (pure logic, no FastAPI, no I/O side-effects beyond files)
   │  codecs, steganography algorithms, metrics calculators
   ▼
Infra (storage, job queue, FFmpeg subprocess, crypto)
```

Rule of thumb: **routers never import `cv2`/`PIL`/`ffmpeg` directly** — they only call services. This keeps business logic testable without spinning up FastAPI, and lets image/audio/video share infra (storage, jobs) without duplicating it.

---

## 2. Folder Structure

```
backend/
├── app/
│   ├── main.py                      # FastAPI() instance, router registration, CORS, startup/shutdown
│   ├── config.py                    # Settings (env vars: upload limits, storage path, secret key)
│   ├── dependencies.py               # Shared FastAPI Depends() — e.g. get_job_store(), get_settings()
│   │
│   ├── api/                         # ── ROUTER LAYER (HTTP only) ──
│   │   ├── __init__.py
│   │   ├── deps.py                  # request-scoped deps: validate_upload(), get_current_job()
│   │   ├── routes_image.py
│   │   ├── routes_audio.py
│   │   ├── routes_video.py
│   │   ├── routes_jobs.py           # generic job status/result/download endpoints
│   │   └── routes_health.py
│   │
│   ├── schemas/                     # ── PYDANTIC MODELS (request/response contracts) ──
│   │   ├── __init__.py
│   │   ├── common.py                # JobStatus, ErrorResponse, MetricsResponse
│   │   ├── image.py                 # ImageCompressRequest, ImageEmbedRequest, ...
│   │   ├── audio.py
│   │   └── video.py
│   │
│   ├── services/                    # ── ORCHESTRATION / USE CASES ──
│   │   ├── __init__.py
│   │   ├── image_service.py         # compress_image(), decompress_image(), embed(), extract(), compare()
│   │   ├── audio_service.py
│   │   ├── video_service.py
│   │   └── job_service.py           # create_job(), update_status(), get_result()
│   │
│   ├── core/                        # ── PURE DOMAIN LOGIC (no FastAPI imports) ──
│   │   ├── __init__.py
│   │   ├── compression/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # CompressionCodec ABC (compress/decompress interface)
│   │   │   ├── image_rle.py
│   │   │   ├── image_huffman.py
│   │   │   ├── audio_bitrate.py     # wraps ffmpeg via infra/ffmpeg_runner
│   │   │   └── video_transcode.py   # wraps ffmpeg via infra/ffmpeg_runner
│   │   │
│   │   ├── steganography/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # StegoCodec ABC (embed/extract interface)
│   │   │   ├── image_lsb.py
│   │   │   ├── audio_lsb.py
│   │   │   └── video_frame_embed.py
│   │   │
│   │   ├── metrics/
│   │   │   ├── __init__.py
│   │   │   ├── image_metrics.py     # PSNR, SSIM, MSE (scikit-image)
│   │   │   ├── common_metrics.py    # compression ratio, processing time, hidden capacity
│   │   │   └── registry.py          # dispatch metrics calc by media type
│   │   │
│   │   └── security/
│   │       ├── __init__.py
│   │       └── aes_cipher.py        # encrypt_bytes()/decrypt_bytes() via `cryptography`
│   │
│   ├── infra/                       # ── I/O, EXTERNAL PROCESSES, STORAGE ──
│   │   ├── __init__.py
│   │   ├── storage.py               # save_upload(), load_file(), cleanup_job_files()
│   │   ├── ffmpeg_runner.py         # subprocess wrapper, timeout, safe arg-building (no shell=True)
│   │   ├── job_store.py             # in-memory or Redis-backed job status store
│   │   └── file_validation.py       # MIME sniffing, extension whitelist, size check
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── timing.py                # @timed decorator for processing-time metric
│   │   └── exceptions.py            # custom exceptions: UnsupportedFormatError, CapacityExceededError, etc.
│   │
│   └── middleware/
│       ├── __init__.py
│       └── error_handler.py         # maps custom exceptions → HTTP error responses
│
├── tests/
│   ├── unit/
│   │   ├── core/
│   │   │   ├── test_image_rle.py
│   │   │   ├── test_image_huffman.py
│   │   │   ├── test_image_lsb.py
│   │   │   ├── test_audio_bitrate.py
│   │   │   ├── test_audio_lsb.py
│   │   │   ├── test_video_transcode.py
│   │   │   ├── test_video_frame_embed.py
│   │   │   └── test_metrics.py
│   │   └── services/
│   │       ├── test_image_service.py
│   │       ├── test_audio_service.py
│   │       └── test_video_service.py
│   ├── integration/
│   │   ├── test_image_routes.py
│   │   ├── test_audio_routes.py
│   │   └── test_video_routes.py
│   └── fixtures/
│       ├── sample.png / sample.jpg
│       ├── sample.wav / sample.mp3
│       └── sample.mp4
│
├── requirements.txt
├── Dockerfile                       # installs ffmpeg system package
└── pytest.ini
```

**Why this split:**
- `core/` has zero FastAPI or HTTP awareness — every codec/stego/metric function is unit-testable with plain bytes/arrays in, bytes/arrays out. Matches AGENTS.md's "separate business logic from API layer."
- `compression/` and `steganography/` each define a small ABC (`base.py`) so image/audio/video implementations are interchangeable — composition over large classes.
- `services/` is the only layer allowed to chain core calls together (e.g. "embed, then encrypt, then save, then compute metrics") and is what routers call.
- `infra/` isolates anything that touches the filesystem, subprocess, or external state — easy to mock in tests.

---

## 3. API Routes

Base path: `/api/v1`

### 3.1 Health

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/health` | Liveness check |

### 3.2 Image

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/image/compress` | Upload image, params: `algorithm` (`rle`\|`huffman`). Returns `job_id` |
| POST | `/api/v1/image/decompress` | Upload compressed payload, params: `algorithm`. Returns `job_id` |
| POST | `/api/v1/image/embed` | Upload image + `message` (+ optional `encrypt`, `password`). Returns `job_id` |
| POST | `/api/v1/image/extract` | Upload stego image (+ optional `password`). Returns extracted message |
| GET | `/api/v1/image/{job_id}/compare` | Returns metrics (PSNR/SSIM/MSE/ratio/time) + before/after file URLs |

### 3.3 Audio

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/audio/compress` | Upload WAV/MP3, params: `target_bitrate`. Returns `job_id` |
| POST | `/api/v1/audio/decompress` | (passthrough/transcode-back where applicable). Returns `job_id` |
| POST | `/api/v1/audio/embed` | Upload WAV + `message` (+ optional `encrypt`, `password`). WAV only, per spec |
| POST | `/api/v1/audio/extract` | Upload stego WAV (+ optional `password`). Returns extracted message |
| GET | `/api/v1/audio/{job_id}/compare` | Returns metrics (ratio/time/capacity) + before/after file URLs |

### 3.4 Video

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/video/compress` | Upload MP4, params: `codec`, `crf`/`bitrate`. Returns `job_id` (async) |
| POST | `/api/v1/video/embed` | Upload MP4 + `message`, params: `frame_indices` or `frame_count` (+ `encrypt`, `password`). Returns `job_id` (async) |
| POST | `/api/v1/video/extract` | Upload stego MP4 (+ `password`). Returns `job_id` (async) |
| GET | `/api/v1/video/{job_id}/compare` | Returns metrics (ratio/time/capacity) + before/after file URLs |

### 3.5 Jobs (generic, cross-media)

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/jobs/{job_id}` | Status: `pending`\|`processing`\|`done`\|`error` |
| GET | `/api/v1/jobs/{job_id}/download` | Download processed result file |
| DELETE | `/api/v1/jobs/{job_id}` | Cleanup job files |

**Design notes:**
- All "processing" endpoints return a `job_id` immediately and run work via `BackgroundTasks` (per TASKS.md M1.3 decision) — image/audio can resolve fast, video almost never will within the request lifecycle.
- `extract` endpoints take a `password` param when content was AES-encrypted; missing/wrong password → `400` with a clear "decryption failed" error, never a silent garbage payload.
- `compare` is read-only and idempotent — it doesn't reprocess, just reads stored before/after files + cached metrics from the job record.

---

## 4. Example Request Flow (Image Embed)

```
POST /api/v1/image/embed
   │
   ▼
routes_image.py::embed_image()
   - validates file via api/deps.py::validate_upload()
   - calls services/image_service.py::embed_message(file, message, encrypt, password)
   │
   ▼
image_service.py
   - infra/storage.py::save_upload()
   - if encrypt: core/security/aes_cipher.py::encrypt_bytes()
   - core/steganography/image_lsb.py::embed()  [raises CapacityExceededError if too small]
   - core/metrics/common_metrics.py::hidden_capacity(), processing_time()
   - infra/storage.py::save_result()
   - services/job_service.py::create_job(status="done", result_path=..., metrics=...)
   │
   ▼
returns { "job_id": "...", "status": "done" }
```

Errors (e.g. `CapacityExceededError`) bubble up to `middleware/error_handler.py`, which maps them to a `400` with a structured `ErrorResponse` — routers never write their own try/except blocks for domain errors.

---

## 5. Cross-Cutting Concerns

| Concern | Where it lives |
|---|---|
| Upload size limit (100MB) | `infra/file_validation.py`, enforced in `api/deps.py` before any processing starts |
| MIME/extension whitelist | `infra/file_validation.py` |
| Async/background jobs | `infra/job_store.py` + `services/job_service.py`, started via FastAPI `BackgroundTasks` in routers |
| FFmpeg safety (no shell injection) | `infra/ffmpeg_runner.py` — always list-form subprocess args, never `shell=True`, sanitized temp filenames (never user-supplied names) |
| AES encryption hook | `core/security/aes_cipher.py`, called optionally from each `*_service.py` before the stego embed step |
| Metrics computation | `core/metrics/`, dispatched via `registry.py` so services don't need per-media if/else branching |
| Error → HTTP mapping | `middleware/error_handler.py` registered once in `main.py` |
| Job cleanup | scheduled task or `DELETE /jobs/{id}`, both calling `infra/storage.py::cleanup_job_files()` |

---

## 6. Suggested `requirements.txt` Core Set

```
fastapi
uvicorn[standard]
pydantic
pydantic-settings
python-multipart
pillow
opencv-python-headless
numpy
scikit-image
cryptography
ffmpeg-python   # or raw subprocess via infra/ffmpeg_runner.py
pytest
pytest-asyncio
httpx           # for TestClient / integration tests
```

(`ffmpeg` itself is a system binary, not a pip package — installed in `Dockerfile`.)