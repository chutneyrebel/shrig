# Phase 10F: upstream Schwung runtime investigation

Source reviewed: [charlesvestal/schwung](https://github.com/charlesvestal/schwung), `main` on 2026-11-15. Relevant upstream files:
- `src/shared/param_pages/page_plan.mjs`
- `src/shared/param_pages/page_nav.mjs`
- `src/shadow/shadow_ui_presets.mjs`
- `schwung-manager/static/schwung-remote-api.js`

## MAIN duplication is upstream behavior

`page_plan.mjs` explicitly plans `page_first` canvas pages **before** the level's ordinary knob grid. Its own comment says the canvas page carries the level's knobs and **the grid follows it**. The Synth_esis root declares eight knobs and an `as_page: true, page_first: true` FACE canvas. Consequently FACE and MAIN are intentionally generated as separate pages by the host planner. No documented `hide_grid` or `skip_grid` flag was found in the reviewed planner.

**Do not delete root.knobs**: the canvas page uses them too, so this would break the FACE encoders. **Do not invent a metadata suppression flag**: it would silently be ignored or introduce unexpected behavior.

Options requiring future testing:
1. Request/add an upstream opt-in `canvas_only`/equivalent page-planner feature to suppress a level's ordinary grid while retaining its canvas and knob bindings. This changes Schwung, not Synth_esis alone.
2. Keep MAIN until an upstream-compatible implementation exists.

## Native user presets already exist

`src/shadow/shadow_ui_presets.mjs` documents a generic per-component preset browser, stored under `/data/UserData/schwung/presets/<module-id>/<name>.json`, with slot `<prefix>:state` snapshots. It already supports debounced audition, revert-on-Back, confirm-on-pick, and Save/Save As/Delete via a host-provided trailing **My Presets** page. This is distinct from Synth_esis's portable factory patch JSON schema.

**Implication:** Avoid duplicating native user-preset storage or writing directly to the host's private preset directory. Verify that Synth_esis's DSP implements a complete `synth:state` getter/setter compatible with Schwung's generic preset browser. If it does, use the host's built-in trailing My Presets navigation instead of creating an incompatible second page.

## Navigation

The host page planner follows root `params` navigation edges in order and appends host-supplied trailing menus. The requested order therefore has a host-owned tail: MY PRESETS and MODULE should be tested on the actual Schwung build. The existing PR #15 rearranges authored sections, but is not sufficient to remove MAIN.

## Next implementation gates

1. Audit DSP `state` roundtrip: save, change, restore all 68 writable parameters; no UI-only keys or invalid values.
2. Confirm factory preset format conversion to host-native state and installation strategy; avoid undocumented writes.
3. Validate native My Presets availability on the Move firmware/Schwung revision in use.
4. For MAIN suppression, propose an upstream change and test its backward compatibility; do not risk the currently working module.
