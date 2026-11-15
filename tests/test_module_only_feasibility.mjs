#!/usr/bin/env node
// Prove whether Schwung's unmodified planner can provide a canvas-only FACE
// while preserving the same eight root encoders. No firmware changes.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
const root=process.argv[2], modulePath=process.argv[3];
if(!root||!modulePath)throw Error('Usage: node test_module_only_feasibility.mjs <schwung> <module.json>');
const {planPages,pageSlotKeys}=await import(pathToFileURL(resolve(root,'src/shared/param_pages/page_plan.mjs')).href);
const mod=JSON.parse(readFileSync(modulePath,'utf8'));
const original=mod.capabilities.ui_hierarchy;
const chainParams=mod.capabilities.chain_params;
const copy=()=>JSON.parse(JSON.stringify(original));
const analyze=(hierarchy)=>{const pages=planPages({hierarchy,chainParams}).pages;const face=pages.find(p=>p.canvas?.key==='face');const main=pages.filter(p=>p.level==='root'&&p.kind==='knobs'&&!p.canvas);return {face:face? pageSlotKeys(face):[],main:main.length}};
const baseline=analyze(copy());
const noRoot=copy();delete noRoot.levels.root.knobs;
const stripped=analyze(noRoot);
assert.equal(baseline.face.filter(Boolean).length,8,'baseline FACE has eight controls');
assert.ok(baseline.main>0,'upstream emits redundant MAIN');
assert.equal(stripped.main,0,'removing root knobs removes MAIN');
assert.equal(stripped.face.filter(Boolean).length,0,'but also removes FACE encoder bindings');
console.log(JSON.stringify({baseline,withoutRootKnobs:stripped},null,2));
console.log('Result: deleting root knobs is NOT a safe module-only fix.');
