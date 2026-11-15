"""Phase 10C: transport-independent, reversible preset audition state machine.

No Schwung API or device file I/O is assumed. The host adapter must provide a
complete current patch and an atomic, voice-safe apply callback before integration.
"""
from copy import deepcopy
from preset_schema import validate_patch

class PreviewSession:
    def __init__(self, read_current, apply_atomic):
        self.read_current = read_current
        self.apply_atomic = apply_atomic
        self.original = None
        self.candidate = None

    @property
    def active(self):
        return self.original is not None

    def begin(self):
        if self.active:
            raise RuntimeError("preview already active")
        original = deepcopy(validate_patch(self.read_current()))
        self.original = original
        self.candidate = None

    def preview(self, patch):
        if not self.active:
            raise RuntimeError("begin preview first")
        candidate = deepcopy(validate_patch(patch))
        # Apply must be atomic. If the host rejects a patch, restore the
        # snapshot and propagate the original error.
        try:
            self.apply_atomic(candidate)
        except Exception:
            try:
                self.apply_atomic(deepcopy(self.original))
            finally:
                self.candidate = None
            raise
        self.candidate = candidate

    def confirm(self):
        if not self.active or self.candidate is None:
            raise RuntimeError("nothing to confirm")
        committed = deepcopy(self.candidate)
        self.original = None
        self.candidate = None
        return committed

    def cancel(self):
        if not self.active:
            return
        self.apply_atomic(deepcopy(self.original))
        self.original = None
        self.candidate = None

    def close(self):
        self.cancel()
