# Sprig WT v0.2.1: Phase 0 and 1 compatibility notes

## Schwung compatibility facts

The primary host reference is https://github.com/charlesvestal/schwung/blob/main/docs/MODULES.md.

- For a sound generator the **live DSP** supplies chain_params and ui_hierarchy via get_param(). module.json alone is not enough to register the native pages. The live definitions are now generated from the canonical metadata by scripts/generate_metadata.py.
- Native as_page canvases inherit the *knobs of their enclosing hierarchy level*. MAIN is on root; OSC1, OSC2 and FILTER are in their respective child levels. Therefore the jog wheel does **not** cycle all four as consecutive root pages with separate knob sets. The user enters the appropriate child level; this is what the current Schwung contract permits.
- Each as_page canvas receives no more than four extra_keys. All four use just **face_snapshot**, one derived, read-only, non-persistent comma-separated DSP value containing 25 live fields. It is small and never added to the saved state.
- Every existing parameter key, enum option, default and range is compared against tests/preset_abi_baseline.json. Old saved states can be restored without the new master_pan field, whose neutral default is 50.
- The descriptor must remain smaller than 8192 bytes. CI checks source/live parity and exact archive contents. The original globalThis.canvas_overlay remains available for existing integrations; native pages use the named overlays.

## Phase 1 implemented

MAIN: blended approximation of OSC1 and OSC2 waveforms with note-gated LFO/WT motion. Eight working encoders: Motion Rate, Motion Depth, LFO Filter Depth, Cutoff, Resonance, Master Pan, Level, OSC2 Volume.

OSC1 and OSC2: each has its own eight encoders (table, position, octave, warp type, warp amount, detune, pan and volume). Graphic previews follow the chosen table, morph position and warp.

FILTER: the current master low-pass response preview and existing controls. The full eight modes, filter envelope extension and routing choices remain Phase 3. No nonfunctional mode selector has been exposed.

Every native face has four concise meters. Schwung draws touched encoder names/values in the host header; the canvas does not duplicate that overlay.

The hybrid LFO design approved for Phase 5 (free/synced dual modulators and matrix destinations) is *not* claimed as implemented here. Existing one-LFO sound and old presets are retained.

## CI vs on-device acceptance

The action runs host DSP/ABI tests, native canvas JS tests, AArch64 build and package checks. Even a fully green Actions run does **not** verify Move CPU usage, real knob behavior, jog navigation, Schwung version quirks or audio fidelity.

Before calling this a release, test on Ableton Move: native level navigation, encoder mappings and refresh, osc1/osc2 wave and warp audition, both pan stages, old preset restore, note-on/off animation and idle stillness, filter response, stock Move coexistence and resource use. Keep a known-good backup.
