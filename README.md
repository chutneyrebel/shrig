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

## Recent changes on main\n\n### Audio-engine parity pass (14 November 2026)\n\n- Added independent left/right per-voice filter states so OSC 1 and OSC 2 pan can produce stereo output while retaining the shared master-filter settings.\n- Routed wavetable-position LFO modulation to OSC 2 as well as OSC 1.\n- Made warp amount 0 neutral for all modes and increased the audible range of Quantize. Other warp algorithms still need hardware verification.\n- Added desktop regression tests for pan extremes, centered stereo and OSC 2 modulation.\n- Standardized the displayed OSC 1/OSC 2 wavetable and position labels in both packaged metadata and live DSP chain parameters.\n- Fixed CI package verification after expanded JSON formatting exceeded the 8 KB metadata limit; the shipped JSON remains compact.\n- Added an early metadata-size regression assertion (before host compilation) and an always-on GitHub Actions diagnostic summary linking to each run's failure logs. GitHub Actions executes on each push; this does not automatically repair failures or send external notifications. Internal parameter keys remain unchanged for preset compatibility.\n- **Not yet hardware-verified:** The latest GitHub Actions run must pass before installing; warp parity, parameter naming, and four graphical pages remain outstanding.\n\n## Development priorities

1. **Phase 1:** Dual wavetable oscillator DSP, independently controlled warp, audio tests and stereo pan.
2. **Phase 2:** Four native Synth Face pages and graph rendering that matches oscillator and filter mathematics; confirm Schwung's page-navigation contract.
3. **Phase 3:** Master LP/HP/BP/comb modes, filter display, modulation indicators, CPU profiling and regression tests.
4. **Hardware acceptance:** Verify each page, knob, preset restoration, note handling, CPU load and audible warp behavior on Ableton Move.

## Repository and licensing

Current repository: [chutneyrebel/shrig](https://github.com/chutneyrebel/shrig). Active development takes place directly on `main`. Experimental changes are not releases.

MIT license; see [LICENSE](LICENSE). Not affiliated with or endorsed by Ableton, the Schwung developers, Xfer Records or the creators of Shrub.


### v0.2.1 warp regression coverage

The host audio suite now checks Off plus all seven active warp modes separately on OSC 1 and OSC 2. For each active mode it compares a fresh-instance reference against zero amount (must be sample-identical) and strong warp (must audibly alter the PCM signal). This is automated audio verification, not yet confirmation of on-device control feel or perceived musical quality.


### Four-face native UI development (not yet hardware-ready)

`src/canvas.js` now contains distinct MAIN, OSC 1, OSC 2 and FILTER drawing functions, with host-side tests for unique traces and meters. The current Schwung metadata still registers only one native canvas page. The four renderers are **not yet four hardware jog-wheel pages**: separate `as_page` declarations and host-compatible overlay selection remain to be wired and tested before the consolidated v0.2.1 hardware test. The FILTER graphic is an illustrative low-pass response, not a measured DSP frequency response; the audio filter remains low-pass only.


### Wavetable expansion in development (v0.2.1)

The unified oscillator selector now targets **100 waveforms per oscillator**: IDs 0–3 retain the original classic tables, IDs 4–51 retain the existing 48 generated spectral tables, and IDs 52–99 add 48 new spectral tables in 12 families (formant peaks, dual peaks, spectral notches, sparse clusters, nonlinear ripples, periodic partial selection, resonant combs and moving clusters). Every expanded table has four morph frames and nine pitch-dependent band-limited versions, generated before compilation with no runtime sample loading. Existing IDs remain stable. This is still a **procedurally generated wavetable library**, not user WAV import, and the native four-page registration is still pending. Test the expanded library, warp engine and four-page hardware navigation together only after the full v0.2.1 release is marked ready.


### Wavetable quality guard (v0.2.1)

New expanded waveforms (IDs 52–99) are DC-centered before peak normalization, while original IDs 0–51 retain their established generation. The host test scans all 48 × 4 × 9 newly generated waveform rows for 256 samples, near-zero mean and conservative headroom. This does not yet implement 16/32-frame wavetables, phase-aligned spectral interpolation, or user WAV imports. Those need explicit memory/CPU and compatibility evaluation before changing the real-time DSP.


### Categorized wavetable library

`src/wavetable_catalog.json` maps the 96 expanded waveforms into Organic & Evolving (28), Industrial & Metallic (36), and Vocal & Spectral (32), with the four classic waveforms separate. The catalog is bundled with the module and checked for complete non-overlapping ID coverage in host tests. These are **discovery categories only**: there is not yet a native Move category picker, and this change does not add new waveforms or alter preset IDs. Native four-page Synth Face registration remains incomplete; hold hardware testing until the combined release is ready.


### Categorized wavetable browsing (v0.2.1)

The Schwung remote HTML interface now provides **independent category pickers for OSC 1 and OSC 2**, alongside each oscillator's continuous wavetable ID slider. Categories are **Classic (0–3)**, **Original Spectral (4–51)**, **Organic / Atmospheric (52–67)**, **Industrial / Metallic (68–83)** and **Vocal / Formant (84–99)**. Choosing a category selects its first waveform; the slider then explores individual waveforms. The category picker follows parameter changes. IDs remain stable for presets. These are sound-design groupings of generated spectral recipes, not imported recordings. Physical Move category browsing and four native canvas page registration remain to be implemented and verified; do not mistake remote HTML grouping for native hardware navigation.
