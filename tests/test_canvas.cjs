// Host-side contract smoke test for Schwung's module-owned graphical page.
'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const code = fs.readFileSync('src/canvas.js', 'utf8');
const sandbox = {globalThis: {}};
vm.runInNewContext(code, sandbox, {timeout: 1000});
const overlay = sandbox.globalThis.canvas_overlay;
assert.equal(typeof overlay.drawPage, 'function');
let count = 0;
const ctx = {
  width: 128, height: 42,
  print(x,y,text,color) {
    assert(Number.isFinite(x) && Number.isFinite(y));
    assert(typeof text==='string');
    count++;
  },
  fillRect(x,y,w,h,color) {
    assert([x,y,w,h].every(Number.isFinite));
    assert(w>=0 && h>=0 && x>=0 && y>=0);
    count++;
  },
  line(x1,y1,x2,y2,color) {
    assert([x1,y1,x2,y2].every(Number.isFinite));
    count++;
  }
};
overlay.drawPage(ctx, {values:{wave:2,position:68,cutoff:30,lfo_depth:45,filter_env_amt:70,osc2_level:50}});
assert(count>25);
overlay.drawPage(ctx, {values:{}});
overlay.drawPage({ ...ctx, width: 25, height: 12 }, { values:{} });
// Modulation must visibly change the trace over time, while zero depth stays still.
function waveformLines(depth, nowMs, voices=0) {
  const lines=[];
  overlay.drawPage({...ctx, line(...args){lines.push(args);}}, {nowMs, values:{wave:1,position:50,cutoff:40,lfo_depth:depth,lfo_rate:25,voice_activity:voices}});
  return JSON.stringify(lines);
}
assert.equal(waveformLines(0,1000),waveformLines(0,1700));
assert.equal(waveformLines(80,1000,0),waveformLines(80,1700,0));
assert.notEqual(waveformLines(80,1000,1),waveformLines(80,1700,1));
console.log('PASS: idle waveform stable even at depth 80; sounding voices enable motion');
// Missing clock must not freeze a canvas on hosts without nowMs.
const withoutClockA=waveformLines(80,undefined,1);
let withoutClockB=withoutClockA;
for(let i=0;i<20;i++) withoutClockB=waveformLines(80,undefined,1);
assert.notEqual(withoutClockA,withoutClockB);
console.log('PASS: missing nowMs uses redraw-frame fallback');
// Schwung owns the parameter header. The canvas must never duplicate it.
const keys=['wave','position','osc2_level','detune','cutoff','resonance','lfo_depth','level'];
const vals={wave:2,position:63,osc2_level:41,detune:72,cutoff:30,resonance:25,lfo_depth:80,level:66};
for(let i=0;i<keys.length;i++){
  const printed=[];
  overlay.drawPage({...ctx,print(x,y,t,c){printed.push(t);}}, {keys,touched:i,values:vals,nowMs:1000});
  assert.deepEqual(printed,['C','M','E','O'],'canvas must not repeat host parameter header');
}
// Stage 2C: harmonic shimmer is absent while idle and at zero motion,
// but appears as sparse pixels when a voice sounds with sufficient motion.
function shimmerPixels(voices,depth,nowMs=1200){
  const pixels=[];
  overlay.drawPage({...ctx,fillRect(x,y,w,h,color){
    if(w===1 && h===1) pixels.push([x,y]);
  }},{nowMs,values:{wave:1,position:55,lfo_depth:depth,lfo_rate:30,voice_activity:voices}});
  return pixels;
}
assert.equal(shimmerPixels(0,80).length,0);
assert.equal(shimmerPixels(1,0).length,0);
assert.equal(shimmerPixels(1,14).length,0);
assert(shimmerPixels(1,80).length>15);
assert.notEqual(JSON.stringify(shimmerPixels(1,80,1000)),JSON.stringify(shimmerPixels(1,80,1800)));
console.log('PASS: sparse harmonic shimmer is note-gated and modulation-reactive');
console.log('PASS: no duplicate encoder feedback inside canvas');
console.log('PASS: canvas overlay loads and draws on the 128x64 hardware page contract');



function unifiedLines(table,shape=50){
 const lines=[];
 overlay.drawPage({...ctx,line(...args){lines.push(args);}}, {nowMs:1000,values:{wavetable:table,shape,position:50,voice_activity:0}});
 return JSON.stringify(lines);
}
assert.notEqual(unifiedLines(0),unifiedLines(4),'Classic and spectral waveforms differ');
assert.notEqual(unifiedLines(4),unifiedLines(40),'Spectral tables differ');
assert.notEqual(unifiedLines(40,0),unifiedLines(40,50),'Dark Shape changes waveform');
assert.notEqual(unifiedLines(40,50),unifiedLines(40,100),'Bright Shape changes waveform');
console.log('PASS: unified 52-table canvas and universal Shape');

