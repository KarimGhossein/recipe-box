# Recipe Box: notes for Claude

A desktop recipe app built with Electron. The owner is a paramedic who also has some development background. Start every reply with "Sassafras", be concise, and push back on weak ideas with a fix.

## Layout
- `app/index.html` holds the whole UI, a single file with inline CSS and JS. There's no bundler; edit it directly.
- `electron/main.js` is the window, the menu, file storage over IPC (`kv:*`), and `net:fetchText`, which imports recipe links without CORS limits.
- `electron/preload.js` exposes `window.rbNative`. The page falls back to the old `server.py` API when it's missing.
- `tests/` has `data.test.js` (nutrition database checks) and `app.test.js` (launches the real app through Playwright's `_electron`).
- `tools/usda/` rebuilds `NUTRI_DB` from USDA SR Legacy; see the docstring at the top of `build_nutri_db.py`. `tools/make_icon.py` draws `build/icon.png`.
- `.github/workflows/build.yml` runs the tests and builds the Mac `.dmg` and Windows installer on every push to `main`. It publishes a release when `package.json` `version` is new. Tag pushes are blocked from Claude sessions; the workflow creates the tag.

## Rules that matter
- Ingredient data is per 100 g, as a recipe measures it: meat, fish and produce raw; grains, pasta and lentils dry; beans canned or cooked. "cooked ..." entries cover grains measured after cooking. Don't hand-edit numbers; change `tools/usda/build_nutri_db.py` and rebuild.
- Structured ingredients are `{text, item, qty, unit, label, note}`. Keep `text` in sync (`composeIngText`), because scaling, the shopping list, search and the diet scans read it.
- Nutrition and diet tags are estimates. Say so; don't oversell them.
- Data lives in `<userData>/data/{personal,shared}/<quote(key)>.txt`. Never change that layout without a migration.

## Workflow
- `npm start` runs the app from source. Add `RECIPE_BOX_DATA_DIR=/tmp/x` to use a throwaway data folder.
- `npm test` runs everything. Use `xvfb-run -a npm test` on Linux without a display, and `--no-sandbox` if you're root (the tests already pass it).
- Before pushing, run `npm test`, then bump `version` in `package.json` if this should become a release.
