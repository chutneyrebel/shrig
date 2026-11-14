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
function waveformLines(depth, nowMs) {
  const lines=[];
  overlay.drawPage({...ctx, line(...args){lines.push(args);}}, {nowMs, values:{wave:1,position:50,cutoff:40,lfo_depth:depth,lfo_rate:25}});
  return JSON.stringify(lines);
}
assert.equal(waveformLines(0,1000),waveformLines(0,1700));
assert.notEqual(waveformLines(80,1000),waveformLines(80,1700));
console.log('PASS: idle waveform stable; modulation produces time-dependent motion');
// Missing clock must not freeze a canvas on hosts without nowMs.
const withoutClockA=waveformLines(80,undefined);
let withoutClockB=withoutClockA;
for(let i=0;i<20;i++) withoutClockB=waveformLines(80,undefined);
assert.notEqual(withoutClockA,withoutClockB);
console.log('PASS: missing nowMs uses redraw-frame fallback');
console.log('PASS: canvas overlay loads and draws on the 128x64 hardware page contract');
