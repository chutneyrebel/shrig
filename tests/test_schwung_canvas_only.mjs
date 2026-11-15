#!/usr/bin/env node
// Functional contract for a patched Schwung checkout. No Move required.
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
const root=process.argv[2];
if(!root) throw Error('Pass Schwung checkout path');
const {planPages,pageSlotKeys}=await import(pathToFileURL(resolve(root,'src/shared/param_pages/page_plan.mjs')).href);
const keys=['lfo_rate','lfo_depth','lfo_filter','cutoff','resonance','master_pan','level','osc2_volume'];
const make=(flag,extra=false,hidden=false)=>({
 hierarchy:{root:'root',levels:{root:{name:'Main',knobs:keys,params:[{key:'face',type:'canvas',as_page:true,page_first:true,...(flag?{replace_knob_grid:true}:{})},...(extra?['bonus']:[]),{level:'osc1'}]},osc1:{name:'OSC1',knobs:['osc1_level'],params:['osc1_level']}}},
 chainParams:[{key:'face',type:'canvas',as_page:true,page_first:true,name:'FACE',...(flag?{replace_knob_grid:true}:{})},...keys.map(key=>({key,type:'float'})),...(extra?[{key:'bonus',type:'float'}]:[]),{key:'osc1_level',type:'float'}],
 visible:hidden?{face:false}:undefined
});
function run(opts){return planPages({...make(...opts),trailingMenus:[]}).pages}
const baseline=run([false,false,false]);
const opted=run([true,false,false]);
const canvases=pages=>pages.filter(p=>p.canvas?.key==='face');
assert.equal(canvases(baseline).length,1,'baseline canvas present');
assert.equal(canvases(opted).length,1,'opt-in canvas present');
assert.deepEqual(pageSlotKeys(canvases(opted)[0]),keys,'FACE retains eight encoder keys');
const rootGrids=pages=>pages.filter(p=>p.level==='root'&&p.kind==='knobs'&&!p.canvas);
assert.ok(rootGrids(baseline).length>=1,'default keeps MAIN');
assert.equal(rootGrids(opted).length,0,'opt-in removes MAIN');
assert.ok(opted.some(p=>p.level==='osc1'),'child level preserved');
const overflow=run([true,true,false]);
assert.ok(overflow.some(p=>p.keys?.includes('bonus')),'overflow remains reachable');
console.log('Schwung functional planner tests passed');
