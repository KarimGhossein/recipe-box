// End-to-end tests: launches the real desktop app (Electron) with a throwaway data folder.
// Run: npm test   (on Linux without a display: xvfb-run -a npm test)
const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { _electron: electron } = require('playwright');

const ROOT = path.join(__dirname, '..');
const DATA = fs.mkdtempSync(path.join(os.tmpdir(), 'recipe-box-test-'));
const PERSONAL = path.join(DATA, 'personal');
fs.mkdirSync(PERSONAL, { recursive: true });

// A recipe saved by the old folder version: plain-text ingredients, published nutrition panel.
const legacy = {
  id: 'legacy1', title: 'Old Format Chili', servings: 4, prep: 10, cook: 40, tags: ['Dinner'],
  ingredients: [{ text: '1 lb ground beef' }, { text: '2 cans kidney beans, drained' }, { text: '1 onion, diced' },
    { text: '2 tbsp chili powder' }, { text: '2 cups rice, cooked' }],
  steps: ['Cook.'], notes: '', source: 'https://example.com/chili',
  manualNutritionPerServing: { kcal: 410, p: 30, c: 35, f: 15, fib: 9, sug: 5, na: 700 }
};
fs.writeFileSync(path.join(PERSONAL, 'recipe%3Alegacy1.txt'), JSON.stringify(legacy));

let app, win;
const errors = [];
async function launch() {
  app = await electron.launch({
    executablePath: require('electron'),
    args: ['--no-sandbox', ROOT],
    env: { ...process.env, RECIPE_BOX_DATA_DIR: DATA },
    timeout: 60000
  });
  win = await app.firstWindow();
  win.on('pageerror', e => errors.push(String(e)));
  await win.waitForLoadState();
  await win.waitForFunction(() => typeof ALL_RECIPES !== 'undefined' && document.querySelector('#newRecipeBtn'));
  await win.waitForTimeout(500);
}
async function quit() {
  if (!app) return;
  const proc = app.process();
  await Promise.race([app.close(), new Promise(r => setTimeout(r, 5000))]);
  try { proc.kill('SIGKILL'); } catch {}
  app = null;
}
test.after(async () => { await quit(); fs.rmSync(DATA, { recursive: true, force: true }); });

test('app starts with the native bridge and loads old-format recipes', async () => {
  await launch();
  assert.strictEqual(await win.evaluate(() => window.__NATIVE__), true);
  assert.deepStrictEqual(await win.evaluate(() => ALL_RECIPES.map(r => r.title)), ['Old Format Chili']);
  const fonts = await win.evaluate(async () => { await document.fonts.ready; return [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family); });
  assert.ok(fonts.includes('Cormorant Garamond') && fonts.includes('Inter'), 'bundled fonts load offline: ' + fonts);
});

test('every recipe opens in the detail view', async () => {
  const ids = await win.evaluate(() => ALL_RECIPES.map(r => r.id));
  for (const id of ids) {
    await win.evaluate(id => document.querySelector(`article.card[data-id="${id}"]`).click(), id);
    await win.waitForTimeout(150);
    assert.ok(await win.evaluate(() => document.getElementById('detailOverlay').classList.contains('show')), `detail opens for ${id}`);
    await win.keyboard.press('Escape');
  }
});

test('old text lines convert to linked rows, including "rice, cooked"', async () => {
  const rows = await win.evaluate(() => { openForm(recipeById('legacy1')); return formIngs.map(r => [r.qty, r.unit, r.item, r.note]); });
  assert.deepStrictEqual(rows[0], [1, 'lb', 'ground beef', '']);
  assert.deepStrictEqual(rows[2], [1, '', 'onion', 'diced']);
  assert.strictEqual(rows[4][2], 'cooked white rice');
  // published nutrition stays until an ingredient changes
  assert.match(await win.innerText('#formEstimate'), /original recipe/);
  await win.fill('.ing-row[data-i="0"] .ing-qty', '2');
  assert.doesNotMatch(await win.innerText('#formEstimate'), /original recipe/);
  await win.keyboard.press('Escape');
});

test('nutrition maths: 100 g raw chicken breast + 1 cup dry white rice = 795 kcal', async () => {
  const n = await win.evaluate(() => computeNutritionRaw({ servings: 1, ingredients: [
    { text: '100 g chicken breast', item: 'chicken breast', qty: 100, unit: 'g', label: 'chicken breast', note: '' },
    { text: '1 cup white rice', item: 'white rice', qty: 1, unit: 'cup', label: 'white rice', note: '' }] }).perServing);
  assert.ok(Math.abs(n.kcal - (120 + 1.85 * 365)) < 1, `got ${n.kcal}`);
  assert.ok(Math.abs(n.p - (22.5 + 1.85 * 7.13)) < 0.1, `protein ${n.p}`);
});