const faces=sandbox.globalThis.sprig_faces;
assert.deepEqual(Object.keys(faces).sort(),['filter','main','osc1','osc2']);
for(const name of Object.keys(faces)){
  const lines=[];
  const labels=[];
  faces[name]({...ctx,line(...args){lines.push(args);},print(x,y,t){labels.push(t);}},{
    nowMs:1000,values:{wavetable:1,osc2_wavetable:24,position:30,osc2_position:80,cutoff:45,resonance:50,lfo_depth:60,voice_activity:1}
  });
  assert(lines.length>30, name+' face has no trace');
  assert.equal(labels.length,4,name+' face needs four meters');
}
const faceLines=(name)=>{const lines=[];faces[name]({...ctx,line(...args){lines.push(args);}},{
  nowMs:1000,values:{wavetable:1,osc2_wavetable:24,position:30,osc2_position:80,cutoff:45,resonance:50}
});return JSON.stringify(lines);};
assert.notEqual(faceLines('osc1'),faceLines('osc2'),'oscillator faces must be distinct');
assert.notEqual(faceLines('filter'),faceLines('osc1'),'filter must show response rather than oscillator wave');
console.log('PASS: four separate canvas face renderers produce distinct graphics');

// Regression: all curated core IDs must draw distinct physical Move traces.
function coreTrace(id, face='main') {
  const lines=[];
  const draw=face==='main'?overlay.drawPage:sandbox.globalThis.sprig_faces[face];
  draw({...ctx,line(...args){lines.push(args);}}, {nowMs:1000,values:{wavetable:id,osc2_wavetable:id,position:48,osc2_position:48,lfo_depth:0,voice_activity:0}});
  return JSON.stringify(lines);
}
const coreTraces=Array.from({length:8},(_,i)=>coreTrace(100+i));
assert.equal(new Set(coreTraces).size,8,'all eight core tables must have distinct native traces');
assert.notEqual(coreTrace(99),coreTrace(100),'ID 99 and core ID 100 must differ');
assert.notEqual(coreTrace(100,'osc1'),coreTrace(107,'osc1'));
console.log('PASS: native Move canvas renders all eight curated core wavetable IDs');

// Dedicated WT LFO must animate native waveforms independently of Motion Depth.
function wtLfoTrace(depth,nowMs,voices=1){
  const lines=[];
  overlay.drawPage({...ctx,line(...args){lines.push(args);}}, {
    nowMs,values:{wavetable:106,position:50,lfo_depth:0,lfo_wt_depth:depth,lfo_rate:15,voice_activity:voices}
  });
  return JSON.stringify(lines);
}
assert.equal(wtLfoTrace(0,1000),wtLfoTrace(0,1700));
assert.equal(wtLfoTrace(100,1000,0),wtLfoTrace(100,1700,0));
assert.notEqual(wtLfoTrace(100,1000),wtLfoTrace(100,1700));
console.log('PASS: dedicated WT LFO animates physical waveform only while sounding');

// All curated IDs must render on both oscillator faces across WT positions.
// This catches partial fixes where the main face works but OSC2 is still clamped.
for(const face of ['main','osc1','osc2']){
  for(const position of [0,33,67,100]){
    const traces=[];
    for(let id=100;id<=107;id++){
      const lines=[];
      const draw=face==='main'?overlay.drawPage:sandbox.globalThis.sprig_faces[face];
      draw({...ctx,line(...args){lines.push(args);}}, {
        nowMs:1000,values:{wavetable:id,osc2_wavetable:id,position,osc2_position:position,lfo_depth:0,lfo_wt_depth:0,voice_activity:0}
      });
      assert(lines.length>30,face+' failed to render '+id+' at '+position);
      traces.push(JSON.stringify(lines));
    }
    assert.equal(new Set(traces).size,8,face+' has indistinguishable curated traces at '+position);
  }
}
console.log('PASS: all eight curated waveforms render distinctly on main, OSC1 and OSC2 at four positions');

const named=sandbox.globalThis.canvas_overlays;
assert.deepEqual(Object.keys(named).sort(),['sprig_filter','sprig_main','sprig_osc1','sprig_osc2']);
for(const [name,entry] of Object.entries(named)){
  assert.equal(typeof entry.drawPage,'function',name+' must provide drawPage');
  const lines=[];
  entry.drawPage({...ctx,line(...args){lines.push(args);}}, {
    nowMs:1000,values:{wavetable:106,osc2_wavetable:107,position:60,osc2_position:40,voice_activity:0}
  });
  assert(lines.length>0,name+' must draw waveform or filter response');
}
console.log('PASS: four named native overlay entry points render without changing legacy overlay');
