import * as monaco from 'monaco-editor'
import { EXAMPLE_SCRIPT } from "./fountain";

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
    run: function (ed) {
      console.log('Opening file.')
    }
  })
}

export function createEditor(container: HTMLElement) {

  let editor = monaco.editor.create(container, {
    value: EXAMPLE_SCRIPT,
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