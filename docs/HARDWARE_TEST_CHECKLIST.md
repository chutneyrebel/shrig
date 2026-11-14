# Sprig WT v0.2.1: consolidated Ableton Move hardware-test checklist

Status: **Preparation only. Do not install until native page registration is completed and the release is explicitly marked hardware-test-ready.**

## Preflight
- [ ] Latest main GitHub Actions build passes desktop ABI/audio, canvas, ARM64 packaging and integrity tests.
- [ ] Verify the downloaded GitHub Actions artifact is a ZIP containing `sprig-wt-module.tar.gz`; extract the ZIP once.
- [ ] Back up current Schwung configuration, projects and Sprig WT presets before replacing the module.
- [ ] Confirm native MAIN, OSC 1, OSC 2 and FILTER pages are actually registered and reachable on Move. Distinct drawing functions alone do **not** prove hardware page navigation.

## Audio and controls
- [ ] Load a known existing preset (IDs 0–99); confirm it sounds and recalls the same settings.
- [ ] Select curated IDs 100–107 on OSC 1 and OSC 2, individually and together; check sound, level and silence/dropouts.
- [ ] Sweep WT Position 0–100% for each curated table; listen for discontinuities, unexpected clicks and level spikes.
- [ ] Set Motion Depth to zero and WT LFO Depth above zero; confirm wavetable motion is audible and controllable.
- [ ] Restore WT LFO Depth to zero; confirm existing motion/preset behavior remains unchanged.
- [ ] Save, reload and reopen a project using distinct OSC 1/OSC 2 curated IDs, positions and WT LFO Depth.
- [ ] Exercise all eight warp modes on each oscillator; verify zero warp amount remains neutral.
- [ ] Test polyphony, note release and rapid parameter changes.

## Screen and Remote
- [ ] Verify native Move screen displays IDs 100–107 without reverting to 99.
- [ ] Check main, OSC 1 and OSC 2 waveform previews at 0%, 50% and 100% WT Position.
- [ ] Confirm screen animation stops when voices are idle and follows WT LFO Depth while playing.
- [ ] Confirm Schwung Remote shows curated names, both oscillator selections and parameter updates.
- [ ] Check screen redraw responsiveness and audio stability while navigating.

## Performance and reporting
- [ ] Play eight simultaneous notes with both oscillators active, WT LFO Depth 100% and sustained modulation.
- [ ] Note audio glitches, interface lag, thermal issues or excessive CPU use. Host benchmark numbers do not measure Move CPU.
- [ ] Record Schwung version, Move firmware, build commit, installed artifact and reproduction steps for any issue.
- [ ] If anything fails, restore the backed-up module and preset state.

**Release gate:** Do not call v0.2.1 hardware-test-ready until native four-page registration is verified in source and CI, the build passes, and the consolidated archive is identified.
