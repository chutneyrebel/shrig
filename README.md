# Sprig WT v0.2.0 development (experimental)

A small, independently implemented, Shrub-inspired wavetable synthesizer module for [Schwung](https://schwung.dev/) on Ableton Move. This is not a port of Shrub and includes **no Shrub/Xfer firmware or proprietary wavetable assets**.

**Status:** ARM64 DSP and archive built locally; host-side DSP smoke tests passed. **Not tested on actual Move hardware.** Install at your own risk after backing up Move sets and learning Schwung recovery procedures.

## Synth

- 8-voice polyphony, second saw oscillator, detune, LFO wavetable movement, nonlinear drive, and velocity; round-robin oldest voice stealing
- 4 originally generated wavetable families (sine, saw, square/pulse, triangle), each with 4 morphable timbre frames
- Per-note band-limited tables, linear table interpolation, smooth morphing
- 2-pole zero-delay-feedback state-variable low-pass filter with resonance
- Attack, decay, sustain, release; bounded audio; no runtime heap allocations, locking, I/O, or subprocesses
- `state` parameter for round-trip patch storage; version 0.1 has integer controls

Move's eight performance knobs: **Wave**, **WT Position**, **Osc 2 Mix**, **Detune**, **Cutoff**, **Resonance**, **Motion Depth**, **Output**. Navigate to Oscillators, Filter + Color, Motion, Amp Envelope and Output for more controls. A custom web synth panel is included for Schwung Manager's Remote UI. The dedicated on-device graphical synthesizer face is not yet implemented.

## Build (Mac/Linux)

Requires Python 3, Clang, LLVM lld, `readelf`, `nm`, `gcc` (for the desktop tests). The build creates a standalone AArch64 `.so` that has **no glibc/libm dynamic dependencies** and does not need a cross sysroot.

```bash
python3 scripts/generate_tables.py
python3 tests/test_plugin.py
bash scripts/build.sh
python3 tests/check_package.py
```

Use the Actions workflow for a reproducible archive from GitHub.

The resulting archive is `dist/sprig-wt-module.tar.gz` containing `sprig-wt/module.json` and `sprig-wt/dsp.so`. The target directory is `/data/UserData/schwung/modules/sound_generators/sprig-wt`.

## Schwung Manager distribution

**Manager installs from a published module repository**, not necessarily by accepting an arbitrary local tarball upload. For Manager installation, publish this code as a GitHub repository, run its Actions workflow, attach the generated `sprig-wt-module.tar.gz` to a GitHub release, and create a `release.json` with the exact release download URL. Add `owner/repo` using the Manager's supported module repository workflow. Do not invent an unverified release URL.

For a first hardware test, there is also an optional manual SSH path in [docs/HARDWARE_TEST.md](docs/HARDWARE_TEST.md). The package layout is compatible with Schwung's sound-generator module convention, but **Manager installation has not yet been verified on your device**.

## Repository guidance

Use a **new dedicated repository** such as `chutneyrebel/sprig-wt`, with development branch `feature/shrub-inspired-synth`. Do not commit files into Schwung's upstream `main` or existing SchwungPocket project. The included workflow expects repository root. This local source ZIP is ready to place into a newly created repo.

## License and attribution

Original DSP and generated wavetable definitions in this prototype are independently authored for this experiment. License for this prototype: MIT, see LICENSE. The public Schwung plugin ABI and metadata conventions are interface references, not copied DSP algorithms. The proprietary Shrub firmware is intentionally omitted.

No connection to or endorsement by Ableton, Xfer Records, or the Shrub authors.

## v0.2.0 development status

- Source changes committed to `feature/shrub-inspired-synth`; **not released**.
- Additive synth controls and a remote browser interface; no proprietary Shrub assets.
- Existing installed v0.1.0 remains unchanged until a verified v0.2.0 release is published.
- GitHub Actions and new Move hardware compatibility require confirmation before installation.
