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
assert len((ROOT/'src/module.json').read_bytes()) < 8192, 'Sprig WT metadata exceeds 8 KB'
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
        # Stereo channels may differ when either oscillator is panned.
    return out

def rms(seq):return math.sqrt(sum(x*x for x in seq)/len(seq))

# The three sound-design categories must cover each expanded waveform once.
catalog=json.loads((ROOT/'src/wavetable_catalog.json').read_text())
assert catalog['classic']['ids']==[0,3]
assert set(catalog['categories'])=={'organic','industrial','vocal'}
ids=[]
for category,families in catalog['categories'].items():
    for family in families:
        lo,hi=family['ids']
        assert hi-lo==3,(category,family)
        ids.extend(range(lo,hi+1))
assert sorted(ids)==list(range(4,100)), 'Catalog must cover each expanded wavetable exactly once'
print('PASS: organic, industrial and vocal catalog covers all 96 expanded waveforms')
# New spectral tables must be DC-centered without changing established IDs.
# Inspect generated float rows, not just the recipe's intent.
import re
table_text=(ROOT/'src/expanded_tables.h').read_text()
rows=re.findall(r'\{([^{}]+)\}',table_text)
assert len(rows)==104*4*9, ('unexpected expanded table dimensions',len(rows))
for wave in range(48,96):
    for frame in range(4):
        for band in range(9):
            row=rows[(wave*4+frame)*9+band]
            samples=[float(x.rstrip('f')) for x in row.split(',') if x.strip()]
            assert len(samples)==256
            assert abs(sum(samples)/256)<0.0001,(wave,frame,band,'DC bias')
            assert max(abs(x) for x in samples)<=0.871,(wave,frame,band,'headroom')
print('PASS: all new wavetable frames are DC-centered with safe headroom')
# Spectral checks compare the actual generated band-limited waveform frames.
# Core IDs 100-107 are appended; every historical ID 0-99 remains unchanged.
def table_row(wave,frame,band=0):
    row=rows[((wave-4)*4+frame)*9+band]
    return [float(x.rstrip('f')) for x in row.split(',') if x.strip()]
def spectral_features(samples):
    # Compare normalized harmonic magnitude profiles, ignoring phase shifts.
    mags=[]
    for h in range(1,49):
        re=sum(v*math.cos(2*math.pi*h*i/256) for i,v in enumerate(samples))
        im=sum(v*math.sin(2*math.pi*h*i/256) for i,v in enumerate(samples))
        mags.append(math.hypot(re,im))
    total=sum(mags) or 1
    return [v/total for v in mags]
def spectral_distance(a,b):
    return sum(abs(x-y) for x,y in zip(a,b))
cores={i:[spectral_features(table_row(i,f)) for f in range(4)] for i in range(100,108)}
for i,frames in cores.items():
    assert spectral_distance(frames[0],frames[3])>.18,(i,'insufficient position evolution')
for i in cores:
    for j in cores:
        if i>=j:continue
        assert max(spectral_distance(cores[i][f],cores[j][f]) for f in (0,3))>.22,(i,j,'core timbres too similar')
print('PASS: eight core tables exhibit position evolution and pairwise spectral distinction')
# Remote curated discovery keeps the full numeric ID range for preset recall.
remote=(ROOT/'src/web_ui.html').read_text()
assert 'const curatedWaves=[' in remote and 'curatedIds' in remote
for label in ('Pure · Fundamental','Glass · Bell','Vocal · Formant','Metal · Cluster','Alien · Fracture'):
    assert label in remote, ('missing curated sound',label)
