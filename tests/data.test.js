// Sanity checks on the built-in nutrition database. Run: npm test
const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'app', 'index.html'), 'utf8');
function grab(name) {
  const m = html.match(new RegExp(`const ${name} = (\\{[\\s\\S]*?\\n?\\});`));
  if (!m) throw new Error(`${name} not found in app/index.html`);
  return Function(`"use strict"; return (${m[1]});`)();
}
const DB = grab('NUTRI_DB');
const SOURCE = grab('NUTRI_SOURCE');
const FIELDS = ['kcal', 'p', 'c', 'f', 'fib', 'sug', 'na', 'sf', 'chol', 'cup', 'tbsp', 'tsp', 'unit'];
// Foods whose energy doesn't follow 4-4-9 (alcohol, sugar alcohols, organic acids, rounding on tiny values)
const ENERGY_EXCEPTIONS = new Set(['white wine', 'red wine', 'beer', 'vanilla extract', 'stevia', 'balsamic vinegar',
  'rice vinegar', 'white vinegar', 'apple cider vinegar', 'red wine vinegar', 'lemon juice', 'lime juice', 'lemon', 'lime',
  'coffee', 'tea', 'cocoa powder', 'nutmeg', 'cloves', 'garam masala', 'mustard', 'dijon mustard', 'hot sauce', 'pickles',
  'capers', 'kimchi', 'sauerkraut', 'protein powder', 'fish sauce',
  // USDA's own measured energy differs from 4-4-9 for these (fillers, high-fibre spices)
  'baking powder', 'allspice', 'dried dill']);

test('every entry has every field as a non-negative number', () => {
  for (const [k, e] of Object.entries(DB)) {
    for (const f of FIELDS) assert.ok(typeof e[f] === 'number' && e[f] >= 0 && Number.isFinite(e[f]), `${k}.${f} = ${e[f]}`);
  }
});

test('every entry names its source', () => {
  for (const k of Object.keys(DB)) assert.ok(SOURCE[k], `${k} has no NUTRI_SOURCE entry`);
});

test('calories agree with protein, carbs and fat (4-4-9 rule, within 20%)', () => {
  const bad = [];
  for (const [k, e] of Object.entries(DB)) {
    if (ENERGY_EXCEPTIONS.has(k) || e.kcal < 40) continue;
    const est = 4 * e.p + 4 * (e.c - e.fib * 0.5) + 9 * e.f;   // fibre counts roughly half
    if (Math.abs(est - e.kcal) / e.kcal > 0.2) bad.push(`${k}: ${e.kcal} kcal vs ~${Math.round(est)} from macros`);
  }
  assert.deepStrictEqual(bad, []);
});

test('parts never exceed the whole', () => {
  const bad = [];
  for (const [k, e] of Object.entries(DB)) {
    if (e.sf > e.f + 0.5) bad.push(`${k}: sat fat ${e.sf} > fat ${e.f}`);
    if (e.sug > e.c + 0.5) bad.push(`${k}: sugar ${e.sug} > carbs ${e.c}`);
    if (e.fib > e.c + 0.5) bad.push(`${k}: fibre ${e.fib} > carbs ${e.c}`);
    if (e.p + e.c + e.f > 101) bad.push(`${k}: macros add up to more than 100 g`);
  }
  assert.deepStrictEqual(bad, []);
});

test('household measures are consistent (1 cup ≈ 16 tbsp, 1 tbsp ≈ 3 tsp)', () => {
  const bad = [];
  for (const [k, e] of Object.entries(DB)) {
    if (e.cup && e.tbsp && Math.abs(e.cup / e.tbsp - 16) > 16 * 0.35) bad.push(`${k}: cup ${e.cup} g vs tbsp ${e.tbsp} g`);
    if (e.tbsp && e.tsp && Math.abs(e.tbsp / e.tsp - 3) > 3 * 0.35) bad.push(`${k}: tbsp ${e.tbsp} g vs tsp ${e.tsp} g`);
  }
  assert.deepStrictEqual(bad, []);
});

test('grains are stored dry, with cooked versions available', () => {
  for (const k of ['white rice', 'brown rice', 'pasta', 'quinoa', 'lentils', 'couscous', 'barley']) {
    assert.ok(DB[k].kcal > 300, `${k} should be dry (got ${DB[k].kcal} kcal/100 g)`);
  }
  for (const k of ['cooked white rice', 'cooked brown rice', 'cooked pasta', 'cooked quinoa', 'cooked lentils']) {
    assert.ok(DB[k] && DB[k].kcal < 180, `${k} should exist and be cooked`);
  }
});

test('meat and fish are stored raw', () => {
  assert.strictEqual(DB['chicken breast'].kcal, 120);
  assert.ok(DB['salmon'].kcal < 220 && DB['egg'].kcal === 143);
});
