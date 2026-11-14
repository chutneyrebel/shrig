# Research: independent Shrub-inspired synthesis on Schwung

Date: 2026-11-14

## Confirmed from public Schwung source

- Schwung's module API uses `move_plugin_init_v2` returning a `plugin_api_v2_t` function table.
- `sound_generator` modules are loaded from `modules/sound_generators/<id>/dsp.so`.
- Audio is stereo int16 interleaved, 128 frames/block, 44.1kHz; native param/MIDI callbacks are real-time sensitive.
- A `module.json` capabilities section can declare `chain_params`, `ui_hierarchy`, `midi_in`, `audio_out`, and `chainable`.
- Primary reference: [Tablor](https://github.com/athousanddetails/schwung-tablor), a fully featured polyphonic wavetable generator supporting API v2, native controls, native tests and ARM builds.
- Secondary reference: [Maze Voice](https://github.com/sd88me/schwung-maze), a smaller API-v2 native sound generator with a clear ARM64 build+archive pattern.

## Confirmed from uploaded firmware

- Input files `SHRUB-V1.00.fwsc` and `SHRUB-V1.00(1).fwsc` are byte-for-byte identical.
- SHA-256: `075be13d07de99b32fefd390c95dea0686e1eabc3990fd99cbd0c0897de05e95`
- `.fwsc` marker parsing yields identity `FM-1_901`.
- JieLi UFW header and entry-list CRC-16s pass using the independent format decoder published in [MvaveFM1Unbricker](https://github.com/Quixotic7/MvaveFM1Unbricker).
- UFW has 2 entries; type-0 flash starts at `0x400` and is `0x93000` bytes.

## Inferred or unknown

- Shrub's internal oscillator/filter algorithms have not been recovered; identifying the outer UFW container does **not** identify its executable ISA or DSP algorithm.
- Neither Ghidra disassembly nor REA/Binwalk/Unblob analysis was run in this environment. Dependencies for that path are unavailable.
- No official Shrub desktop VST3 binary was downloaded or inspected; further examination would require a legally obtained binary, compatible tools and separate analysis.
- CPU budget on real Move and compatibility with the currently installed Schwung host have **not** been tested.

## Design decision

Keep v0.1 independently authored: fixed precomputed band-limited wavetables, 8 voices, per-voice SVF low-pass, ADSR, no run-time I/O, no external dependencies. This removes firmware decompilation from the critical path and allows empirical testing before complex modulation is implemented.

## Follow-up REA path

On an isolated Linux x64 analysis machine with official REA + Binwalk + Unblob installed, run the documented `inspect-firmware-regions` and `extract-firmware` against a *copy* of the original package; consider the logical UFW type-0 payload when a generic extractor fails. Do not execute firmware or flash a device during analysis. Compare documented behavior to the independent synth, and import only ideas that can be independently implemented and legally distributed.
