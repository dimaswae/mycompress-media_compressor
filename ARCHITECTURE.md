# ARCHITECTURE.md — `mycompress` System Architecture

Role: Senior architecture review of `AGENTS.md`, `PROJECT_SPEC.md`, and the prior `BACKEND_ARCHITECTURE.md`. This document supersedes the earlier backend doc where they conflict.

---

## 1. Review of Prior Architecture

**What was right and is kept:**
- Layering (router → service → core → infra) is sound and matches AGENTS.md's clean-architecture rule.
- ABC-based codec/stego interfaces (composition over large classes) is the correct pattern for three media types sharing structure.
- Per-media routers + a generic job resource is the right REST shape.

**Gaps found on review:**

| # | Gap | Why it matters |
|---|---|---|
| G1 | No **persistence layer** — job state was assumed in-memory/Redis with no schema | Job history, metrics, and file metadata need a durable record beyond process lifetime; "Compare original and processed files" implies the system remembers both. |
| G2 | No **frontend architecture** was produced at all | Required deliverable; also the backend API shape should be informed by what the UI actually needs (job polling, comparison view, A/B audio/video playback). |
| G3 | No **file lifecycle / retention policy** | 100MB uploads × 3 media types will fill disk fast without a defined TTL + cleanup trigger. |
| G4 | No **API versioning / error contract spec** beyond a table — needed as an actual OpenAPI-style spec other agents/devs can build against without re-deriving conventions | Ambiguity here causes frontend/backend drift. |
| G5 | No explicit **concurrency/rate-limiting** story | Video transcoding is CPU/time-expensive; without limits, concurrent uploads can exhaust the host. |
| G6 | No **decompress flow definition** — what exactly does a user upload to "decompress"? (the compressed artifact, or do we even expose a separate decompressed file at all, since compress→decompress is usually demonstrated round-trip in one job) | Spec says "Decompress media files" as a top-level requirement; routes existed but the data contract was vague. |
| G7 | No **format-conversion boundary defined for JPG** (lossy format + custom RLE/Huffman) | Carried over from TASKS.md risk list but never resolved at the architecture level — needs a final decision, not just a flagged risk. |
| G8 | No **CORS/static-file-serving** decision for how the frontend actually retrieves result files | Needed for `compare` view and downloads to function across origins in dev vs. prod. |

This document resolves G1–G8 below.

---

## 2. Technical Risks (Architecture-Level)

| Risk | Severity | Resolution Strategy |
|---|---|---|
| **R1 — Video re-encode destroys frame-embedded stego data** | High | Architecture mandates: video stego embedding always writes a **lossless intermediate** (e.g., FFV1/raw-frame remux) as the stego artifact, distinct from the "compressed" artifact. Compression and steganography on video are two separate output files, never chained losslessly→lossy in one step. See §4.3. |
| **R2 — 30s NFR unrealistic for video transcoding** | Medium | Architecture treats this as a *target for "normal" files* (defined as ≤ 30s of 720p video) and surfaces estimated time to the user; not a hard constraint enforced by the system. |
| **R3 — FFmpeg subprocess as attack surface (command injection, resource exhaustion)** | High | All FFmpeg calls go through one hardened wrapper (`infra/ffmpeg_runner.py`): list-args only, generated filenames only (never user input), hard timeout + kill, CPU/time ulimits if containerized. |
| **R4 — Disk fills from uploads + intermediate + result files** | Medium | Defined retention policy (§6) + scheduled cleanup job + per-job storage quota check before accepting new uploads. |
| **R5 — Synchronous request blocking on video jobs** | Medium | Background-task job model is mandatory for video (optional for image/audio), per prior decision — reaffirmed here as architecture-level, not implementation detail. |
| **R6 — Huffman coding correctness (edge cases: empty file, single symbol)** | Medium | Addressed at implementation/testing stage (TASKS.md M2), not an architecture concern, but flagged here so it isn't dropped. |
| **R7 — AES key/password handling** | Medium | Passwords are **never persisted** — not in DB, not in logs. Only a salt (if using password-derived keys) is stored alongside the job record, never the key or password itself. |
| **R8 — Job store as single point of failure if in-memory** | Low–Medium | Architecture specifies SQLite (or Postgres if scaling matters) for job/metrics persistence instead of pure in-memory dict, so a backend restart doesn't silently orphan jobs the frontend is still polling. |
| **R9 — Frontend polling vs. real-time updates** | Low | Polling is sufficient given short-lived jobs; WebSocket/SSE explicitly deferred as out-of-scope to avoid overengineering for a project of this size. |
| **R10 — MIME spoofing on upload (extension lies about content)** | Medium | `infra/file_validation.py` performs magic-byte sniffing (not just extension/MIME header trust) before any processing. |

