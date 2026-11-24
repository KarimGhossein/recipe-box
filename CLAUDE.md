# Recipe Box: notes for Claude

A desktop recipe app built with Electron. The owner is a paramedic who also has some development background. Start every reply with "Sassafras", be concise, and push back on weak ideas with a fix.

## Layout
- `app/index.html` holds the whole UI, a single file with inline CSS and JS. There's no bundler; edit it directly.
- `electron/main.js` is the window, the menu, file storage over IPC (`kv:*`), and `net:fetchText`, which imports recipe links without CORS limits.
- `electron/preload.js` exposes `window.rbNative`. The page falls back to the old `server.py` API when it's missing.
- `tests/` has `data.test.js` (nutrition database checks) and `app.test.js` (launches the real app through Playwright's `_electron`).
- `tools/usda/` rebuilds `NUTRI_DB`, `NUTRI_SOURCE` and `NUTRI_MICRO` (vitamins and minerals) from USDA SR Legacy. Run `build_nutri_db.py`, then `apply.py`, which writes them into `app/index.html`. `tools/make_icon.py` draws `build/icon.png`.
- `.github/workflows/build.yml` runs the tests and builds the Mac `.dmg` and Windows installer on every push to `main`. It publishes a release when `package.json` `version` is new. Tag pushes are blocked from Claude sessions; the workflow creates the tag.

## Rules that matter
- Ingredient data is per 100 g, as a recipe measures it: meat, fish and produce raw; grains, pasta and lentils dry; beans canned or cooked. "cooked ..." entries cover grains measured after cooking. Don't hand-edit numbers; change `tools/usda/build_nutri_db.py` and rebuild.
- Structured ingredients are `{text, item, qty, unit, label, note}`. Keep `text` in sync (`composeIngText`), because scaling, the shopping list, search and the diet scans read it.
- Nutrition and diet tags are estimates. Say so; don't oversell them.
- Micronutrients: `null` means USDA didn't measure it (unknown), never 0. Recipe totals carry a per-nutrient coverage figure, and the label shows `≥` when under 90%. White rice is unenriched on purpose (as sold in Canada).
- Data lives in `<userData>/data/{personal,shared}/<quote(key)>.txt`. Never change that layout without a migration.
- Explanations live on the About page (`#aboutOverlay`, sections `about-<id>`). Elsewhere, link to it with `estCue('<id>')` instead of writing disclaimers into a section.
- Weight conversions: `WEIGHT_YIELD` turns purchase weight into what the database entry describes (bacon: USDA cooked values, 28 g raw slice → 9.1 g; mussels and clams in the shell). `COOK_RETENTION` applies USDA vitamin retention factors when a recipe has a cook time. Lines like "to taste" go to `unmeasured`, not `unmatched`, so they don't flag a recipe as incomplete.
- Shopping list: `shopName` cleans names, `fmtShopQty` adds compatible units then rounds up once. Rules are listed on the About page; keep the two in sync.
- Tools sit in the fixed right-side rail (`#rail`). Gluten-free mode is the `diet: 'Gluten free'` facet, shown with `paintGlutenFree()`: `body.gf-mode` swaps the palette variables to sage (registered with `@property` so they can animate), plus `.gf-wash` and `.gf-frame`. `body.gf-anim` is added for 3 s only while switching, so light/dark stays instant.
- Meals come from tags, or from a breakfast/snack/smoothie title. An untagged recipe gets no meal (shows under All only).
- Nutrition database panel: one Nutrition Facts form (`#dbFormSet`) for adding and editing. Values are typed per serving as printed and stored per 100 g, with the typed label kept in `data.label` so editing shows it again. Editing a built-in saves an override in `CUSTOM_DB`; deleting the override is "Reset to USDA". USDA lookup (`searchUsda`) shows matches; the pick loads into the form with portions from the detail endpoint. `fdcEnergy` takes kcal (FDC lists energy in kcal and kJ). `repairCustomDb()` fixes older lookups that stored kJ.
- Units: `unitsFor(item)` lists only units with a known weight; `volWeights` derives cup/tbsp/tsp from any one of them. An imported unit that doesn't fit stays visible but disabled and the row asks to choose a unit.

## Workflow
- `npm start` runs the app from source. Add `RECIPE_BOX_DATA_DIR=/tmp/x` to use a throwaway data folder.
- `npm test` runs everything. Use `xvfb-run -a npm test` on Linux without a display, and `--no-sandbox` if you're root (the tests already pass it).
- Before pushing, run `npm test`, then bump `version` in `package.json` if this should become a release.
