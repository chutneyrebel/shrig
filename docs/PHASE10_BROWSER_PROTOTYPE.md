# Phase 10D: MY PRESETS browser prototype

Open `tools/preset_browser.html` through an HTTP server rooted at the repository (for example `python3 -m http.server 8000`, then visit `http://localhost:8000/tools/preset_browser.html`).

The browser reads `presets/factory.json`, displays all 16 patches, supports category filtering and text search, and demonstrates the preview/confirm/cancel interaction.

**Safety boundary:** This is a standalone UI prototype, not part of the packaged Move module. Its preview and confirm buttons simulate state only. They do not change audio, call Schwung APIs, write files, or load presets on the Move. The production implementation must use an independently verified Move/Schwung parameter adapter, ensure complete atomic parameter application outside the audio callback, and provide durable save and rollback semantics.

**Acceptance checklist:** 16 items; six categories; search; selection; preview; confirm; cancel; page exit; missing/invalid library; keyboard-accessible controls. Host integration and hardware audition are still pending.
