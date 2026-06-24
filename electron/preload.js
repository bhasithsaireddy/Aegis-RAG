const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to the renderer
contextBridge.exposeInMainWorld('electron', {
  // File dialogs
  openFile: () => ipcRenderer.invoke('dialog:openFile'),
  openFolder: () => ipcRenderer.invoke('dialog:openFolder'),

  // App info
  getAppInfo: () => ipcRenderer.invoke('app:getInfo'),

  // Platform check
  platform: process.platform,
});

// Expose API URL
contextBridge.exposeInMainWorld('api', {
  baseUrl: 'http://127.0.0.1:8000',

  // Helper for API calls
  async fetch(endpoint, options = {}) {
    const url = `http://127.0.0.1:8000${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    return response;
  },

  // Health check
  async checkHealth() {
    try {
      const response = await fetch('http://127.0.0.1:8000/health');
      return response.ok;
    } catch {
      return false;
    }
  }
});
