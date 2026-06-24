# ROADMAP_MVP.md — Fastest-Path MVP Delivery Plan

Source documents reviewed: `AGENTS.md`, `PROJECT_SPEC.md`, `ARCHITECTURE.md`, `BACKEND_ARCHITECTURE.md`, `TASKS.md`, `MILESTONES.md`. 

## Guiding Principle

The fastest defensible demo is **one media type, one compression algorithm, one stego technique, synchronous processing, no auth, no encryption, no async jobs** — i.e., the smallest slice that still touches every required capability from AGENTS.md (compress, decompress, hide, extract, compare, metrics) for at least one format. Everything else (audio, video, second algorithm, AES, job queue, polish) is explicitly deferred past the first working demo and layered on only after that demo exists.

This plan deliberately cuts deeper than `MILESTONES.md` for Phase 1 — even within the Image module, it trims to the single fastest path (PNG only, RLE only, synchronous) before expanding to the full image feature set in Phase 2.

---

## Phase 1 — Bare-Metal Image Demo (Speed Priority)

### Goals
Get *something real* working end-to-end — upload → compress → decompress → embed → extract → compare — for the single lowest-risk format and algorithm combination, with zero infrastructure beyond what's strictly required to run.

### Features
- PNG only (skip JPG — avoids the lossy-decode-boundary decision entirely for now)
- RLE compression/decompression only (skip Huffman — it's the riskiest algorithm; defer until the easy path is proven)
- LSB steganography embed/extract (no AES, no password)
- Metrics: compression ratio, processing time, hidden capacity, PSNR/SSIM/MSE
- Synchronous processing (no job queue, no `BackgroundTasks`, no polling) — request returns the result directly
- In-memory or filesystem-only storage (no database, no job records, no TTL/cleanup)
- Minimal frontend: one page, file input, two buttons (Compress, Embed), result + metrics shown inline — no routing, no comparison slider, no styling polish

### Deliverables
- FastAPI backend with 4 endpoints: `POST /compress`, `POST /decompress`, `POST /embed`, `POST /extract` (synchronous, return file + metrics directly, no job_id)
- `core/compression/image_rle.py`, `core/steganography/image_lsb.py`, `core/metrics/` (reused as-is from architecture design)
- One-page React app (no router, no component library structure yet) hitting those 4 endpoints
- Sample PNG fixture committed
- A short README describing how to run it

### Success Criteria
- A person can open the page, upload a PNG, click Compress, see a smaller file download with a ratio number shown.
- They can click Embed, type a message, get back a stego PNG.
- They can upload that stego PNG and click Extract, and get back the exact original message.
- PSNR/SSIM/MSE are displayed and are sane (e.g., SSIM ≈ 1.0 for compress round-trip).
- No database, no job system, no auth — and that's fine, because nothing in AGENTS.md's Definition of Done is violated yet (this phase isn't claiming to be "done," just demoable).

**Risk note:** This phase intentionally avoids the two highest-risk items identified earlier (Huffman correctness, FFmpeg subprocess safety) by not touching them at all yet. Risk is minimized by *scope exclusion*, not by careful engineering — that's the point of Phase 1.

---

## Phase 2 — Complete the Image Module (Breadth Within One Media Type)

### Goals
Round out the Image module to everything PROJECT_SPEC.md actually requires for images, and add the minimum architecture needed to make the system trustworthy (not just demoable) — without yet touching audio, video, or security.

### Features
- Add JPG support (resolve the decode-boundary decision from `FINAL_ARCHITECTURE.md` §4.2: operate on decoded pixel buffer, document it)
- Add Huffman coding compression/decompression, with explicit edge-case handling (empty input, single unique byte) — the one deferred high-risk item from Phase 1, now tackled deliberately and in isolation
- Add capacity-exceeded validation before embed (no more silent corruption on oversized messages)
- Introduce the job/DB model (SQLite, `jobs` + `metrics` tables) — still synchronous, but now persisted and pollable, replacing Phase 1's fire-and-forget responses
- Proper error envelope + middleware (consistent `{error: {code, message}}` shape)
- Frontend: real `compare` view (before/after side-by-side + metrics table), still single-page but visually organized

### Deliverables
- `core/compression/image_huffman.py` with full round-trip + edge-case unit tests
- `db/` module (SQLAlchemy models, Alembic migration) wired into image endpoints
- `GET /api/v1/image/{job_id}/compare` endpoint
- Updated frontend with a proper compare/metrics view
- Full `IMG-*` test suite passing (per `TASKS.md`)

### Success Criteria
- Both PNG and JPG can be compressed with either RLE or Huffman, and decompressed back losslessly (PNG exactly; JPG losslessly relative to its decoded pixels, as documented).
- Huffman correctly handles an empty file and a single-unique-byte-value file without crashing.
- An oversized embed message is rejected with a clear error before any file is touched.
- Every image job is now backed by a DB record retrievable via `GET /jobs/{id}`.
- This phase satisfies AGENTS.md's Definition of Done **for the Image module specifically**: code works, tests pass, API documented, UI integrated, README updated.

**Risk note:** Huffman — the deferred risk from Phase 1 — is now tackled in isolation, after the rest of the pipeline is proven, exactly as recommended in `MILESTONES.md`'s Milestone 1 rationale, just sequenced after a working demo rather than before it (since this plan optimizes for "demo exists ASAP" over "risk resolved ASAP").

---

## Phase 3 — Audio Module (Lowest-Risk Expansion)

### Goals
Extend the now-proven architecture pattern to a second media type, validating that the design generalizes — while still deferring the genuinely hard problem (video) and the optional one (security).

### Features
- WAV and MP3 compression (bitrate reduction via FFmpeg) — first real use of `infra/ffmpeg_runner.py`, so this is also where FFmpeg subprocess safety gets validated for the first time, in the lowest-risk context (audio, not video)
- WAV-only LSB steganography embed/extract (MP3 explicitly rejected for embed, per spec)
- Metrics: compression ratio, processing time, hidden capacity (no audio-specific fidelity metric, per the architecture decision — flagged, not silently invented)
- Frontend: Audio tab/page reusing the same upload → job-poll → compare pattern established in Phase 2, now with an A/B audio player

### Deliverables
- `core/compression/audio_bitrate.py`, `core/steganography/audio_lsb.py`
- `infra/ffmpeg_runner.py` with timeout handling and an injection-safety test (`TEST-04`) — first production use of FFmpeg in the system
- Audio routes + service layer mirroring the image pattern
- Audio sample fixtures (short WAV, short MP3)
- Frontend `AudioPage` with A/B playback

### Success Criteria
- A WAV file can be compressed (smaller output, measurable ratio) and round-tripped through embed/extract with an exact message match.
- An MP3 file can be compressed but cleanly rejected (with a clear error, not a crash) if a user attempts to embed into it.
- The FFmpeg wrapper survives the injection-safety test and a forced-timeout test before this phase is considered done.
- Audio module independently satisfies AGENTS.md's Definition of Done.

**Risk note:** This is the first point where FFmpeg-as-subprocess risk is actually exercised in production code (not just unit-tested in isolation) — but it's exercised on audio, where a bug has low blast radius (a failed compress, not a corrupted multi-minute video job), before video makes the same risk much more expensive to debug.

---

## Phase 4 — Video Module + Security + Hardening (Remaining Risk & Polish)

### Goals
Close out the remaining spec requirements — video (the highest-risk module) and AES encryption (the lowest-priority, spec-optional feature) — then harden and document for final delivery.

### Features
- FFmpeg-based video transcoding (compression)
- Frame-based LSB steganography with **lossless remux** as a separate artifact from compression (per the architecture decision resolving the re-encode-destroys-stego risk)
- Async job lifecycle (`BackgroundTasks`) — introduced here specifically because video is the only module that actually requires it; image/audio remained synchronous-but-DB-backed through Phase 3
- Optional AES-GCM encryption hook wired into all three media types' embed/extract flows (image, audio, video)
- Storage retention (TTL + cleanup sweep), quota check, CORS finalization
- Full responsive frontend pass, job history page, OpenAPI doc review
- Technical report, README finalization, demo video recording

### Deliverables
- `core/compression/video_transcode.py`, `core/steganography/video_frame_embed.py` (extract → lossless remux → embed → extract, isolated and round-trip tested *before* wiring into the service layer)
- Async video routes/services with job polling on the frontend (visible "processing" state)
- `core/security/aes_cipher.py` wired into image/audio/video services
- `infra/cleanup.py` TTL sweep, quota check
- Full `TEST-*` suite (integration, security, load-sanity, quota, cleanup)
- `docs/` technical report + presentation video

### Success Criteria
- A short MP4 can be compressed (smaller, valid output) and separately embedded with a message that survives lossless remux and extracts exactly.
- Video jobs return immediately (202) and are pollable to completion — no request hangs waiting on FFmpeg.
- AES encryption round-trips correctly on all three media types; wrong password fails cleanly, never silently.
- All `AGENTS.md` Definition-of-Done criteria are met project-wide: code works, tests pass, API documented, UI integrated, README updated — for every module, not just image.
- Final deliverables (source, technical report, presentation video) are complete per `PROJECT_SPEC.md`.

**Risk note:** Video's two hard problems (lossless remux, async jobs) are tackled last, but by this point the team has already validated FFmpeg safety (Phase 3) and built/tested the comparison-and-metrics UI pattern twice (Phases 2–3) — so Phase 4 is applying proven patterns to one genuinely new technical problem, not learning the whole architecture under risk pressure.

---

## Summary Table

| Phase | Headline Deliverable | New Risk Introduced | Demo-able? |
|---|---|---|---|
| **1** | PNG compress/embed/extract, synchronous, no DB | None (deliberately scoped out) | ✅ Yes — fastest possible |
| **2** | Full Image module (JPG, Huffman, DB-backed jobs, compare view) | Huffman correctness (isolated, tested) | ✅ Yes — image "done" |
| **3** | Audio module (WAV/MP3 compress, WAV stego) | First production FFmpeg use (low blast radius) | ✅ Yes — image + audio "done" |
| **4** | Video module + AES security + hardening + delivery | Lossless remux + async jobs (highest risk, tackled last) | ✅ Yes — full project "done" |

**Why this beats jumping straight to the full architecture:** Phase 1 produces a clickable demo before the database even exists. Every later phase adds exactly one new axis of complexity (DB/Huffman → FFmpeg/audio → async/video/security) rather than building all axes simultaneously, so if schedule pressure hits, the project can stop after any phase and still have a working, demoable system that's a strict subset of the final one — never a half-built mess of four incomplete media types at once.