import { app, BrowserWindow, dialog, ipcMain } from "electron";
import * as chokidar from "chokidar";
import * as express from 'express';
import * as filesys from 'fs';
import * as path from 'path';

// Use the promise based fs api.
const fs = filesys.promises

const staticFiles = path.resolve(__dirname, "public")
const port = 3000

function startFileServer(): Promise<void> {
  let promise: Promise<void> = new Promise((resolve, reject) => {

    const app = express()
    app.use(express.static(staticFiles))

    app.listen(port, () => {
      console.log("Static file server listening")
      resolve(null)
    })
  })

  return promise
}

function createWindow() {

  const win = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      nodeIntegration: true,
      enableRemoteModule: false
    }
  })

  win.loadURL(`http://localhost:${port}`)

  // If we're developing, setup live reload of the browser window.
  console.log("env:", process.env.NODE_ENV)
  if (process.env.NODE_ENV !== 'production') {
    chokidar.watch(staticFiles).on('change', (evt, path) => {
      win.webContents.reload()
    })
  }

}
// -- Application lifecycle
app.whenReady().then(() => {
  startFileServer().then(() => {
    createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

// -- Frontend/Backend IPC
ipcMain.handle('file-open', async () => {
  let result = await dialog.showOpenDialog({ properties: ['openFile'] })
  let fileContent = await fs.readFile(result.filePaths[0], {})
  return fileContent.toString()
})