assert "['wavetable','OSC 1 Wavetable',0,107,1]" in remote
assert "['osc2_wavetable','OSC 2 Wavetable',0,107,1]" in remote
assert 'Other / Existing Preset' in remote
print('PASS: curated discovery and legacy preset IDs coexist')
# Stage 3A architecture guard: legacy tables and preset IDs stay untouched.
header=(ROOT/'src/wavetable_engine.h').read_text()
assert '#define SPRIG_LEGACY_BANK 0' in header
assert '#define SPRIG_LEGACY_WAVES 4' in header
assert '#define SPRIG_LEGACY_FRAMES 4' in header
assert '#define SPRIG_LEGACY_BANDS 9' in header
assert 'sprig_table_lookup_legacy' in (ROOT/'src/dsp.c').read_text()
meta=json.loads((ROOT/'src/module.json').read_text())
assert meta['api_version']==2 and meta['id']=='sprig-wt'
assert len((ROOT/'src/module.json').read_bytes())<8192, 'module.json must fit Schwung 8 KB metadata limit'
assert len(meta['capabilities']['ui_hierarchy']['levels']['root']['knobs'])==8
assert meta['capabilities']['ui_hierarchy']['levels']['root']['knobs'][:2]==['lfo_rate','lfo_depth'], 'Main controls must prioritize motion'
assert all(k in meta['capabilities']['ui_hierarchy']['levels']['root']['knobs'] for k in ('osc1_detune','osc2_detune','osc2_volume')), 'Native face missing audition controls'
assert meta['capabilities']['ui_hierarchy']['levels']['osc1']['params'][:3]==['wavetable','position','osc1_octave']
assert len(meta['capabilities']['chain_params'])==43
assert 'lfo_wt_depth' in meta['capabilities']['ui_hierarchy']['levels']['motion']['params']
assert 'lfo_wt_depth' in meta['capabilities']['ui_hierarchy']['levels']['motion']['knobs']
# v1.9 obtains canvas type/as_page metadata from DSP chain_params, not module.json.
chain_params=json.loads(getp('chain_params'))
assert chain_params==meta['capabilities']['chain_params'], 'DSP and packaged chain_params drifted'
warp_labels=['Off','Sync','Bend+','Bend-','PWM','Asym','Mirror','Quant']
for key in ('osc1_warp_type','osc2_warp_type'):
    info=next(p for p in chain_params if p['key']==key)
    assert info['type']=='enum' and info['options']==warp_labels,(key,info)
remote_ui=(ROOT/'src/web_ui.html').read_text()
assert "const warpNames=['Off','Sync','Bend+','Bend−','PWM','Asym','Mirror','Quant']" in remote_ui
assert "['osc1_warp_type','OSC 1 Warp Type'" in remote_ui
assert "['osc2_warp_type','OSC 2 Warp Type'" in remote_ui
assert "['osc2_volume','OSC 2 Volume',0,100,1]" in remote_ui, 'Remote OSC 2 volume slider missing'
print('PASS: native and remote UI expose eight named warp modes')
face=next((p for p in chain_params if p.get('key')=='face'), None)
assert face and face['type']=='canvas' and face['as_page'] is True and face['page_first'] is True
assert face['canvas_script']=='canvas.js'
assert 'voice_activity' in face['extra_keys']
assert getp('voice_activity')=='0'
hierarchy=json.loads(getp('ui_hierarchy'))
assert hierarchy==meta['capabilities']['ui_hierarchy'], 'Live DSP legacy hierarchy differs from shipped metadata'
assert 'levels' in hierarchy and 'root' in hierarchy['levels']
assert any(isinstance(p,dict) and p.get('key')=='face' and p.get('type')=='canvas' for p in hierarchy['levels']['root']['params'])
assert any(isinstance(p,dict) and p.get('level')=='osc2' for p in hierarchy['levels']['root']['params'])
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
# Unified selection exposes all 100 waveforms without a bank switch.
assert json.loads(getp('ui_hierarchy'))['levels']['osc1']['knobs'][:3]==['wavetable','position','osc1_octave']
setp('wavetable',0);assert getp('wavetable')=='0'
setp('wavetable',107);assert getp('wavetable')=='107'
setp('wavetable',999);assert getp('wavetable')=='107'
setp('wavetable',4);setp('shape',0)
dark=sample_with(1,50)
setp('shape',100)
bright=sample_with(1,50)
assert rms([a-b for a,b in zip(dark,bright)])>50, 'Unified Shape must change the sound'
setp('shape',50)
setp('wavetable',1)
classic=sample_with(1,50)
setp('wavetable',88)
spectral=sample_with(1,50)
assert rms([a-b for a,b in zip(classic,spectral)])>100, 'Unified table selector must change audio'
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
# Stereo pan and OSC 2 motion regression checks.
def stereo_with(pan1,pan2,depth=0):
    midi(0xB0,123,0);render(140)
    setp('osc1_volume',100);setp('osc2_volume',100)
    setp('osc2_level',0);setp('osc1_pan',pan1);setp('osc2_pan',pan2)
    setp('lfo_depth',depth);setp('osc2_wavetable',20)
    midi(0x90,60,110)
    buf=(C.c_int16*256)()
    left=[];right=[]
    for _ in range(50):
        api.render(inst,buf,128)
        left.extend(buf[0::2]);right.extend(buf[1::2])
    midi(0x80,60,0);render(140)
    return left,right
left,right=stereo_with(0,0)
assert rms(left)>100 and rms(right)<2, 'Full left pan must silence right channel'
left,right=stereo_with(100,100)
assert rms(right)>100 and rms(left)<2, 'Full right pan must silence left channel'
left,right=stereo_with(50,50)
assert rms(left)>100 and left==right, 'Center pan must be symmetric'
setp('osc1_volume',0);setp('osc2_volume',100)
setp('osc1_pan',50);setp('osc2_pan',50)
def osc2_motion(depth):
    midi(0xB0,123,0);render(140)
    setp('lfo_depth',depth)
    midi(0x90,60,110)
    x=render(100)
    midi(0x80,60,0);render(140)
    return x