---

## 3. Final Architecture — System View

```
┌─────────────────────────────────────────────────────────────────┐
│                         React + Vite + Tailwind                  │
│   Upload UI → Job Status Poller → Comparison/Metrics Dashboard   │
└───────────────────────────┬───────────────────────────────────────┘
                            │ REST (JSON + multipart), same-origin or CORS in dev
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
│  Routers → Services → Core (codecs/stego/metrics/security) →     │
│  Infra (storage, ffmpeg, job store, validation)                  │
└───────────────────────────┬───────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────────┐
              ▼             ▼                 ▼
        Filesystem      SQLite DB         FFmpeg (subprocess)
     (uploads/results)  (jobs, metrics)
```

Single-process deployment is sufficient for this project's scope (no message broker, no separate worker fleet) — `BackgroundTasks` + SQLite is the right-sized solution; a Celery/Redis queue would be overengineering for a project of this size and is explicitly rejected.

---

## 4. Final Architecture — Resolved Design Decisions

### 4.1 Compress / Decompress Contract (resolves G6)
- **Compress**: upload original → returns `job_id` with a `compressed` artifact + metrics (ratio, time). The compressed artifact is downloadable.
- **Decompress**: takes a `job_id` (or re-uploads the compressed artifact directly) → returns the reconstructed file. This is primarily how round-trip fidelity is demonstrated and how PSNR/SSIM/MSE get computed (original vs. reconstructed).
- `compare` always operates on **original vs. reconstructed-after-decompress**, not original vs. raw-compressed-bytes (which usually aren't directly comparable as an image/audio/video, especially for custom RLE/Huffman containers).

### 4.2 JPG + Custom Compression Boundary (resolves G7)
- Decision: custom RLE/Huffman operate on the **decoded raw pixel buffer** (via Pillow/NumPy), not on JPEG's native bytestream. Input format (PNG or JPG) is decoded to a common raw representation first; this is documented clearly in the technical report so results aren't misread as "we out-compressed JPEG."
- PNG round-trips losslessly through this pipeline; JPG round-trips losslessly **relative to its own decoded pixels** (i.e., decode JPG once, then RLE/Huffman + LSB operate losslessly on that raw buffer — the JPEG decode step itself is the only lossy point, and it happens once, at upload).

### 4.3 Video Compression vs. Steganography Separation (resolves R1)
- **Compress** path: original MP4 → FFmpeg transcode → compressed MP4. Metrics computed on file size/time only (no frame-level fidelity metric required by spec).
- **Embed** path: original MP4 → extract target frames → LSB-embed in raw frame data → **remux losslessly** (no re-encoding step) into a stego container. This is a separate artifact from "compressed video" — the two features are not chained. If a user wants both, that's two sequential jobs, with the explicit caveat (documented in UI copy) that compressing a stego video will likely destroy the hidden message.

### 4.4 Storage & Retention (resolves G3, R4)
- Each job gets a UUID-named directory: `storage/{job_id}/original.*`, `storage/{job_id}/result.*`.
- Default TTL: 24 hours. A scheduled cleanup task (FastAPI startup background loop or cron) deletes job directories past TTL and marks the DB record `expired`.
- Quota check: reject new uploads with `507` if total storage dir exceeds a configured cap (e.g. 5GB for a demo deployment).

### 4.5 Persistence Layer (resolves G1)
SQLite is sufficient for project scope (single-instance demo app, not a production multi-tenant service). See §8 for schema.

### 4.6 API Conventions (resolves G4)
- Base path `/api/v1`, JSON bodies for non-file params alongside `multipart/form-data` file uploads.
- All error responses follow one shape: `{ "error": { "code": str, "message": str, "details": dict|null } }`.
- All success responses for processing endpoints: `{ "job_id": str, "status": "pending"|"processing"|"done"|"error" }`.
- Pagination not required (no list-heavy endpoints at this scope) except optionally `GET /api/v1/jobs` (list recent jobs) — included as a nice-to-have, paginated via `limit`/`offset`.

### 4.7 CORS & File Serving (resolves G8)
- Dev: FastAPI serves on `:8000`, Vite dev server on `:5173`, CORS middleware allows the Vite origin explicitly (not `*`, since cookies/auth could be added later).
- Result files served via `GET /api/v1/jobs/{id}/download` (streamed from disk by the backend) rather than exposing the storage directory as static files — keeps access controlled through the job layer and makes the eventual addition of auth/expiry trivial.

---

## 5. Backend Folder Structure (Final)

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   ├── routes_image.py
│   │   ├── routes_audio.py
│   │   ├── routes_video.py
│   │   ├── routes_jobs.py
│   │   └── routes_health.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py
│   │   ├── image.py
│   │   ├── audio.py
│   │   └── video.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── image_service.py
│   │   ├── audio_service.py
│   │   ├── video_service.py
│   │   └── job_service.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── compression/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── image_rle.py
│   │   │   ├── image_huffman.py
│   │   │   ├── audio_bitrate.py
│   │   │   └── video_transcode.py
│   │   ├── steganography/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── image_lsb.py
│   │   │   ├── audio_lsb.py
│   │   │   └── video_frame_embed.py
│   │   ├── metrics/
│   │   │   ├── __init__.py
│   │   │   ├── image_metrics.py
│   │   │   ├── common_metrics.py
│   │   │   └── registry.py
│   │   └── security/
│   │       ├── __init__.py
│   │       └── aes_cipher.py
│   │
│   ├── infra/
│   │   ├── __init__.py
│   │   ├── storage.py
│   │   ├── ffmpeg_runner.py
│   │   ├── job_store.py          # SQLite-backed (see §8), not in-memory
│   │   ├── file_validation.py    # incl. magic-byte sniffing
│   │   └── cleanup.py            # TTL-based retention sweep (NEW)
│   │
│   ├── db/                        # NEW — persistence
│   │   ├── __init__.py
│   │   ├── database.py            # SQLAlchemy engine/session
│   │   ├── models.py              # Job, MetricRecord ORM models
│   │   └── migrations/            # Alembic (optional, even SQLite benefits)
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── timing.py
│   │   └── exceptions.py
│   │
│   └── middleware/
│       ├── __init__.py
│       └── error_handler.py
│
├── tests/
│   ├── unit/
│   │   ├── core/
│   │   └── services/
│   ├── integration/
│   └── fixtures/
│
├── storage/                       # NEW — gitignored runtime upload/result dir
├── requirements.txt
├── Dockerfile
├── alembic.ini
└── pytest.ini
```

Changes from prior draft: added `db/` (persistence), `infra/cleanup.py` (retention), `storage/` made explicit as a top-level runtime directory rather than implied inside `infra/storage.py` logic only.

---

## 6. Frontend Folder Structure

```
frontend/
├── public/
│   └── favicon.svg
│
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── router.tsx                      # routes: /image, /audio, /video, /jobs/:id
│   │
│   ├── api/                            # ── API CLIENT LAYER ──
│   │   ├── client.ts                   # base fetch wrapper, error normalization
│   │   ├── imageApi.ts
│   │   ├── audioApi.ts
│   │   ├── videoApi.ts
│   │   └── jobsApi.ts
│   │
│   ├── types/
│   │   ├── job.ts                      # JobStatus, JobResult
│   │   ├── metrics.ts
│   │   └── media.ts
│   │
│   ├── hooks/
│   │   ├── useJobPolling.ts            # polls /jobs/{id} until done/error
│   │   ├── useFileUpload.ts
│   │   └── useMetrics.ts
│   │
│   ├── pages/
│   │   ├── HomePage.tsx                # media-type selector landing page
│   │   ├── ImagePage.tsx               # compress/decompress/embed/extract UI for image
│   │   ├── AudioPage.tsx
│   │   ├── VideoPage.tsx
│   │   └── JobHistoryPage.tsx          # optional, lists recent jobs
│   │
│   ├── components/
│   │   ├── upload/
│   │   │   ├── UploadDropzone.tsx
│   │   │   └── UploadProgress.tsx
│   │   ├── jobs/
│   │   │   ├── JobStatusBadge.tsx
│   │   │   └── JobProgressBar.tsx
│   │   ├── comparison/
│   │   │   ├── ImageCompareView.tsx    # side-by-side / slider before-after
│   │   │   ├── AudioCompareView.tsx    # A/B audio player
│   │   │   └── VideoCompareView.tsx    # A/B video player
│   │   ├── metrics/
│   │   │   ├── MetricsTable.tsx
│   │   │   └── MetricsChart.tsx        # recharts-based viz
│   │   ├── stego/
│   │   │   ├── MessageInput.tsx
│   │   │   ├── EncryptionToggle.tsx    # AES on/off + password field
│   │   │   └── CapacityIndicator.tsx
│   │   └── common/
│   │       ├── Button.tsx
│   │       ├── ErrorBanner.tsx
│   │       └── LoadingSpinner.tsx
│   │
│   ├── context/
│   │   └── JobContext.tsx              # optional: shares active job state across views
│   │
│   ├── styles/
│   │   └── index.css                   # Tailwind entry
│   │
│   └── lib/
│       └── formatters.ts               # bytes → human-readable, time formatting
│
├── index.html
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
└── package.json
```

**Rationale:**
- `api/` mirrors the backend's per-media router split, keeping the contract 1:1 and easy to trace.
- `components/comparison/` and `components/metrics/` are split out because §6 of the roadmap (M6) treats cross-media comparison as a shared concern — each media type gets its own compare component (since audio/video need players, image needs a slider/overlay) but they share `MetricsTable`/`MetricsChart`.
- `hooks/useJobPolling.ts` centralizes the polling logic referenced in R9 so every page uses one tested implementation instead of three copies.

---

## 7. API Specification (Final)

Base path: `/api/v1`. Content negotiation: JSON for control data, `multipart/form-data` for uploads, binary stream for downloads.

### Common conventions
- Success (processing): `{ "job_id": "uuid", "status": "pending" }` — `202 Accepted`
- Success (sync, e.g. health): `200 OK` with resource body
- Error: `{ "error": { "code": "CAPACITY_EXCEEDED", "message": "...", "details": {} } }` with appropriate 4xx/5xx
- All file-bearing requests are `multipart/form-data` with a `file` field; non-file params are additional form fields (not nested JSON, to keep multipart simple).

### 7.1 Health
- `GET /health` → `{ "status": "ok" }`

### 7.2 Image
- `POST /image/compress` — form: `file`, `algorithm` (`rle`|`huffman`) → `202` job
- `POST /image/decompress` — form: `job_id` (of a prior compress job) **or** `file` (raw compressed artifact), `algorithm` → `202` job
- `POST /image/embed` — form: `file`, `message`, `encrypt` (bool), `password` (optional) → `202` job
- `POST /image/extract` — form: `file`, `password` (optional) → `200` `{ "message": str, "encrypted": bool }` or `400` decrypt-failed
- `GET /image/{job_id}/compare` → `200` `{ metrics: { psnr, ssim, mse, compression_ratio, processing_time_ms, hidden_capacity_bits }, original_url, result_url }`

### 7.3 Audio
- `POST /audio/compress` — form: `file`, `target_bitrate_kbps` → `202` job
- `POST /audio/decompress` — form: `job_id` or `file` → `202` job
- `POST /audio/embed` — form: `file` (WAV only), `message`, `encrypt`, `password` → `202` job
- `POST /audio/extract` — form: `file`, `password` → `200` message or `400`
- `GET /audio/{job_id}/compare` → `200` `{ metrics: { compression_ratio, processing_time_ms, hidden_capacity_bits }, original_url, result_url }`

### 7.4 Video
- `POST /video/compress` — form: `file`, `crf` or `target_bitrate_kbps` → `202` job (async)
- `POST /video/embed` — form: `file`, `message`, `frame_count`, `encrypt`, `password` → `202` job (async); response/job notes output is a **lossless stego container**, distinct from a "compressed" artifact (per §4.3)
- `POST /video/extract` — form: `file`, `password` → `202` job (async) → polled result contains message
- `GET /video/{job_id}/compare` → `200` `{ metrics: { compression_ratio, processing_time_ms, hidden_capacity_bits }, original_url, result_url }`

### 7.5 Jobs
- `GET /jobs/{job_id}` → `{ job_id, media_type, operation, status, created_at, error? }`
- `GET /jobs/{job_id}/download` → binary stream of result file
- `DELETE /jobs/{job_id}` → `204`, deletes files + marks DB record deleted
- `GET /jobs?limit=20&offset=0` → paginated list (optional, supports JobHistoryPage)

---

## 8. Database Schema

SQLite (file-based, zero-ops, sufficient for this project's scale — escalate to Postgres only if multi-instance deployment is later required).

### Table: `jobs`
| Column | Type | Notes |
|---|---|---|
| `id` | TEXT (UUID) PK | |
| `media_type` | TEXT | `image`\|`audio`\|`video` |
| `operation` | TEXT | `compress`\|`decompress`\|`embed`\|`extract` |
| `status` | TEXT | `pending`\|`processing`\|`done`\|`error`\|`expired` |
| `original_filename` | TEXT | |
| `original_path` | TEXT | relative path under `storage/{job_id}/` |
| `result_path` | TEXT NULL | populated when done |
| `algorithm` | TEXT NULL | e.g. `rle`, `huffman`, `lsb`, `bitrate`, `transcode`, `frame_embed` |
| `encrypted` | BOOLEAN | whether AES was applied |
| `salt` | TEXT NULL | password-derived-key salt, **never the key/password itself** |
| `error_code` | TEXT NULL | |
| `error_message` | TEXT NULL | |
| `created_at` | DATETIME | |
| `updated_at` | DATETIME | |
| `expires_at` | DATETIME | `created_at` + TTL, used by `infra/cleanup.py` |

### Table: `metrics`
| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `job_id` | TEXT FK → jobs.id | |
| `metric_name` | TEXT | `psnr`\|`ssim`\|`mse`\|`compression_ratio`\|`processing_time_ms`\|`hidden_capacity_bits` |
| `metric_value` | REAL | |

One-row-per-metric (EAV-style) chosen over fixed columns because metric sets differ by media type (image has 6 possible metrics, audio/video have 3) — avoids a wide table full of NULLs and keeps `registry.py`'s dispatch logic trivially mappable to inserts.

### Indices
- `jobs(status, expires_at)` — for the cleanup sweep query.
- `metrics(job_id)` — for compare-view lookups.

No user/auth tables — out of scope per spec (no mention of accounts/auth anywhere in AGENTS.md or PROJECT_SPEC.md). If auth is added later, a `users` table + `jobs.user_id` FK is the natural extension point; not built now to avoid speculative scope.

---

## 9. Summary of Changes from Prior Draft

| Area | Prior Draft | Final |
|---|---|---|
| Job persistence | Implied in-memory/Redis | SQLite via `db/` module, explicit schema |
| Video stego + compression | Treated as one pipeline | Explicitly split into two non-chained artifacts to avoid re-encode data loss |
| Decompress contract | Vague ("upload compressed payload") | Defined as job-reference or re-upload, always compared against reconstructed output |
| Retention | Not addressed | 24h TTL + quota + scheduled cleanup, `infra/cleanup.py` |
| Frontend | Not designed | Full folder structure, mirrors backend per-media split |
| API error/response shape | Implied | Standardized envelope, documented |
| File serving | Implied static | Routed through `/jobs/{id}/download` for control |