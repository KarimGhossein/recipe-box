# Recipe Box

A private recipe box for Mac and Windows: structured ingredients with live nutrition, diet and nutrition filters, a shopping list, printing, import from recipe links, and backups. Everything stays on your computer.

## Install

Download the latest installer from the **Releases** page:

- **Mac:** `Recipe-Box-<version>-Mac.dmg`. Open it and drag **Recipe Box** into **Applications**. It runs on both Apple Silicon and Intel Macs.
- **Windows:** `Recipe-Box-Setup-<version>.exe`. Run it and follow the setup wizard. It adds Start menu and desktop shortcuts.

### First launch (one time only)

The app isn't signed with a paid Apple or Microsoft certificate, so each system asks once:

- **Mac:** open Recipe Box from Applications. When macOS says it can't verify the app, click **Done**. Then go to **System Settings → Privacy & Security**, scroll down to the Recipe Box message, click **Open Anyway** and confirm. After that it opens normally.
- **Windows:** if SmartScreen says "Windows protected your PC", click **More info**, then **Run anyway**.

## Your data

Recipes and your own ingredients are saved as plain files on your computer. Use **File → Show Data Folder** to see them.

- Mac: `~/Library/Application Support/Recipe Box/data`
- Windows: `%APPDATA%\Recipe Box\data`

Uninstalling the app leaves your recipes where they are. Use **More → Backup** in the app for a single-file backup you can keep anywhere.

**Coming from the older folder version** (the one with `server.py`)? Choose **File → Import Recipes from Old Recipe Box Folder…** and pick that folder. Nothing already in the app is overwritten.

## Ingredients and nutrition

Each ingredient is a row: amount, unit, an ingredient linked to the nutrition database, and an optional note such as "diced". Nutrition updates as you type.

- **The database:** 421 ingredients from the USDA's SR Legacy database, stored the way recipes measure them. Meat, fish and produce are raw; grains, pasta and lentils are dry; beans are canned. There are separate "cooked rice", "cooked quinoa" and similar entries for grains measured after cooking. A handful of items USDA doesn't cover (oat milk, za'atar and so on) use typical label values and are marked as estimates in **More → Nutrition database**.
- **The label:** Canadian Nutrition Facts table by default, with a Canada/US switch on the label. Numbers are rounded the way real labels round them.
- **Uncounted ingredients:** a **red** line means that ingredient isn't being counted. Pick a suggestion, or click **Add it** to put it in your own database.
- **Published nutrition:** recipes imported with a published nutrition panel use those numbers until you change an ingredient. After that they're calculated from your ingredients, and you can switch back in the edit form.
- **Limits:** everything is an estimate. Shell weight isn't subtracted for mussels or clams, and the diet filters only read the ingredient list, so check labels if you have an allergy.

## Making changes

**Easiest way:** open this repo in Claude Code (on claude.ai/code, or the desktop app with the repo cloned) and describe the change. `CLAUDE.md` tells Claude how the project works, and the tests check the result before anything ships.

**By hand:**
1. Install [Node.js](https://nodejs.org) 22, then clone the repo and run `npm ci` once.
2. Run `npm start` to open the app from source. To keep your real recipes safe while experimenting, use a throwaway data folder: `RECIPE_BOX_DATA_DIR=~/rb-test npm start`.
3. Edit `app/index.html` (the whole interface) or `electron/main.js` (window, menu, storage). Press **Cmd+R** / **Ctrl+R** in the app to reload after editing the page. The menu has **View → Toggle Developer Tools** when you run from source.
4. Run `npm test`. It checks the nutrition database and drives the real app: creating, editing, saving and reopening recipes, the label, filters, and data surviving a restart.
5. Commit and push to `main`. GitHub runs the tests, then builds the installers. Bump `"version"` in `package.json` to publish a new release.

## Building

Every push to `main` builds both installers on GitHub (Actions tab). To publish a new release, bump `"version"` in `package.json` (for example to `2.0.1`) and push. The Releases page gets the new installers automatically.

To build locally, run `npm ci`, then `npm run dist:mac` (on a Mac) or `npm run dist:win`. Use `npm start` to run the app without packaging.
