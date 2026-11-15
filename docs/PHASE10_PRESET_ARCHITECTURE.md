# Phase 10A: Hybrid preset format

Phase 10A is **host-side groundwork only**. No new Move controls, DSP parameter writes, preset file I/O on the device, or audible changes are introduced.

## Format
A preset is a UTF-8 JSON object with exactly four fields: `schema` (currently 1), `module_id` (`synth_esis`), `name` (1–64 non-whitespace characters), and `parameters` (a complete map of writable numeric synth parameters from `src/module.json`).

`scripts/preset_schema.py` generates an Init patch, validates patches, and provides deterministic serialization and strict parsing. It rejects unknown/missing keys, invalid enum values, out-of-range numbers, duplicate JSON keys, NaN/Infinity, invalid module IDs, and oversized payloads. Read-only visualization and voice-activity fields are excluded. No assumptions about Schwung's file storage API are made.

## Hybrid preview contract for later phases
1. Capture the currently active patch as a rollback snapshot before entering preview.
2. Browsing selects a candidate without overwriting native project state.
3. Preview temporarily applies a validated patch, with rollback on cancel or leaving the browser.
4. Confirm commits the candidate as the current patch; saving to native Schwung state and a user library are separate explicit actions.
5. Preset switching must be voice-safe, avoid intermediate partial-state changes and preserve predictable output levels.
6. Factory presets are read-only; user presets must use an independently verified writable location and atomic storage mechanism.
7. Hardware navigation, persistence and preview/rollback cannot be implemented until Schwung's actual API behavior is verified.

## Validation
Run `python3 -m unittest discover -s tests -p test_preset_schema.py`. CI runs the same tests alongside the existing DSP, canvas and package checks. Phase 10A alone does not require new Move hardware validation because it is not bundled into the instrument.