test('new recipe through the ingredient editor saves as a file', async () => {
  await win.click('#newRecipeBtn');
  await win.waitForFunction(() => document.activeElement && document.activeElement.id === 'f-title');  // form focuses the title after opening
  await win.fill('#f-title', 'Test Omelette');
  await win.fill('#f-servings', '1');
  await win.fill('.ing-row[data-i="0"] .ing-qty', '3');
  await win.click('.ing-row[data-i="0"] .ing-name'); await win.keyboard.type('egg'); await win.waitForTimeout(150); await win.keyboard.press('Enter');
  await win.keyboard.type('beaten'); await win.keyboard.press('Enter');
  await win.fill('.ing-row[data-i="1"] .ing-qty', '30'); await win.selectOption('.ing-row[data-i="1"] .ing-unit', 'g');
  await win.click('.ing-row[data-i="1"] .ing-name'); await win.keyboard.type('chedd'); await win.waitForTimeout(150); await win.keyboard.press('Enter');
  await win.click('#recipeForm button[type=submit]');
  await win.waitForTimeout(500);
  const file = fs.readdirSync(PERSONAL).find(f => f.startsWith('recipe%3A') && f !== 'recipe%3Alegacy1.txt');
  assert.ok(file, 'recipe file written');
  const saved = JSON.parse(fs.readFileSync(path.join(PERSONAL, file), 'utf8'));
  assert.strictEqual(saved.ingredients[0].text, '3 Eggs, beaten');
  assert.strictEqual(saved.ingredients[1].item, 'cheddar cheese');
});

test('recipe view: database ingredients are capitalised tags, unknown ones stay plain text', async () => {
  await win.evaluate(() => openDetail(recipeById('legacy1')));
  const tags = await win.$$eval('#detailBody .ing-tag', els => els.map(e => e.textContent));
  assert.ok(tags.includes('Ground beef') && tags.includes('Onion'), 'tags: ' + tags);
  const notes = await win.$$eval('#detailBody .ing-note', els => els.map(e => e.textContent));
  assert.ok(notes.includes('diced'), 'note shown beside the tag');
  assert.strictEqual(await win.evaluate(() => displayName('dijon mustard')), 'Dijon mustard');
  assert.strictEqual(await win.evaluate(() => displayName('monterey jack cheese')), 'Monterey Jack cheese');
  await win.keyboard.press('Escape');
});

test('shopping list: add with amounts or ingredients only, and switch later', async () => {
  await win.evaluate(() => { SHOP = {items:[], checked:{}}; openDetail(recipeById('legacy1')); });
  await win.click('#detailBody [data-act="cart"]');
  await win.click('#detailBody [data-act="cart-names"]');
  let items = await win.evaluate(() => buildShoppingItems());
  assert.ok(items.length > 0 && items.every(i => i.qty === ''), 'names only: ' + JSON.stringify(items));
  assert.ok(items.some(i => i.name === 'Ground beef'), 'capitalised names');
  await win.evaluate(() => { SHOP.items[0].mode = 'amounts'; });
  items = await win.evaluate(() => buildShoppingItems());
  assert.ok(items.find(i => i.name === 'Ground beef').qty === '1 lb', JSON.stringify(items));
  await win.evaluate(() => { SHOP = {items:[], checked:{}}; saveShopping(); });
  await win.keyboard.press('Escape');
});

test('nutrition label: Canadian by default, US on request, rounded like real labels', async () => {
  await win.evaluate(() => { localStorage.removeItem('rb.labelStyle'); openDetail(ALL_RECIPES.find(r => r.title === 'Test Omelette')); });
  let txt = await win.innerText('.nutrition-label');
  assert.match(txt, /Fibre/); assert.match(txt, /Per 1 serving/); assert.doesNotMatch(txt, /Dietary Fiber/);
  const kcal = Number(await win.innerText('.nl-calories .val'));
  assert.strictEqual(kcal % 10, 0, 'calories rounded to 10');
  await win.click('[data-act="label-style"]');
  txt = await win.innerText('.nutrition-label');
  assert.match(txt, /Dietary Fiber/); assert.match(txt, /Total Carbohydrate/);
  assert.doesNotMatch(txt, /\d\.\d{2}/, 'no false precision');
  await win.click('[data-act="label-style"]');
  await win.keyboard.press('Escape');
});

test('label shows vitamins & minerals (Canada: potassium, calcium, iron; more on request)', async () => {
  await win.evaluate(() => openDetail(ALL_RECIPES.find(r => r.title === 'Test Omelette')));
  const top = await win.innerText('.nutrition-label');
  for (const n of ['Potassium', 'Calcium', 'Iron']) assert.match(top, new RegExp(n));
  // 3 eggs + 30 g cheddar: ~ 3*50*56/100 + 30*710/100 = 84 + 213 = ~297 mg calcium
  const ca = Number((top.match(/Calcium (?:≥ )?([\d.]+) mg/) || [])[1]);
  assert.ok(ca > 270 && ca < 320, `calcium ${ca}`);
  await win.click('.nl-more summary');
  const more = await win.innerText('.nl-more');
  for (const n of ['Vitamin D', 'Vitamin B12', 'Folate', 'Monounsaturated fat']) assert.match(more, new RegExp(n));
  await win.keyboard.press('Escape');
});

test('filters include the nutrition groups', async () => {
  await win.click('#filtersBtn'); await win.waitForTimeout(300);
  const groups = await win.evaluate(() => [...new Set([...document.querySelectorAll('.fchip-btn')].map(b => b.dataset.g))]);
  for (const g of ['diet', 'fibre', 'satfat', 'sodium']) assert.ok(groups.includes(g), `group ${g}`);
  await win.keyboard.press('Escape');
});

test('data survives a restart', async () => {
  await quit();
  await launch();
  const titles = await win.evaluate(() => ALL_RECIPES.map(r => r.title).sort());
  assert.deepStrictEqual(titles, ['Old Format Chili', 'Test Omelette']);
});

test('safety: links open outside the app and only web links can be fetched', async () => {
  const r = await win.evaluate(async () => { try { await rbNative.fetchText('file:///etc/passwd'); return 'fetched'; } catch (e) { return e.message; } });
  assert.match(r, /only http/);
  assert.strictEqual(errors.length, 0, 'no page errors: ' + errors.join(' | '));
});
