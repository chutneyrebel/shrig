# Synth_esis development roadmap: Phases 10 and 11

Status: Phase 10A automated CI and Move hardware validation passed. Integration branch: `development-phase10-11`. Do not merge to `main` without explicit approval.

## Integration strategy

- Continue Phases 10 and 11 on this **single integration branch**, branched from the Phase 10A refactor. PR #32 remains an independent review record and is **not merged**.
- Keep small, reviewable commits and a passing GitHub Actions run at each checkpoint.
- Preserve IDs 0–107, historical presets, Schwung API v2, 8-encoder control contracts, 128x64 canvas performance and metadata size.
- New shaping defaults must be strictly bypassed for existing presets. Do not repurpose legacy `spectral_shape`, `shape`, or `legacy_shape` parameters: they already have historical meanings.
- Keep new features independently authored; Vital GPLv3 source is reference material only and must not be copied into this MIT repository.
- Only merge the integration branch to `main` after Phase 11 is stable, CI is green, hardware tests pass, and the owner explicitly approves.

## Phase 10: advanced wavetable shaping and responsive visuals

| Stage | Deliverable | Gate |
| --- | --- | --- |
| 10A | Unified legacy and expanded wavetable lookup boundary, no audible change | **Passed**: CI and user Move test |
| 10B-1 | Offline spectral transform prototypes: harmonic tilt, spectral filtering; deterministic generated data, no runtime allocation | Numeric spectral regression tests and table-size budget |
| 10B-2 | Per-oscillator shape engine, explicit neutral/bypass defaults, safe interpolation | Legacy preset audio regression and ARM64 CPU budget |
| 10C | Bounded DSP-derived waveform/spectrum snapshot for Move canvas; rate-limited UI reads | Canvas/host contract and hardware animation test |
| 10D | Harmonic shift, spectral fold and phase distortion; avoid unsafe high-frequency content | Aliasing, headroom and polyphony tests |
| 10E | Two independent OSC SHAPE pages, 8 encoders each, modulation routing and smoothing | Full page-order/encoder/preset regression |
| 10F | Advanced hybrid editor data contract and offline wavetable import/export design | Round-trip tests and safe invalid-file handling |

**Design invariant:** wavetable preprocessing is offline/non-audio-thread. Playback remains bounded lookup and interpolation; avoid FFTs and allocations inside `render`. New spectral preview must represent the actual transformed tables, not a separate visual approximation.

## Phase 11: hybrid editor and stability consolidation

| Stage | Deliverable | Gate |
| --- | --- | --- |
| 11A | Versioned wavetable/shape interchange schema, bank IDs and validation | Compatibility, corruption and round-trip tests |
| 11B | Schwung web editor: harmonic spectrum, draw/import controls, live preview | Cross-browser and host integration |
| 11C | Optional dedicated editor interface, export/import with no dependency on desktop at performance time | Repeatable export and Move install |
| 11D | Hardware performance tuning, UI/audio stress tests, migration and rollback support | 8-voice sustained load, no dropouts |
| 11E | Consolidated Phase 10+11 release candidate on integration branch | CI, hardware acceptance, explicit merge approval |

## Next immediate work

1. Implement 10B-1 as a standalone, independently authored offline spectral prototype and unit tests.
2. Measure generated bank footprint before introducing more shapes.
3. Integrate neutral-by-default oscillator shaping only after audio equivalence tests are in place.
4. Start Phase 10C DSP-derived visuals alongside the sound engine, not as an afterthought.

## Merge policy

Do not automatically merge PR #32 or the integration branch. The final consolidation PR will target `main` from `development-phase10-11` only after Phase 11 stability is confirmed.
