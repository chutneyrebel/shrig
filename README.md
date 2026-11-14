# Sprig WT

**Experimental wavetable synthesizer for Ableton Move via Schwung.** Independently developed and inspired by exploratory wavetable instruments such as Shrub. Not a port of Shrub, and no proprietary Shrub wavetables or code are included.

> **Development status (14 November 2026):** Work in progress on `main`. The latest dual-oscillator changes are **not hardware-verified**. Do not install a failing or unverified CI artifact. The project is unreleased and development proceeds directly on `main`.

## Vision

Sprig WT aims to make wavetable exploration immediate: one collection of 52 original waveforms (four classic and 48 spectral), independent oscillators, hands-on warp transformations, motion, and clear visual feedback. No separate Legacy/Expanded bank selection is needed in the intended interface.

## Implemented in the development source

- Freestanding C11 audio engine for 44.1 kHz stereo output, eight voices and band-limited wavetable playback.
- Unified wavetable selection **0–51** with four interpolated frames per table.
- Independent OSC 1 and OSC 2 wavetable, position, warp mode, warp amount, detune, pan and volume **parameters**. Note: the first dual-oscillator DSP implementation is in progress; stereo pan is now implemented in the development DSP and awaits Move hardware verification.
- Eight initial phase-warp modes: **Off, Sync, Bend+, Bend−, PWM, Asymmetry, Mirror, Quantize**. These are independently authored transformations, not exact reproductions of Shrub's algorithms.
- ADSR amplitude envelope, filter envelope, LFO motion, drive and resonant low-pass filtering.
- A single native Synth Face canvas exists. It currently approximates the selected waveform rather than reading the exact DSP output, so visuals may differ from sound.
- Some older compatibility parameters remain in the metadata. They are not intended to appear in the final simplified performance interface.

## Target four-page layout

| Page | Graph | Controls |
| --- | --- | --- |
| **MAIN** | Combined OSC 1 + OSC 2 waveform | Motion Rate, Motion Depth, LFO Filter Depth |
| **OSC 1** | OSC 1 waveform | Wavetable, Position, Warp Type, Warp Amount, Detune, Pan, Volume |
| **OSC 2** | OSC 2 waveform | Wavetable, Position, Warp Type, Warp Amount, Detune, Pan, Volume |
| **FILTER** | Combined waveform after filtering | Cutoff, Resonance, Filter Type |

**Filter routing decision:** one **master filter** applied to the combined oscillators, not separate filters per oscillator. Planned modes include LP, HP, BP and comb, subject to DSP and CPU testing. The current DSP only implements a resonant low-pass filter.

The on-screen **C / M / E / O** indicators should show relevant modulation on each page. Their final definitions and Schwung page compatibility are still being tested. Four independent native canvas pages are **not yet implemented or verified**.

## Build and test

Requirements: Python 3, Clang, LLVM lld, GNU binutils, GCC and Node.js for the canvas tests.

```bash
python3 scripts/generate_tables.py
python3 tests/test_plugin.py
node tests/test_canvas.cjs
bash scripts/build.sh
python3 tests/check_package.py
```

The build generates `dist/sprig-wt-module.tar.gz`. GitHub Actions publishes it as the **sprig-wt-targz-download** artifact, which GitHub wraps in a ZIP. Extract the ZIP once to obtain the actual `.tar.gz`.

[View CI builds](https://github.com/chutneyrebel/shrig/actions)

Only use a build whose full workflow is marked **Success**. CI success verifies desktop tests, packaging and cross-compilation, **not** behavior on the actual Move.

## Installation and safety

See [hardware test instructions](docs/HARDWARE_TEST.md) before changing anything on the device. Back up your Move sets and existing Sprig WT installation. The expected module directory is `/data/UserData/schwung/modules/sound_generators/sprig-wt`; verify the packaging and supported Schwung Manager installation route before deploying.

Do not overwrite a known-good installation with an experimental build unless you can restore it. Schwung v1.9 compatibility, canvas navigation, encoder refresh, stereo pan and filter variants require on-device verification.

## Recent changes on main\n\n### Audio-engine parity pass (14 November 2026)\n\n- Added independent left/right per-voice filter states so OSC 1 and OSC 2 pan can produce stereo output while retaining the shared master-filter settings.\n- Routed wavetable-position LFO modulation to OSC 2 as well as OSC 1.\n- Made warp amount 0 neutral for all modes and increased the audible range of Quantize. Other warp algorithms still need hardware verification.\n- Added desktop regression tests for pan extremes, centered stereo and OSC 2 modulation.\n- Standardized the displayed OSC 1/OSC 2 wavetable and position labels in both packaged metadata and live DSP chain parameters. Internal parameter keys remain unchanged for preset compatibility.\n- **Not yet hardware-verified:** The latest GitHub Actions run must pass before installing; warp parity, parameter naming, and four graphical pages remain outstanding.\n\n## Development priorities

1. **Phase 1:** Dual wavetable oscillator DSP, independently controlled warp, audio tests and stereo pan.
2. **Phase 2:** Four native Synth Face pages and graph rendering that matches oscillator and filter mathematics; confirm Schwung's page-navigation contract.
3. **Phase 3:** Master LP/HP/BP/comb modes, filter display, modulation indicators, CPU profiling and regression tests.
4. **Hardware acceptance:** Verify each page, knob, preset restoration, note handling, CPU load and audible warp behavior on Ableton Move.

## Repository and licensing

Current repository: [chutneyrebel/shrig](https://github.com/chutneyrebel/shrig). Active development takes place directly on `main`. Experimental changes are not releases.

MIT license; see [LICENSE](LICENSE). Not affiliated with or endorsed by Ableton, the Schwung developers, Xfer Records or the creators of Shrub.
