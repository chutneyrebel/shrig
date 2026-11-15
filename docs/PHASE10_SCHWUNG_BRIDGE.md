# Phase 10E: Schwung preset bridge readiness

The existing `src/web_ui.html` uses `window.schwungRemote.setParam(component + ':' + key, value)` and subscribes to `onParamChange`. These observations **do not** establish a complete, authoritative current-state snapshot, synchronous acknowledgement, atomic multi-parameter writes, or guaranteed rollback. No runtime preset apply is enabled.

`scripts/preset_bridge.py` implements a fail-closed dry-run bridge. It requires two fully schema-valid patch snapshots, produces a deterministic changed-parameter plan, and refuses to write to hardware. This allows offline validation of factory presets and future user patches without corrupting a running set.

Before real audition can be enabled, verify on Schwung/Move:
1. How to read **all** 68 writable parameters, including those absent from the current web UI, and distinguish fresh values from defaults.
2. How to apply a complete patch without audible intermediate states or stuck voices; whether batch transactions exist.
3. How parameter acknowledgement and failure are reported.
4. How to restore the exact original patch after cancellation, page exit, or interrupted preview.
5. Whether the native hierarchy supports suppressing the generated MAIN/root control page while retaining the animated FACE page.
6. Where user presets may be saved atomically without modifying factory presets.

**Release gate:** Do not connect preview buttons to `setParam` or suppress MAIN based on an undocumented metadata flag. Add targeted integration tests and hardware validation after the API contracts are confirmed.
