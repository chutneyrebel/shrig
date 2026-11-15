# Phase 11C: Schwung canvas-only root page contract

## Hardware evidence (Schwung 1.9.3)
21 functional checks passed on Ableton Move, including FACE encoder control, all DSP functions, preset preview/cancel, persistence, and ten-minute stability. Remaining defects: duplicate MAIN page and old navigation order on the installed build. The child order fix was merged separately in PR #15; a fresh build is needed to observe it.

## Verified host cause
Upstream `charlesvestal/schwung/src/shared/param_pages/page_plan.mjs` walks each level, emits `page_first` canvas pages via `emitCanvasPage(cp,key)`, then always generates `PAGE_KNOBS` pages from `authoredSlots` and overflow `extra`. Root `knobs` must remain: FACE's eight encoder assignments are inherited from them. Removing `root.knobs` is NOT a fix.

## Proposed host opt-in (not implemented in Schwung 1.9.3)
Introduce a boolean canvas declaration `replace_knob_grid: true`, honored only when the canvas has `as_page: true` and `page_first: true` and is visible. Default false for every existing module.

Planner behavior:
1. Compute `authored`, `authoredSlots`, and `extra` exactly as today.
2. Emit the canvas first as today, retaining the page's complete encoder `keys`, `childLevel`, and metadata.
3. For the opted-in canvas, suppress ONLY the corresponding level's duplicate `PAGE_KNOBS` pages when their keys are fully represented on the canvas. Do not suppress overflow keys not represented by canvas; keep them as continuation grids.
4. Preserve selectors, child pickers, child levels, menus, trailing MY PRESETS and MODULE pages, and existing name claims.
5. Mark keys represented by canvas as emitted for duplicate/overflow bookkeeping. Avoid changes to non-opted-in modules.

### Required upstream tests
- No flag: canvas followed by grid, unchanged from current Schwung.
- Opt-in root with exactly eight knobs: one FACE canvas, no MAIN grid; all eight keys identical to existing FACE.
- Opt-in root with nine editable keys: FACE plus a continuation page for the ninth key.
- Hidden/conditional canvas: grid retained, no controls lost.
- Non-`as_page` canvas or `page_first: false`: flag ignored.
- Child pages, presets, and MODULE trailing menus remain in original relative order.
- Duplicate signatures across alias levels still deduplicated correctly.
- All existing Schwung planner tests pass.

### Integration order
1. Implement and test opt-in in upstream Schwung or an explicitly maintained fork.
2. Ship a Schwung version/build containing that support. Do not claim 1.9.3 understands the flag.
3. Add `replace_knob_grid: true` to Synth_esis root FACE declaration only.
4. Regenerate metadata, verify module.json size budget, build and run CI.
5. Install compatible host + module on Move, verify no MAIN and eight FACE encoders, then validate full page order.

### Expected Synth_esis page order
FACE → FACE_OSC1 → OSC1 → FACE_OSC2 → OSC2 → FACE_FILTER → FILTER → MOTION → MATRIX → OSC1 AMP → OSC2 AMP → OSC MIX → MY PRESETS → MODULE.

**Safety:** This document specifies a host change. It does not alter DSP or claim the duplicate page has already been removed.
