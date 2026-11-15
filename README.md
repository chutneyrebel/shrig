# Sprig WT

**Experimental dual-oscillator wavetable synthesizer for Ableton Move, integrated through Schwung.** Independently developed; not a port of Shrub. No proprietary Shrub wavetables or source code are included.

## Current status (15 November 2026)

**Phases 1, 2 and 3 are merged into `main` and hardware-validated on Ableton Move.** Phase 3 passed all 12 hardware checks with zero failures or skips. Its corresponding GitHub Actions workflow passed desktop audio/ABI tests, native canvas tests, ARM64 cross-compilation and package verification. **Phase 4 modulation-matrix development is separate from the validated `main` baseline.**

The module descriptor currently reports version `0.2.0`; development milestones should not be confused with tagged public releases.

## What works

- Two independent wavetable oscillators with 108 selectable tables each (IDs 0–107), four interpolated frames per table, pitch-dependent band-limiting and independent position controls.
- Independent oscillator octave, detune, stereo pan, level, phase-warp type and amount. Warp modes: Off, Sync, Bend+, Bend−, PWM, Asymmetry, Mirror and Quantize.
- Eight-voice, 44.1 kHz stereo C11 DSP engine with independent oscillator amplitude envelopes (opt-in), OSC MIX balance, and legacy-compatible global amplitude envelope.
- Eight selectable shared-filter modes: **LP12, HP12, BP12, Notch, Peak, Allpass, LP24 and HP24**. The default LP12 retains the historical filter behavior.
- Filter cutoff, resonance, drive, triggered filter envelope and LFO-to-filter modulation.
- Four hardware-verified native Schwung canvas faces: **MAIN** (combined oscillators), **OSC 1**, **OSC 2**, and **FILTER** (illustrative response curve). Each shows contextual meter labels.
- Additional native encoder levels for **OSC MIX**, **OSC1 Env** and **OSC2 Env**.
- Preset save/reload and compatibility with existing presets, confirmed in Phase 2 and Phase 3 hardware testing.
- Categorized wavetable browsing in the remote HTML interface. A native hardware category picker is not implemented.

The waveform and filter displays are lightweight visual approximations, not measured FFTs or sample-accurate oscilloscopes. The filter is global in its parameter settings and operates on the combined oscillator signal per voice.

## Hardware validation

| Milestone | Acceptance |
| --- | --- |
| Phase 1: oscillator and native face foundation | Hardware tested; original report: 15 pass, 0 fail, 1 skip |
| Phase 2: independent oscillator ADSRs and OSC MIX | **29 pass, 0 fail, 0 skip** |
| Phase 3: eight-mode filter engine | **12 pass, 0 fail, 0 skip** |

Phase 3 checks covered physical encoder selection, each filter's audible behavior, FILTER FACE response, envelope/LFO modulation, old and new presets, and stability with no reported crashes, clicks, excessive CPU usage or stuck notes.

- [Phase 3 merged PR #4](https://github.com/chutneyrebel/shrig/pull/4)
- [Phase 3 passing CI run](https://github.com/chutneyrebel/shrig/actions/runs/43654970584)
- [All Actions builds](https://github.com/chutneyrebel/shrig/actions)

## Build and install

Requirements: Python 3, Clang, LLVM lld, GNU binutils, GCC and Node.js.

```bash
python3 scripts/generate_tables.py
python3 tests/test_plugin.py
node tests/test_canvas.cjs
bash scripts/build.sh
python3 tests/check_package.py
```

The build produces `dist/sprig-wt-module.tar.gz`. Successful GitHub Actions runs publish `sprig-wt-targz-download` as a ZIP containing the `.tar.gz` package. Extract the ZIP once before using the established Schwung installation process.

Read [hardware test instructions](docs/HARDWARE_TEST.md) and back up your Move sets and current module before replacing an installation. Expected module path: `/data/UserData/schwung/modules/sound_generators/sprig-wt`. A green CI run is not a substitute for on-device testing of new branches.

## Development roadmap

- **Completed:** Phase 1, dual-oscillator architecture and hardware faces.
- **Completed:** Phase 2, independent oscillator envelopes and OSC MIX.
- **Completed:** Phase 3, eight-mode global filter engine.
- **Next:** Phase 4, a backward-compatible modulation matrix, motion routing and hardware/CPU regression tests.
- **Future:** Advanced preset management, richer motion visualization, optional native wavetable category navigation and further modulation destinations. These are plans, not shipped features.

The Schwung module metadata has a strict **8192-byte** size budget. Keep `src/module.json` and generated `src/ui_metadata.h` synchronized and preserve the legacy parameter ABI/defaults when extending controls.

## License and attribution

[MIT license](LICENSE). Not affiliated with or endorsed by Ableton, Schwung developers, Xfer Records or the creators of Shrub.
