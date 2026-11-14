# Stage 3: Wavetable expansion contract

## Checkpoint 3A.0 (architecture only)

- Legacy bank ID 0: Sine=0, Saw=1, Square=2, Triangle=3.
- Keep original 4 frames, 9 anti-alias bands, 256 samples per frame, original values and interpolation.
- All existing preset keys, enum labels, audio behavior, DSP voice handling and canvas metadata remain unchanged.
- src/wavetable_engine.h is the new lookup boundary. No new banks are selectable in this checkpoint.

## Planned implementation checkpoints

1. **3A.1 built-in bank:** Generate independently authored, named multi-frame tables in the offline generator. Add a new bank/table selector with default Legacy and preserve the existing wave parameter. Test old preset renders and parameter round-trips. Keep band limiting, interpolation, CPU and memory budgets measurable.
2. **3A.2 OSC 2 selection:** Introduce independent source/table selection for OSC 2, while preserving its legacy saw and existing mix/detune behavior for old presets.
3. **3B warp/modulation:** Add oscillator shaping incrementally with CPU/polyphony stress tests. Avoid allocation, parsing, file I/O or locks on the audio callback.
4. **3C user WAV imports:** Parse WAV off-device or on a non-realtime management path, validate mono/PCM/float formats and cyclic table frames, resample and normalize offline, create band-limited tables, then atomically load prepared immutable assets. Do not assume Schwung's DSP ABI exposes safe filesystem access or hot-reload. Investigate package/manager integration first.
5. **Stage 2C.2 visual response:** Expose DSP-derived velocity, voice count and filter activity as read-only parameters. Keep note-gated idle behavior and native encoder header.

## Hardware validation gates

- Existing preset loaded from previous build has unchanged wave indices and audibly identical output.
- Eight-voice sustained chord, rapid encoder movement, long playback and release tails remain stable.
- UI canvas remains note-gated, non-duplicated, and reloads after a full Move restart.
- Never change the stable v0.1.0 branch or release.
