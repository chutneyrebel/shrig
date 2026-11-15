# Sprig WT

**Experimental dual-oscillator wavetable synthesizer for Ableton Move, integrated through Schwung.** Independently developed; not a port of Shrub. No proprietary Shrub wavetables or source code are included.

## Current status (15 November 2026)

**Phases 1–8 are merged into `main` and hardware-validated on Ableton Move.** Phase 8 completed **7/7 hardware checks** after improving the physical-display visibility of oscillator balance and voice activity. Phase 7.1 also passed its final main SYNTH animation retest. GitHub Actions passed for the Phase 8 branch before merge. **Phase 9 modulation-aware visuals are in development separately from `main`.**

The module descriptor still reports version `0.2.0`; development phases are not tagged public releases.

## What works

- Two independent wavetable oscillators with 108 selectable tables each (IDs 0–107), four interpolated frames per table, pitch-dependent band-limiting and independent position controls.
- Independent oscillator octave, detune, stereo pan, level, phase-warp type and amount. Warp modes: Off, Sync, Bend+, Bend−, PWM, Asymmetry, Mirror and Quantize.
- Eight-voice, 44.1 kHz stereo C11 DSP engine with independent oscillator amplitude envelopes (opt-in), OSC MIX balance, and legacy-compatible global amplitude envelope.
- Eight selectable shared-filter modes: **LP12, HP12, BP12, Notch, Peak, Allpass, LP24 and HP24**. The default LP12 retains the historical filter behavior.
- Filter cutoff, resonance, drive, triggered filter envelope and LFO-to-filter modulation.
- Four hardware-verified native Schwung canvas faces: **MAIN** (combined oscillators), **OSC 1**, **OSC 2**, and **FILTER** (illustrative response curve). The MAIN face includes oscillator balance, stereo pan position, eight voice-activity slots and voice-gated waveform motion.
- Dual-LFO, 24-route modulation matrix with named destinations; hardware-validated modulation routing and preset persistence. The redundant AMP page was removed; independent **OSC1 Env** and **OSC2 Env** pages remain.
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
| Phase 7: dual-LFO modulation matrix | **10 pass, 0 fail** |
| Phase 7.1: named matrix destinations and enhanced animations | **Final SYNTH retest passed**; earlier round 9/10, fixed before merge |
| Phase 8: performance HUD and visual legibility | **7 pass, 0 fail** |

Phase 3 checks covered physical encoder selection, each filter's audible behavior, FILTER FACE response, envelope/LFO modulation, old and new presets, and stability with no reported crashes, clicks, excessive CPU usage or stuck notes.

- [Phase 7 merged PR #8](https://github.com/chutneyrebel/shrig/pull/8)
- [Phase 7.1 merged PR #9](https://github.com/chutneyrebel/shrig/pull/9)
- [Phase 8 merged PR #10](https://github.com/chutneyrebel/shrig/pull/10)
- [Phase 8 passing CI run](https://github.com/chutneyrebel/shrig/actions/runs/43664947013)
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

- **Completed and hardware-validated:** Phases 1–3, dual oscillators, independent envelopes and eight-mode filter.
- **Completed and hardware-validated:** Phase 7, dual-LFO 24-route matrix; Phase 7.1, destination names and animated faces; Phase 8, performance HUD.
- **In development:** Phase 9, modulation-aware visual feedback. No Phase 9 changes are shipped on `main` yet.
- **Future:** Advanced preset management and optional native wavetable category navigation.

The Schwung module metadata has a strict **8192-byte** size budget. Keep `src/module.json` and generated `src/ui_metadata.h` synchronized and preserve the legacy parameter ABI/defaults when extending controls.

## License and attribution

[MIT license](LICENSE). Not affiliated with or endorsed by Ableton, Schwung developers, Xfer Records or the creators of Shrub.
