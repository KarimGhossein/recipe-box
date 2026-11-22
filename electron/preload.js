'use strict';
// The only bridge between the page and the computer: storage, app info and fetching a recipe link.
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('rbNative', {
  kvGet: (key, shared) => ipcRenderer.invoke('kv:get', key, !!shared),
  kvSet: (key, value, shared) => ipcRenderer.invoke('kv:set', key, value, !!shared),
  kvDelete: (key, shared) => ipcRenderer.invoke('kv:delete', key, !!shared),
  kvList: (prefix, shared) => ipcRenderer.invoke('kv:list', prefix || '', !!shared),
  kvGetAll: (prefix, shared) => ipcRenderer.invoke('kv:getAll', prefix || '', !!shared),
  info: () => ipcRenderer.invoke('app:info'),
  fetchText: (url) => ipcRenderer.invoke('net:fetchText', url)
});
