# Phase 10J: optional native factory preset download

Every successful GitHub Actions run now publishes two **separate** artifacts:

1. `synth_esis-targz-download`: the existing Schwung module archive, unchanged.
2. `synth_esis-native-factory-presets`: 16 JSON files generated from the compiled DSP, for optional manual testing.

Open the successful run on the repository's Actions tab, scroll to **Artifacts**, and download the native factory preset artifact. GitHub delivers artifacts as ZIP files. The extracted contents are JSON files, not a Schwung module installer.

## Hardware validation (not yet performed)

- Confirm the installed Schwung build exposes a **My Presets** page for Synth_esis and the expected per-module state API.
- Back up the existing Synth_esis user-preset folder before adding anything.
- Install **one** exported factory JSON file using a verified device file-management method, without replacing any existing file.
- Check that the preset appears under My Presets, previews correctly, commits on selection, and restores the previous sound on Back.
- Only then test the remaining 15 files. Confirm that ordinary user preset saving still works.

Upstream Schwung documents the per-module folder as `/data/UserData/schwung/presets/synth_esis/`, but the actual installed build and permissions must be checked first. Do not overwrite user files or run unverified filesystem commands.

The CI artifact **does not install presets on Move**, and the module package remains unchanged. This avoids coupling optional preset testing to DSP installation.
