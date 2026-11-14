# Sprig WT on Move: cautious test procedure

**No hardware testing has been performed.** Ensure the Move, Schwung, and your sets are backed up. Testing a new native `.so` inside the shim can crash the host, so start from a blank set and keep a recovery path.

## Recommended: Schwung Manager via GitHub release

1. Publish the project to a dedicated GitHub repository; do not include `SHRUB-V1.00.fwsc`.
2. Let GitHub Actions pass and attach `sprig-wt-module.tar.gz` to a release `v0.1.0`.
3. Add a `release.json` with `version`, `download_url`, `name`, `description`, and `repo_url` pointing at **that existing release**.
4. In Schwung Manager at `http://move.local:7700`, use the appropriate custom-module/repository installation interface if available on your version. If there is no import control, use manual testing below.
5. Create a blank test set. Load **Sprig WT** as the generator in one shadow slot. Set the Move track MIDI Out channel equal to the shadow slot Receive Ch.
6. Play pads. If you hear both the original Move instrument and Sprig, use an empty/silent native instrument on the Move track (per the Schwung FAQ).

## Alternative: manual SSH installation for isolated testing

Only if your Move has SSH access already enabled and you are comfortable with terminal recovery:

```bash
scp dist/sprig-wt-module.tar.gz ableton@move.local:/data/UserData/
ssh ableton@move.local 'mkdir -p /data/UserData/schwung/modules/sound_generators && tar -xzf /data/UserData/sprig-wt-module.tar.gz -C /data/UserData/schwung/modules/sound_generators/'
```

Then fully unload/reload the instrument (restart Schwung/Move if necessary). A module install or update through Manager is preferable once the repository release is published.

## Hardware test checklist

- [ ] Audio plays for a pad and stops after note-off/release
- [ ] Velocity changes volume
- [ ] Two/three notes play together without clicks
- [ ] All eight physical knobs affect the named parameter
- [ ] Wave and Position produce audible timbre changes
- [ ] High filter resonance does not explode or clip badly
- [ ] Preset changes and reload retain state (test and report)
- [ ] No stuck notes after multiple rapid note-ons and offs
- [ ] CPU / audio stability across 1, 4, and 8 voices
- [ ] Unload/reload and restart do not crash the host
- [ ] Stock Move tracks remain functional after uninstall

## Debug / rollback

Capture the Schwung log, if present:

```bash
ssh ableton@move.local 'tail -n 160 /data/UserData/schwung/debug.log'
```

If the module causes problems, first switch the slot to another generator. To remove the isolated test module:

```bash
ssh ableton@move.local 'rm -rf /data/UserData/schwung/modules/sound_generators/sprig-wt'
```

This only removes the `sprig-wt` directory, **not Schwung or Move**. Before rebooting, ensure no patch still auto-loads this module; switch the test slot to a known stable instrument.

## Note when reporting failure

Provide: Move firmware version, Schwung host version, module version, action performed, audible behavior, and a short log excerpt (without personal network information or secrets).
