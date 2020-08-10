import * as monaco from 'monaco-editor'
import { ipcRenderer } from "electron";

// @ts-ignore
self.MonacoEnvironment = {
  getWorkerUrl: function (moduleId, label) {
    return "./editor.worker.bundle.js"
  }
}

function registerCommands(editor: monaco.editor.IStandaloneCodeEditor) {
  editor.addAction({
    id: 'awdur-file-open',
    label: 'Open File',
    keybindings: [
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.KEY_O
    ],
    run: async function (ed) {
      let fileContent = await ipcRenderer.invoke('file-open')
      ed.setValue(fileContent)
    }
  })
}

export function createEditor(container: HTMLElement) {

  let editor = monaco.editor.create(container, {
    value: '',
    language: 'fountain',
    lineNumbers: "off",
    wordWrap: 'on',
    minimap: { enabled: false }
  })

  //@ts-ignore
  let resizer = new ResizeObserver(e => {
    let dims = e[0].contentRect
    editor.layout({ width: dims.width, height: dims.height })
  })
  resizer.observe(container)
  registerCommands(editor)

  return editor
}