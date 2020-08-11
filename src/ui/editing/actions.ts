import * as monaco from 'monaco-editor';
import { ipcRenderer } from "electron";

export class FileOpenAction implements monaco.editor.IActionDescriptor {
  id = 'awdur-file-open'
  label = 'Open File'

  keybindings = [
    monaco.KeyMod.CtrlCmd | monaco.KeyCode.KEY_O,
  ]

  async run(editor: monaco.editor.ICodeEditor, ...args: any[]): Promise<void> {
    let fileContent = await ipcRenderer.invoke('file-open')
    editor.setValue(fileContent)
  }
}

export class FileSaveAction implements monaco.editor.IActionDescriptor {
  id = 'awdur-file-save'
  label = 'Save'

  keybindings = [
    monaco.KeyMod.CtrlCmd | monaco.KeyCode.KEY_S
  ]

  async run(editor: monaco.editor.ICodeEditor, ...args: any[]): Promise<void> {
    let fileContent = editor.getValue()
    let result = await ipcRenderer.invoke('file-save', { filename: undefined, content: fileContent })
    if (!result.success) {
      alert("Save failed!")
    }
  }
}
