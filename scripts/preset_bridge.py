"""Dry-run parameter bridge for Synth_esis factory presets.

Never writes to hardware. Schwung's remote API exposes setParam, but no
verified atomic multi-parameter commit or complete-state snapshot protocol.
A caller must explicitly supply a verified, complete current snapshot.
"""
from copy import deepcopy
from preset_schema import parameter_specs, validate_patch

class UnsafePresetApply(RuntimeError):
    pass

def build_apply_plan(current, candidate):
    """Validate two full snapshots and return deterministic changed parameters."""
    current = validate_patch(deepcopy(current))
    candidate = validate_patch(deepcopy(candidate))
    specs = parameter_specs()
    changed = []
    for key in specs:
        old = current["parameters"][key]
        new = candidate["parameters"][key]
        if old != new:
            changed.append({"key": key, "from": old, "to": new})
    return changed

class DryRunBridge:
    """Plans changes but cannot send them to a device."""
    def __init__(self, complete_snapshot=None):
        self.complete_snapshot = None
        if complete_snapshot is not None:
            self.capture(complete_snapshot)

    def capture(self, snapshot):
        self.complete_snapshot = deepcopy(validate_patch(snapshot))

    def plan(self, candidate):
        if self.complete_snapshot is None:
            raise UnsafePresetApply("complete live parameter snapshot is required")
        return build_apply_plan(self.complete_snapshot, candidate)

    def apply(self, candidate):
        raise UnsafePresetApply(
            "hardware preset apply disabled: atomic apply, snapshot and rollback unverified"
        )
