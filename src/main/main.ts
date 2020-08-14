import { app, BrowserWindow, dialog, ipcMain, Menu } from "electron";
import * as chokidar from "chokidar";
import * as express from 'express';
import * as filesys from 'fs';
import * as path from 'path';

// Use the promise based fs api.
const fs = filesys.promises

const DEVLEOPMENT = process.env.NODE_ENV !== 'production'
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
  if (DEVLEOPMENT) {
    chokidar.watch(staticFiles).on('change', (evt, path) => {
      win.webContents.reload()
    })
  }

  const menu = Menu.buildFromTemplate([
    {
      label: 'File',
      submenu: [
        {
          label: 'New',
          accelerator: 'CmdOrCtrl+N',
          click() {
            win.webContents.send('new-script')
          }
        },
        {
          label: 'Open',
          accelerator: 'CmdOrCtrl+O',
          click() {
            win.webContents.send("open-script")
          }
        },
        {
          label: 'Save',
          accelerator: 'CmdOrCtrl+S',
          click() {
            win.webContents.send("save-script")
          }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          click() {
            app.quit()
          }
        }
      ]
    },
    ...(DEVLEOPMENT ? [
      {
        label: 'Develop',
        submenu: [
          {
            label: 'Open Developer Tools',
            click() {
              win.webContents.openDevTools()
            }
          }
        ]
      }
    ] : []),
    {
      label: 'About'
    }
  ])
  Menu.setApplicationMenu(menu)
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
  if (result.canceled) {
    return { canceled: true }
  }

  let filename = result.filePaths[0]
  let fileContent = await fs.readFile(filename, {})

  return {
    canceled: false,
    filename: filename,
    content: fileContent.toString()
  }
})

ipcMain.handle('file-save', async (event, args) => {
  let filename = args.filename

  if (!filename) {

    let result = await dialog.showSaveDialog({ properties: ['showOverwriteConfirmation'] })
    if (result.canceled) {
      return
    }

    filename = result.filePath
  }

  await fs.writeFile(filename, args.content)
  return { success: true }
})