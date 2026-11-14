#!/usr/bin/env python3
"""Host-side ABI smoke tests for Sprig WT, no Move access needed."""
import ctypes as C
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'
BUILD.mkdir(exist_ok=True)
if not (ROOT/'src/expanded_tables.h').is_file():
    subprocess.run(['python3',str(ROOT/'scripts/generate_expanded_tables.py')],check=True)
if not (ROOT/'src/tables.h').is_file():
    subprocess.run(['python3',str(ROOT/'scripts/generate_tables.py')],check=True)
so = BUILD / 'dsp-host.so'
subprocess.run(['gcc', '-std=c11', '-O2', '-shared', '-fPIC', '-ffreestanding', '-fno-builtin',
                '-fvisibility=hidden', str(ROOT/'src/dsp.c'), '-o', str(so)],check=True)
# Build with a structure ABI matching the public Schwung plugin_api_v2_t declaration.
CREATE = C.CFUNCTYPE(C.c_void_p,C.c_char_p,C.c_char_p)
DESTROY = C.CFUNCTYPE(None,C.c_void_p)
MIDI = C.CFUNCTYPE(None,C.c_void_p,C.POINTER(C.c_uint8),C.c_int,C.c_int)
SET = C.CFUNCTYPE(None,C.c_void_p,C.c_char_p,C.c_char_p)
GET = C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_char_p,C.c_char_p,C.c_int)
RENDER = C.CFUNCTYPE(None,C.c_void_p,C.POINTER(C.c_int16),C.c_int)
class Plugin(C.Structure):
    _fields_ = [('api_version',C.c_uint32),('create',CREATE),('destroy',DESTROY),
                ('midi',MIDI),('set',SET),('get',GET),('error',GET),('render',RENDER)]
lib=C.CDLL(str(so))
lib.move_plugin_init_v2.restype=C.POINTER(Plugin)
lib.move_plugin_init_v2.argtypes=[C.c_void_p]
api=lib.move_plugin_init_v2(None).contents
assert api.api_version==2
inst=api.create(b'.',None)
assert inst

def midi(status,note,velocity,src=0):
    buf=(C.c_uint8*3)(status,note,velocity)
    api.midi(inst,buf,3,src)

def setp(k,v):api.set(inst,k.encode(),str(v).encode())
def getp(k):
    buf=C.create_string_buffer(8192)
    r=api.get(inst,k.encode(),buf,8192)
    assert r>=0,(k,r)
    return buf.value.decode()
def render(n=1):
    buf=(C.c_int16*256)()
    out=[]
    for _ in range(n):
        api.render(inst,buf,128)
        out.extend(buf[::2])
        assert list(buf[0::2])==list(buf[1::2])
    return out

def rms(seq):return math.sqrt(sum(x*x for x in seq)/len(seq))

# Stage 3A architecture guard: legacy tables and preset IDs stay untouched.
header=(ROOT/'src/wavetable_engine.h').read_text()
assert '#define SPRIG_LEGACY_BANK 0' in header
assert '#define SPRIG_LEGACY_WAVES 4' in header
assert '#define SPRIG_LEGACY_FRAMES 4' in header
assert '#define SPRIG_LEGACY_BANDS 9' in header
assert 'sprig_table_lookup_legacy' in (ROOT/'src/dsp.c').read_text()
meta=json.loads((ROOT/'src/module.json').read_text())
assert meta['api_version']==2 and meta['id']=='sprig-wt'
assert len(meta['capabilities']['ui_hierarchy']['levels']['root']['knobs'])==8
assert meta['capabilities']['ui_hierarchy']['levels']['root']['knobs'][:2]==['wt_bank','bank_select'], 'Expanded oscillator controls must be visible on root Move knobs'
assert meta['capabilities']['ui_hierarchy']['levels']['osc']['params'][:3]==['wt_bank','bank_select','position']
assert len(meta['capabilities']['chain_params'])==26
# v1.9 obtains canvas type/as_page metadata from DSP chain_params, not module.json.
chain_params=json.loads(getp('chain_params'))
assert chain_params==meta['capabilities']['chain_params'], 'DSP and packaged chain_params drifted'
face=next((p for p in chain_params if p.get('key')=='face'), None)
assert face and face['type']=='canvas' and face['as_page'] is True and face['page_first'] is True
assert face['canvas_script']=='canvas.js'
assert 'voice_activity' in face['extra_keys']
assert getp('voice_activity')=='0'
hierarchy=json.loads(getp('ui_hierarchy'))
assert hierarchy==meta['capabilities']['ui_hierarchy'], 'Live DSP legacy hierarchy differs from shipped metadata'
assert 'levels' in hierarchy and 'root' in hierarchy['levels']
assert any(isinstance(p,dict) and p.get('key')=='face' and p.get('type')=='canvas' for p in hierarchy['levels']['root']['params'])
assert any(isinstance(p,dict) and p.get('level')=='filter_env' for p in hierarchy['levels']['root']['params'])
assert getp('module_id')=='sprig-wt'
assert getp('attack')=='10'
assert getp('osc2_level')=='0' and getp('lfo_depth')=='0'
setp('osc2_level',42);setp('detune',73);setp('lfo_depth',28);setp('drive',25)
assert getp('osc2_level')=='42' and getp('detune')=='73' and getp('drive')=='25'
setp('osc2_level',0);setp('lfo_depth',0);setp('drive',0)
setp('filter_env_amt',65);setp('filter_env_attack',10);setp('filter_env_decay',420);setp('lfo_filter',32)
assert getp('filter_env_amt')=='65' and getp('filter_env_decay')=='420'
setp('filter_env_amt',0);setp('lfo_filter',0)
assert rms(render(10))==0
# MIDI note-on produces audible nonzero sound.
midi(0x90,60,105)
assert getp('voice_activity')=='1'
played=render(50)
assert rms(played[512:])>50,rms(played)
assert max(abs(x) for x in played)<32768
# Note-off tail returns to silence.
midi(0x80,60,0)
tail=render(140)
assert rms(tail[-256:])<1
assert getp('voice_activity')=='0'
# Waveform vs position changes materially alter the output.
def sample_with(wave,position):
    midi(0xB0,123,0);render(8)
    setp('wave',wave);setp('position',position)
    render(80)
    midi(0x90,60,110)
    x=render(20)
    midi(0x80,60,0)
    render(120)
    return x
