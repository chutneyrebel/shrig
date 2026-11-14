# Shrig: Sprig WT prototype

An independently authored, experimental Shrub-inspired wavetable synth for [Schwung](https://schwung.dev/) on Ableton Move.

**Status:** v0.1.0 prototype is locally built and desktop-tested, but **not yet verified on Ableton Move hardware**. This repository is being populated on `feature/shrub-inspired-synth`. The CI workflow will fail until the complete source package is committed.

## Design
- Native Schwung sound generator using plugin API v2, AArch64 DSP library `dsp.so`
- Eight voice wavetable synth, independent wavetable assets
- Filter, ADSR, velocity, eight hardware control assignments
- No Shrub firmware or extracted proprietary sound assets

## Source import
The full source is available in the previously supplied `sprig-wt-v0.1.0-source.zip`. Extract it and upload the **contents of the inner `sprig-wt-v0.1.0/` directory**, preserving `.github/workflows/build.yml`, `scripts/`, `src/`, `tests/`, and `docs/`, to this feature branch. Do not upload pre-built `build/` or `dist/` folders.

After uploading, GitHub Actions builds a Schwung sound-generator tarball. A green CI build is not proof of on-device compatibility. Verify on a backed-up Move test set first.

## Safety
Do not install until test and recovery procedures are reviewed. Never modify upstream Schwung or stock Ableton software directly.

Not affiliated with Ableton, Xfer Records, or Shrub developers.
