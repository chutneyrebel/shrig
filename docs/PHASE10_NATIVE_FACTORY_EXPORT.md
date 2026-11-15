# Phase 10I: offline native factory preset export

Upstream Schwung's native preset browser reads JSON objects shaped `{"name":"...","module":"synth_esis","version":1,"state":"..."}`. Synth_esis's native `state` is a comma-separated string of DSP parameters and 24 matrix route values, not the portable patch JSON.

Generate 16 native preset JSON files on a desktop with Python 3 and gcc:

```bash
python3 scripts/export_native_factory.py --output-dir build/native-factory-presets
```

The exporter uses the compiled DSP itself to serialize each factory recipe, rather than assuming the order of `state` fields. It refuses to overwrite a nonempty output directory. CI verifies all 16 outputs.

**Safety:** This is an offline export, not an installer. The generated files are NOT bundled into the Schwung module archive and are NOT automatically copied onto the Move. No direct device writes, user-preset directory modifications, or hardware preset changes are made. Installation and visibility in native MY PRESETS must be separately verified with a backed-up device and its installed Schwung version.

**Known limitation:** The portable factory patch format describes the currently selected modulation matrix editor cell, not 24 independent routes. The DSP exports its actual matrix state. Future factory recipes requiring non-neutral per-route modulation must define those routes explicitly.