x=sample_with(1,0)
y=sample_with(1,100)
assert rms([a-b for a,b in zip(x,y)])>100, 'Position parameter is not audible'
# String enum path supports UI labels.
setp('wave','Triangle');assert getp('wave')=='3'
setp('wave','Sine');assert getp('wave')=='0'
setp('wave','Square');assert getp('wave')=='2'
# Stage 3A.3: the fourth knob is bank-sensitive when the host refreshes hierarchy.
setp('wt_bank',1)
expanded_hierarchy=json.loads(getp('ui_hierarchy'))
assert expanded_hierarchy['levels']['root']['knobs'][3]=='bank_shape'
assert 'spectral_shape' in expanded_hierarchy['levels']['osc']['params']
setp('spectral_shape',0)
assert getp('spectral_shape')=='0'
setp('spectral_shape',100)
assert getp('spectral_shape')=='100'
setp('spectral_shape',50)
setp('wt_bank',0)
assert json.loads(getp('ui_hierarchy'))['levels']['root']['knobs'][3]=='bank_shape'
assert getp('wave') in ('0','1','2','3')
# Expanded bank is opt-in: old state without new keys must stay in Legacy.
setp('wt_bank',1);setp('wt_table',47)
assert getp('wt_bank')=='1' and getp('wt_table')=='47'
# Spectral Shape must affect audio, not just UI metadata.
setp('spectral_shape',0)
dark=sample_with(1,50)
setp('spectral_shape',100)
bright=sample_with(1,50)
assert rms([a-b for a,b in zip(dark,bright)])>50, 'Spectral Shape must audibly alter the expanded waveform'
setp('spectral_shape',50)
expanded=sample_with(1,50)
setp('wt_bank',0)
legacy=sample_with(1,50)
assert rms([a-b for a,b in zip(expanded,legacy)])>100
setp('wt_bank',1);setp('wt_table',999)
assert getp('wt_table')=='47'
setp('wt_bank',0);setp('wt_table',0)
assert getp('wt_bank')=='0'
# Round-trip presets and clamp out-of-range writes.
setp('attack',112);setp('cutoff',35);setp('level',70)
state=getp('state')
setp('attack',1950);setp('cutoff',99)
setp('state',state)
assert getp('attack')=='112' and getp('cutoff')=='35'
setp('sustain',999);assert getp('sustain')=='100'
setp('release',-500);assert getp('release')=='0'
setp('release',280)
# Maximum voice stress, bounded PCM and valid output.
for n in range(48,72):midi(0x90,n,127)
poly=render(200)
assert 0 < rms(poly) and max(abs(v) for v in poly)<=32767
assert getp('voice_activity')=='8'
for n in range(48,72):midi(0x80,n,0)
render(200)
assert getp('voice_activity')=='0'
# Instance limit and isolation.
insts=[api.create(b'.',None) for _ in range(7)]
assert all(insts) and not api.create(b'.',None)
for p in insts:api.destroy(p)
api.destroy(inst)
print('PASS: ABI, v1.9 chain_params/canvas contract, render, MIDI, polyphony, wavetable position, enum, state, clamp, limit')
print('Mono audio RMS:',round(rms(played),1))
print('Polyphony audio RMS:',round(rms(poly),1))

# Cached host mapping: the same proxy keys must resolve to bank-specific targets.
setp('wt_bank',0);setp('bank_select',3);setp('bank_shape',20)
assert getp('wave')=='3' and getp('legacy_shape')=='20'
assert getp('bank_select')=='3' and getp('bank_shape')=='20'
setp('wt_bank',1);setp('bank_select',47);setp('bank_shape',85)
assert getp('wt_table')=='47' and getp('spectral_shape')=='85'
assert getp('wave')=='3' and getp('legacy_shape')=='20'
assert getp('bank_select')=='47' and getp('bank_shape')=='85'
setp('wt_bank',0)
assert getp('bank_select')=='3' and getp('bank_shape')=='20'
print('PASS: cached physical knob proxies preserve independent bank controls')
