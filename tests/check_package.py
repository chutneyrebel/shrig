#!/usr/bin/env python3
import json
import hashlib
import struct
import subprocess
import tarfile
from pathlib import Path
p=Path(__file__).resolve().parents[1]
archive=p/'dist/sprig-wt-module.tar.gz'
assert archive.is_file()
meta=json.loads((p/'src/module.json').read_text())
assert meta['capabilities']['component_type']=='sound_generator'
assert meta['api_version']==2
assert len((p/'src/module.json').read_bytes()) < 8192
with tarfile.open(archive,'r:gz') as tar:
    names=tar.getnames()
    assert 'sprig-wt/module.json' in names and 'sprig-wt/dsp.so' in names and 'sprig-wt/web_ui.html' in names and 'sprig-wt/canvas.js' in names
    for member in tar.getmembers():
        assert member.name.startswith('sprig-wt/') or member.name=='sprig-wt', member.name
        assert member.isfile() or member.isdir(),member.name
    # Verify that the distributable contains exactly the intended runtime files,
    # and that every nonbinary asset matches the tested source byte-for-byte.
    expected={'dsp.so','module.json','web_ui.html','canvas.js','wavetable_catalog.json'}
    actual={m.name.removeprefix('sprig-wt/') for m in tar.getmembers() if m.isfile()}
    assert actual==expected,('unexpected or missing runtime assets',actual^expected)
    for asset in expected-{'dsp.so'}:
        packaged=tar.extractfile('sprig-wt/'+asset).read()
        source=(p/'src'/asset).read_bytes()
        assert hashlib.sha256(packaged).digest()==hashlib.sha256(source).digest(),('stale packaged asset',asset)
    binary=tar.extractfile('sprig-wt/dsp.so').read()
    assert hashlib.sha256(binary).digest()==hashlib.sha256((p/'build/dsp.so').read_bytes()).digest(),'packaged DSP differs from tested ARM64 build'
assert binary[:4]==b'\x7fELF'
assert binary[4]==2 and binary[5]==1
assert struct.unpack_from('<H',binary,18)[0]==183 # EM_AARCH64
symbol=subprocess.check_output(['nm','-D',str(p/'build/dsp.so')],text=True)
assert 'move_plugin_init_v2' in symbol
unresolved=subprocess.check_output(['readelf','-Ws',str(p/'build/dsp.so')],text=True)
assert not any(' UND ' in line and 'NOTYPE' not in line for line in unresolved.splitlines())
needed=subprocess.check_output(['readelf','-d',str(p/'build/dsp.so')],text=True)
assert 'NEEDED' not in needed
print('PASS: valid ARM64 ELF, exact ABI export, no external dynamic dependencies, archive layout and exact source asset integrity')
