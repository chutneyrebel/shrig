"""Host audio integration tests for baked compositional spectra.

Requires build/dsp-host.so from tests/test_plugin.py (the preceding CI step).
The numbers are output comparisons, not claims about Move CPU performance.
"""
import ctypes as C
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


CREATE = C.CFUNCTYPE(C.c_void_p, C.c_char_p, C.c_char_p)
DESTROY = C.CFUNCTYPE(None, C.c_void_p)
MIDI = C.CFUNCTYPE(None, C.c_void_p, C.POINTER(C.c_uint8), C.c_int, C.c_int)
SET = C.CFUNCTYPE(None, C.c_void_p, C.c_char_p, C.c_char_p)
GET = C.CFUNCTYPE(C.c_int, C.c_void_p, C.c_char_p, C.c_char_p, C.c_int)
RENDER = C.CFUNCTYPE(None, C.c_void_p, C.POINTER(C.c_int16), C.c_int)


class Plugin(C.Structure):
    _fields_ = [("api_version", C.c_uint32), ("create", CREATE),
                ("destroy", DESTROY), ("midi", MIDI), ("set", SET),
                ("get", GET), ("error", GET), ("render", RENDER)]


def rms(values):
    return math.sqrt(sum(x * x for x in values) / max(1, len(values)))


class SpectralAudioIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lib = ROOT / "build/dsp-host.so"
        if not lib.exists():
            raise RuntimeError("Run tests/test_plugin.py to compile the host plugin first")
        loaded = C.CDLL(str(lib))
        loaded.move_plugin_init_v2.restype = C.POINTER(Plugin)
        loaded.move_plugin_init_v2.argtypes = [C.c_void_p]
        cls.api = loaded.move_plugin_init_v2(None).contents
        assert cls.api.api_version == 2

    def setp(self, handle, key, value):
        self.api.set(handle, key.encode(), str(value).encode())

    def getp(self, handle, key):
        buffer = C.create_string_buffer(8192)
        n = self.api.get(handle, key.encode(), buffer, 8192)
        self.assertGreaterEqual(n, 0, key)
        return buffer.value.decode()

    def render(self, handle, blocks):
        result = []
        buf = (C.c_int16 * 256)()
        for _ in range(blocks):
            self.api.render(handle, buf, 128)
            result.extend(buf[::2])
        return result

    def note(self, handle, number=60, velocity=110):
        data = (C.c_uint8 * 3)(0x90, number, velocity)
        self.api.midi(handle, data, 3, 0)

    def patch_audio(self, changes, note=60):
        synth = self.api.create(b".", None)
        self.assertTrue(synth)
        try:
            for k, v in {"attack":1, "decay":1, "sustain":100, "cutoff":100,
                         "resonance":0, "shape":50, "position":50,
                         "curated_osc1":8, "curated_osc2":8,
                         "osc1_volume":100, "osc2_volume":0}.items():
                self.setp(synth, k, v)
            for key, value in changes.items():
                self.setp(synth, key, value)
            self.render(synth, 100)  # depth and wavetable smoothing settle
            self.note(synth, note)
            audio = self.render(synth, 18)
            return audio[3 * 128:]
        finally:
            self.api.destroy(synth)

    def test_shift_fold_scramble_and_compound_are_audible(self):
        dry = self.patch_audio({})
        self.assertGreater(rms(dry), 100)
        shift = self.patch_audio({"osc1_spectral_shift":100})
        fold = self.patch_audio({"osc1_spectral_fold":100})
        scramble = self.patch_audio({"osc1_spectral_scramble":100})
        composed = self.patch_audio({"osc1_spectral_shift":100,
                                     "osc1_spectral_fold":100,
                                     "osc1_spectral_scramble":100})
        for name, audio in [("Shift",shift), ("Fold",fold),
                            ("Scramble",scramble), ("Compound",composed)]:
            self.assertGreater(rms([a-b for a,b in zip(dry,audio)]), 15,
                               name + " sounded identical to bypass")
        naive = [(a+b+c)/3 for a,b,c in zip(shift,fold,scramble)]
        self.assertGreater(rms([a-b for a,b in zip(composed,naive)]), 15)

    def test_muted_oscillator_cannot_change_other_oscillator(self):
        baseline = self.patch_audio({"osc2_volume":0})
        osc2_only_changes = self.patch_audio(
            {"osc2_volume":0, "osc2_spectral_shift":100,
             "osc2_spectral_fold":100, "osc2_spectral_scramble":100,
             "osc2_position":91, "curated_osc2":13})
        self.assertEqual(baseline,osc2_only_changes)
        baseline_osc2 = self.patch_audio({"osc1_volume":0,"osc2_volume":100})
        osc1_only_changes = self.patch_audio(
            {"osc1_volume":0, "osc2_volume":100,
             "osc1_spectral_shift":100, "osc1_spectral_fold":100,
             "osc1_spectral_scramble":100,"curated_osc1":10})
        self.assertEqual(baseline_osc2,osc1_only_changes)

    def test_legacy_state_resets_spectral_depth_and_full_state_roundtrips(self):
        synth = self.api.create(b".",None)
        self.assertTrue(synth)
        try:
            controls = ("osc1_spectral_shift", "osc1_spectral_fold",
                        "osc1_spectral_scramble", "osc2_spectral_shift",
                        "osc2_spectral_fold", "osc2_spectral_scramble")
            for i,key in enumerate(controls):
                self.setp(synth,key,10+i*10)
            state = self.getp(synth,"state")
            self.assertTrue(all(f"{key}={10+i*10}" in state for i,key in enumerate(controls)))
            self.api.set(synth,b"state",b"curated_osc1=8,curated_osc2=8,level=70")
            self.assertTrue(all(self.getp(synth,key)=="0" for key in controls))
            self.api.set(synth,b"state",state.encode())
            self.assertTrue(all(self.getp(synth,key)==str(10+i*10)
                                for i,key in enumerate(controls)))
        finally:
            self.api.destroy(synth)


if __name__ == "__main__":
    unittest.main()
