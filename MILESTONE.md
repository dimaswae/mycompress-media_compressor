# MILESTONES.md — Risk-Prioritized Delivery Plan

Based on the granular task breakdown in `TASKS.md`. Sequencing logic: **resolve the highest-uncertainty technical risks first**, and **ship a thin but complete vertical slice (one media type, full pipeline) as the MVP before breadth-expanding** to audio/video/security/polish.

---

## Sequencing Philosophy

Two competing pulls, resolved as follows:
- **Risk-first** would say: tackle Huffman, video remux, and FFmpeg safety before anything else, since they're the most likely to blow up the schedule.
- **MVP-first** would say: ship the thinnest demonstrable path through the system as fast as possible.

Resolution: do both, in this order —
1. Stand up the skeleton (can't build anything without it).
2. Prove the **riskiest reusable primitive** early (FFmpeg subprocess safety + image Huffman) because every later milestone depends on these patterns being right — discovering they're broken in Milestone 5 is far more expensive than discovering it in Milestone 2.
3. Drive straight to an **Image-only MVP** (compress + embed + extract + compare), since image is the lowest-risk full vertical slice and validates the entire architecture end-to-end (DB, storage, job model, routes, frontend) without yet touching the two genuinely hard problems (video remux, async jobs).
4. Only after the MVP works, expand to Audio (low incremental risk) and Video (highest remaining risk), then Security and polish.

This means video's two hardest tasks (lossless remux, async jobs) are deliberately tackled in Milestone 5 — late enough that the rest of the system is proven stable, early enough that there's still schedule room to recover if they take longer than estimated.

---

## Milestone 0 — Foundation
**Tasks:** `SET-01` through `SET-10`
**Risk level:** 🟢 Low
**Goal:** Both apps run, CI is green, Docker works.

No technical unknowns here — purely setup. Fast to execute, unblocks everything else.

**Exit criteria:** `docker compose up` serves both apps; CI passes on an empty test suite.

---

## Milestone 1 — Highest-Risk Primitives (De-risking Spike)
**Tasks:** `INF-09` (FFmpeg runner + timeout), `TEST-04` (injection safety test), `IMG-05`–`IMG-07` (Huffman encode/decode/edge cases), `DB-01`–`DB-07` (persistence layer), `INF-01`–`INF-06`, `INF-10` (validation, storage, quota), `API-01`–`API-03` (error envelope + middleware)
**Risk level:** 🔴 High (by design — this is where the risk lives)
**Goal:** Prove the two riskiest reusable primitives work *before* building features on top of them, and put the storage/DB/error-handling foundation in place that every module depends on.

**Why these specifically, why now:**
- `INF-09`/`TEST-04` (FFmpeg subprocess wrapper) is used by audio compression, video compression, *and* video embedding — a flaw here propagates into three later milestones. Validating it against a trivial command (`ffmpeg -version`) plus an injection-attempt test is cheap insurance.
- `IMG-05`–`07` (Huffman) is the single task cluster most likely to harbor subtle correctness bugs (tree-building, canonical codes, empty/single-symbol edge cases) per the earlier architecture risk review. Doing it now, isolated, with full unit test coverage, means it's a solved problem by the time the MVP needs it.
- `DB-*`/`INF-01–06,10`/`API-01–03` are pure infrastructure with no business logic — every later milestone needs them, so building them once now avoids rework.

**Exit criteria:** FFmpeg wrapper passes its timeout + injection tests; Huffman round-trips correctly on normal input and both edge cases; job/metric DB tables exist and are read/write tested; file validation rejects bad uploads; error responses follow the standard envelope.

---

## Milestone 2 — MVP: Image Module End-to-End ⭐
**Tasks:** `IMG-01`–`IMG-04`, `IMG-08`–`IMG-27`, `API-04`–`API-10`, `FE-01`–`FE-03`, `FE-07`–`FE-18`, `FE-21`, `FE-24`, `FE-26`
**Risk level:** 🟡 Medium (RLE/LSB are low-risk; this milestone's job is mainly *integration*, not new algorithmic risk)
**Goal:** A user can upload a PNG/JPG, compress it (RLE or Huffman), decompress it, embed/extract a hidden message, and view a before/after comparison with PSNR/SSIM/MSE/ratio/time metrics — fully working, in the browser, end to end.

**This is the MVP delivery point.** It exercises every architectural layer (routes → services → core → infra → DB) and the full frontend stack (upload → job polling → compare view → metrics) using the one media type with no outstanding technical risk. If something is wrong with the *architecture* (not just one codec), it surfaces here, while it's still cheap to fix, rather than after three media types have been built on top of a flawed pattern.

**Exit criteria:** Live demo — upload sample PNG, run compress+decompress, run embed+extract, view comparison with all six metrics. All `IMG-*` unit/integration tests green. Frontend `ImagePage` fully functional against the real backend (not mocked).

**🎯 MVP ships here.** Everything after this milestone is breadth (more media types) or depth (security, polish, hardening) — the system is already demonstrably "working" per AGENTS.md's Definition of Done, scoped to one media type.

---

## Milestone 3 — Audio Module
**Tasks:** `AUD-01`–`AUD-19`, `FE-04`, `FE-19`, `FE-22`
**Risk level:** 🟢 Low–Medium
**Goal:** Extend the proven image pattern to audio (WAV/MP3 compress, WAV-only LSB embed/extract).

**Why low risk:** Audio reuses the same `StegoCodec`/`CompressionCodec` ABCs, the same job/metrics pattern, and the now-validated FFmpeg wrapper from Milestone 1. The only genuinely new logic is bitrate-reduction compression and WAV-sample LSB — both simpler than their image counterparts (no Huffman-equivalent complexity, no pixel-channel reasoning).

**Watch item carried over from architecture review:** confirm explicitly that MP3 is correctly rejected for embed (spec is WAV-only) — `AUD-07` exists specifically to prevent silent scope creep here.

**Exit criteria:** Live demo — upload WAV, compress, embed/extract message, compare view with ratio/time/capacity metrics. MP3 upload to `/embed` cleanly rejected with a clear error. All `AUD-*` tests green.

---

## Milestone 4 — Video Module (Highest Remaining Risk)
**Tasks:** `VID-01`–`VID-18`, `FE-05`, `FE-20`, `FE-23`
**Risk level:** 🔴 High
**Goal:** FFmpeg-based transcoding, frame-based steganography with lossless remux, async job lifecycle.

**Why this is last among the feature modules, not first:** Two distinct hard problems live here — (a) frame extraction + lossless remux must be pixel-exact or embedded messages get destroyed, and (b) video is the only module that *requires* the async/background-task job pattern, since processing can't reliably finish inside a single request. Both are isolated, well-understood risks by this point (FFmpeg safety was proven in Milestone 1; the job-status/polling pattern was already built and tested for image/audio jobs, just running synchronously there). Tackling video last means the team is applying a known-good async pattern to one new hard problem (remux correctness) rather than learning both at once.

**Sequencing within the milestone:** do `VID-03`/`VID-04` (frame extraction + lossless remux round-trip) as an isolated spike *before* wiring in LSB embedding (`VID-06`) — if pixel-exact remux doesn't hold up, that's a design-level problem worth knowing immediately, not after embed/extract/metrics/routes are all built on top of it.

**Exit criteria:** Live demo — upload short MP4, compress (async, polls to done), embed message (async, lossless output), extract message, compare view. `TEST-03` (full async lifecycle integration test) green. Documented actual processing time vs. the 30s NFR (`TEST-05`), with realistic limits noted rather than the NFR being silently violated.

---

## Milestone 5 — Security Layer (Cross-Cutting)
**Tasks:** `SEC-01`–`SEC-09`, `FE-14` (already built in M2, just exercised against real encryption now)
**Risk level:** 🟡 Medium (correctness risk is low — AES-GCM via `cryptography` is a solved library problem — but the *process* risk, accidentally logging/persisting a password, is real)
**Goal:** Wire optional AES encryption into all three media types' embed/extract flows.

**Why after all three media modules, not interleaved:** Per the architecture doc, encryption is a hook each service calls before/after the stego step — building it once, after all three `embed()`/`extract()` functions exist with stable signatures, avoids touching the same code three separate times mid-development. This is the one place where "optional, do last" from PROJECT_SPEC.md aligns naturally with "lowest marginal risk, do last."

**Exit criteria:** For each media type — encrypt-then-embed, extract-then-decrypt round-trips exactly; wrong password fails cleanly with `400`, never garbage output. `SEC-09` code-review checklist confirms no password/key ever appears in logs or the database.

---

## Milestone 6 — Hardening, Cross-Media Polish, and Delivery
**Tasks:** `FE-09`–`FE-13`, `FE-15`–`FE-17`, `FE-25`, `FE-27`, `TEST-01`–`TEST-07`, `DOC-01`–`DOC-05`
**Risk level:** 🟢 Low (mostly known work, no remaining technical unknowns)
**Goal:** Cross-media comparison/metrics polish, full test suite, documentation, and deliverables per AGENTS.md's Definition of Done.

**Exit criteria:** All integration tests green; quota/cleanup/injection tests green; OpenAPI docs match the architecture spec; README files let a new developer run the project from scratch; technical report and demo video completed.

---

## Milestone Timeline Summary

| Milestone | Focus | Risk | Ships MVP? |
|---|---|---|---|
| M0 | Foundation/scaffolding | 🟢 Low | No |
| M1 | De-risk FFmpeg + Huffman + core infra | 🔴 High (deliberately front-loaded) | No |
| **M2** | **Image module, full stack** | 🟡 Medium | **✅ Yes — MVP** |
| M3 | Audio module | 🟢 Low–Medium | No (extends MVP) |
| M4 | Video module | 🔴 High | No (extends MVP) |
| M5 | Security (AES) | 🟡 Medium | No (extends MVP) |
| M6 | Hardening, docs, delivery | 🟢 Low | Final delivery |

---

## Why This Order Beats the Alternatives

- **Risk-first-only** (tackle video before image) would delay any working demo until the hardest problem is solved — bad for stakeholder visibility and bad for catching architecture-level mistakes early, since video's complexity would mask whether the *foundation* (routing, DB, job model) is sound.
- **Breadth-first-only** (image+audio+video skeletons all at once, polish later) would mean discovering the Huffman or FFmpeg-safety problems *after* three modules already depend on the broken pattern — much more expensive to fix.
- **This plan** isolates the two specific high-risk primitives (M1), proves the whole architecture on the lowest-risk full vertical slice (M2 = MVP), then expands breadth in risk order (audio before video) and pushes genuinely optional/low-marginal-risk work (security, polish) to the end — giving the earliest possible working demo while still front-loading the things most likely to derail the schedule.