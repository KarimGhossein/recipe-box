'use strict';
/*
 * Recipe Box — desktop app shell.
 * The UI is app/index.html. Recipes and custom ingredients are stored as one
 * text file per key under <userData>/data/{personal,shared}/, the same layout
 * the older folder version (server.py) used, so old data can be copied in.
 */
const { app, BrowserWindow, ipcMain, shell, Menu, dialog, nativeTheme, net } = require('electron');
const path = require('path');
const fs = require('fs');

const isMac = process.platform === 'darwin';
const DATA_DIR = process.env.RECIPE_BOX_DATA_DIR || path.join(app.getPath('userData'), 'data');
const WINDOW_STATE = path.join(app.getPath('userData'), 'window-state.json');

/* ---------------- storage ---------------- */
// Same encoding as Python's urllib.parse.quote(key, safe="") so filenames match the old version.
function quoteKey(key) {
  return encodeURIComponent(String(key)).replace(/[!'()*]/g, c => '%' + c.charCodeAt(0).toString(16).toUpperCase());
}
function unquoteKey(stem) {
  try { return decodeURIComponent(stem); } catch { return stem; }
}
function dirFor(shared) {
  const d = path.join(DATA_DIR, shared ? 'shared' : 'personal');
  fs.mkdirSync(d, { recursive: true });
  return d;
}
function fileFor(key, shared) {
  if (typeof key !== 'string' || !key) throw new Error('missing key');
  return path.join(dirFor(shared), quoteKey(key) + '.txt');
}
function writeAtomic(file, text) {
  const tmp = file + '.' + process.pid + '.tmp';
  fs.writeFileSync(tmp, text, 'utf8');
  fs.renameSync(tmp, file);               // never leaves a half-written recipe behind
}
function listFiles(shared) {
  return fs.readdirSync(dirFor(shared)).filter(f => f.endsWith('.txt')).sort();
}

ipcMain.handle('kv:get', (_e, key, shared) => {
  const f = fileFor(key, !!shared);
  if (!fs.existsSync(f)) return null;
  return { key, value: fs.readFileSync(f, 'utf8'), shared: !!shared };
});
ipcMain.handle('kv:set', (_e, key, value, shared) => {
  if (typeof value !== 'string') throw new Error('value must be a string');
  writeAtomic(fileFor(key, !!shared), value);
  return { key, value, shared: !!shared };
});
ipcMain.handle('kv:delete', (_e, key, shared) => {
  const f = fileFor(key, !!shared);
  if (fs.existsSync(f)) fs.unlinkSync(f);
  return { key, deleted: true, shared: !!shared };
});
ipcMain.handle('kv:list', (_e, prefix, shared) => {
  prefix = prefix || '';
  const keys = listFiles(!!shared).map(f => unquoteKey(f.slice(0, -4))).filter(k => k.startsWith(prefix));
  return { keys, prefix, shared: !!shared };
});
ipcMain.handle('kv:getAll', (_e, prefix, shared) => {
  prefix = prefix || '';
  const d = dirFor(!!shared);
  const items = [];
  for (const f of listFiles(!!shared)) {
    const k = unquoteKey(f.slice(0, -4));
    if (!k.startsWith(prefix)) continue;
    try { items.push({ key: k, value: fs.readFileSync(path.join(d, f), 'utf8') }); } catch { /* skip unreadable */ }
  }
  return { items, prefix, shared: !!shared };
});
ipcMain.handle('app:info', () => ({ dataDir: DATA_DIR, version: app.getVersion() }));

/* ---------------- recipe import from a link ---------------- */
// Fetched here (not in the page) so recipe sites can't block it with CORS.
ipcMain.handle('net:fetchText', async (_e, url) => {
  let u;
  try { u = new URL(String(url)); } catch { throw new Error('that doesn\'t look like a web address'); }
  if (!/^https?:$/.test(u.protocol)) throw new Error('only http and https links work');
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 20000);
  try {
    const res = await net.fetch(u.toString(), {
      signal: ctrl.signal,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml'
      }
    });
    if (!res.ok) throw new Error('the site answered ' + res.status);
    const text = await res.text();
    if (text.length > 15 * 1024 * 1024) throw new Error('that page is too large');
    return text;
  } catch (err) {
    if (err && err.name === 'AbortError') throw new Error('the site took too long to answer');
    throw err;
  } finally { clearTimeout(timer); }
});