motion_off=osc2_motion(0)
motion_on=osc2_motion(90)
assert rms([a-b for a,b in zip(motion_off,motion_on)])>10, 'OSC2 must respond to motion'
setp('lfo_depth',0)
print('PASS: independent stereo pan and OSC2 wavetable motion')
# Optional WT LFO control must be readable and remain neutral by default.
assert getp('lfo_wt_depth')=='0'
setp('lfo_wt_depth',100)
assert getp('lfo_wt_depth')=='100'
setp('lfo_wt_depth',0)
assert getp('lfo_wt_depth')=='0'
assert 'lfo_wt_depth' in (ROOT/'src/web_ui.html').read_text()
print('PASS: opt-in WT LFO depth control and legacy-neutral default')
# Warp regression: each mode must preserve neutral at zero amount and
# produce distinct audio at strong settings on either oscillator.
# Create a fresh instance for each render to eliminate phase/history drift.
def warp_audio(osc, mode, amount):
    probe=api.create(b'.',None)
    assert probe, 'No free voice slot for warp regression'
    def put(key,val): api.set(probe,key.encode(),str(val).encode())
    put('attack',0);put('cutoff',100);put('resonance',0)
    put('lfo_depth',0);put('filter_env_amt',0);put('lfo_filter',0)
    put('osc1_volume',100 if osc==1 else 0)
    put('osc2_volume',100 if osc==2 else 0)
    put('osc2_level',0)
    put('wavetable',1);put('osc2_wavetable',1)
    put('osc1_warp_type',mode if osc==1 else 0)
    put('osc2_warp_type',mode if osc==2 else 0)
    put('osc1_warp',amount if osc==1 else 0)
    put('osc2_warp',amount if osc==2 else 0)
    msg=(C.c_uint8*3)(0x90,60,110)
    api.midi(probe,msg,3,0)
    buf=(C.c_int16*256)()
    audio=[]
    for _ in range(48):
        api.render(probe,buf,128)
        audio.extend(buf[::2])
    api.destroy(probe)
    return audio

for osc in (1,2):
    baseline=warp_audio(osc,0,0)
    assert rms(baseline)>100,(osc,'silent baseline')
    for mode in range(1,8):
        neutral=warp_audio(osc,mode,0)
        assert neutral==baseline,(osc,mode,'zero warp amount changes audio')
        altered=warp_audio(osc,mode,85)
        difference=rms([a-b for a,b in zip(baseline,altered)])
        assert difference>10,(osc,mode,'warp not audible',difference)
print('PASS: seven active warp modes plus Off, zero-amount neutrality on both oscillators')
# Instance limit and isolation.
insts=[api.create(b'.',None) for _ in range(7)]
assert all(insts) and not api.create(b'.',None)
for p in insts:api.destroy(p)
api.destroy(inst)
print('PASS: ABI, v1.9 chain_params/canvas contract, render, MIDI, polyphony, wavetable position, enum, state, clamp, limit')
print('Mono audio RMS:',round(rms(played),1))
print('Polyphony audio RMS:',round(rms(poly),1))


# Independent oscillator controls are exposed and bounded.
for k,hi in [('osc1_warp_type',7),('osc2_warp_type',7),('osc2_wavetable',107),('osc1_pan',100),('osc2_pan',100),('osc1_volume',100),('osc2_volume',100)]:
    setp(k,999)
    assert getp(k)==str(hi),(k,getp(k))
setp('osc1_warp_type',0);setp('osc1_warp',0);setp('osc1_volume',100)
setp('osc2_wavetable',24);setp('osc2_position',60);setp('osc2_warp_type',3);setp('osc2_warp',65);setp('osc2_volume',50)
assert getp('osc2_wavetable')=='24' and getp('osc2_warp_type')=='3'
print('PASS: independent dual oscillator controls and warp ranges')
# Both octave selectors preserve the default pitch at index 2.
for key in ('osc1_octave','osc2_octave'):
    param=next(p for p in chain_params if p['key']==key)
    assert param['options']==['-2','-1','0','+1','+2'] and param['default']==2
    setp(key,4);assert getp(key)=='4'
    setp(key,0);assert getp(key)=='0'
    setp(key,2);assert getp(key)=='2'
assert 'osc1_octave' in hierarchy['levels']['osc1']['knobs']
assert 'osc2_octave' in hierarchy['levels']['osc2']['knobs']
print('PASS: independent octave controls and neutral default')

