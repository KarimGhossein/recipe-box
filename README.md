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

- A **red** line means that ingredient isn't being counted. Pick a suggestion, or click **Add it** to put it in your own database (the USDA lookup there can fill in the numbers).
- Recipes imported with a published nutrition panel use those numbers until you change an ingredient. After that they're calculated from your ingredients, and you can switch back in the edit form.
- All nutrition is an estimate. The diet filters (gluten free, dairy free, nut free and so on) only read the ingredient list, so check labels if you have an allergy.

## Building

Every push to `main` builds both installers on GitHub (Actions tab). To publish a new release, bump `"version"` in `package.json` (for example to `2.0.1`) and push. The Releases page gets the new installers automatically.

To build locally, run `npm ci`, then `npm run dist:mac` (on a Mac) or `npm run dist:win`. Use `npm start` to run the app without packaging.