/* ---------------- moving data over from the old folder version ---------------- */
async function importOldFolder(win) {
  const r = await dialog.showOpenDialog(win, {
    title: 'Choose your old Recipe Box folder',
    message: 'Pick the Recipe Box folder you used before (the one with server.py and a data folder inside).',
    properties: ['openDirectory']
  });
  if (r.canceled || !r.filePaths.length) return;
  const root = r.filePaths[0];
  const candidates = [path.join(root, 'data'), root];
  const src = candidates.find(d => fs.existsSync(path.join(d, 'personal')));
  if (!src) {
    await dialog.showMessageBox(win, { type: 'warning', message: 'No recipes found there', detail: 'That folder doesn\'t contain a "data/personal" folder. Choose the folder that has server.py in it.' });
    return;
  }
  let copied = 0, skipped = 0;
  for (const sub of ['personal', 'shared']) {
    const from = path.join(src, sub);
    if (!fs.existsSync(from)) continue;
    const to = dirFor(sub === 'shared');
    for (const f of fs.readdirSync(from)) {
      if (!f.endsWith('.txt')) continue;
      const dest = path.join(to, f);
      if (fs.existsSync(dest)) { skipped++; continue; }   // never overwrite what's already in the app
      fs.copyFileSync(path.join(from, f), dest);
      copied++;
    }
  }
  await dialog.showMessageBox(win, {
    type: 'info',
    message: copied ? `Imported ${copied} item${copied === 1 ? '' : 's'}` : 'Nothing new to import',
    detail: skipped ? `${skipped} already existed in the app and were left as they are.` : 'Your recipes are now saved inside the app.'
  });
  win.webContents.reload();
}

/* ---------------- window ---------------- */
function loadState() {
  try { return JSON.parse(fs.readFileSync(WINDOW_STATE, 'utf8')); } catch { return {}; }
}
function saveState(win) {
  if (win.isDestroyed()) return;
  const b = win.getNormalBounds();
  try { fs.writeFileSync(WINDOW_STATE, JSON.stringify({ ...b, maximized: win.isMaximized() })); } catch { /* not critical */ }
}

let mainWindow = null;
function createWindow() {
  const st = loadState();
  const win = new BrowserWindow({
    width: st.width || 1280, height: st.height || 860, x: st.x, y: st.y,
    minWidth: 380, minHeight: 500,
    title: 'Recipe Box',
    show: false,
    backgroundColor: nativeTheme.shouldUseDarkColors ? '#0E0C0B' : '#F4EFE4',
    titleBarStyle: isMac ? 'default' : undefined,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      spellcheck: true
    }
  });
  if (st.maximized) win.maximize();
  win.once('ready-to-show', () => win.show());
  win.on('close', () => saveState(win));

  // Links (recipe sources etc.) open in the normal browser, never inside the app.
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/i.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });
  win.webContents.on('will-navigate', (e, url) => {
    if (url !== win.webContents.getURL()) {
      e.preventDefault();
      if (/^https?:/i.test(url)) shell.openExternal(url);
    }
  });

  win.loadFile(path.join(__dirname, '..', 'app', 'index.html'));
  mainWindow = win;
  return win;
}

function buildMenu() {
  const template = [
    ...(isMac ? [{ role: 'appMenu' }] : []),
    {
      label: 'File',
      submenu: [
        { label: 'Import Recipes from Old Recipe Box Folder…', click: () => mainWindow && importOldFolder(mainWindow) },
        { label: 'Show Data Folder', click: () => { dirFor(false); shell.openPath(DATA_DIR); } },
        { type: 'separator' },
        { label: 'Print…', accelerator: 'CmdOrCtrl+P', click: () => mainWindow && mainWindow.webContents.print() },
        { type: 'separator' },
        isMac ? { role: 'close' } : { role: 'quit' }
      ]
    },
    { role: 'editMenu' },          // without this, copy/paste shortcuts don't work on macOS
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { type: 'separator' },
        { role: 'resetZoom' }, { role: 'zoomIn' }, { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
        ...(app.isPackaged ? [] : [{ role: 'toggleDevTools' }])
      ]
    },
    { role: 'windowMenu' }
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

/* ---------------- lifecycle ---------------- */
if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) { if (mainWindow.isMinimized()) mainWindow.restore(); mainWindow.focus(); }
  });
  app.whenReady().then(() => {
    fs.mkdirSync(DATA_DIR, { recursive: true });
    buildMenu();
    createWindow();
    app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
  });
  app.on('window-all-closed', () => { if (!isMac) app.quit(); });
}
