#!/usr/bin/env node
// Apply a deliberately narrow, fail-closed Schwung page planner patch.
// Run against an upstream checkout: node scripts/patch_schwung_canvas_only.mjs /path/to/schwung
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = process.argv[2];
if (!root) throw Error('Pass the path to a Schwung checkout');
const file = resolve(root, 'src/shared/param_pages/page_plan.mjs');
let source = readFileSync(file, 'utf8');
const replacements = [
  [
    'pageFirst: p.page_first === true || p.pageFirst === true,',
    'pageFirst: p.page_first === true || p.pageFirst === true,\n            replaceKnobGrid: p.replace_knob_grid === true,',
  ],
  [
    '        for (const key of paramKeys(lvl)) {\n            const cp = canvasPages.get(key);\n            if (!cp || !cp.pageFirst) continue;\n            if (isHiddenParam(lvl, key, isVisible)) continue;\n            if (cp.presetBrowser && lvl.list_param && lvl.count_param) continue;\n            emitCanvasPage(cp, key);\n        }',
    '        let canvasReplacesGrid = false;\n        for (const key of paramKeys(lvl)) {\n            const cp = canvasPages.get(key);\n            if (!cp || !cp.pageFirst) continue;\n            if (isHiddenParam(lvl, key, isVisible)) continue;\n            if (cp.presetBrowser && lvl.list_param && lvl.count_param) continue;\n            emitCanvasPage(cp, key);\n            if (cp.replaceKnobGrid && authored.length > 0 && authored.length <= KNOBS_PER_PAGE) canvasReplacesGrid = true;\n        }',
  ],
  [
    '        if (parts.length > 0) {\n            for (const p of parts)',
    '        // Only suppress the duplicate authored grid when a single canvas\n        // already exposes every authored control. Never hide overflow pages.\n        if (canvasReplacesGrid && parts.length > 0 &&\n            parts[0].length === authored.length &&\n            parts[0].every((k, i) => k === authored[i])) {\n            parts.shift();\n        }\n        if (parts.length > 0) {\n            for (const p of parts)',
  ],
];
for (const [before, after] of replacements) {
  if (source.split(before).length !== 2) throw Error('Upstream planner changed: refusing unsafe patch at ' + before.slice(0, 60));
  source = source.replace(before, after);
}
writeFileSync(file, source);
console.log('Applied opt-in canvas-only planner patch. Run upstream tests before deployment.');
