import { editor, KeyCode, KeyMod } from 'monaco-editor/esm/vs/editor/editor.api';
import { ipcRenderer } from "electron";

export class FileOpenAction implements editor.IActionDescriptor {
  id = 'awdur-file-open'
  label = 'Open File'

  keybindings = [
    KeyMod.CtrlCmd | KeyCode.KEY_O,
  ]

  async run(editor: editor.ICodeEditor, ...args: any[]): Promise<void> {
    let fileContent = await ipcRenderer.invoke('file-open')
    editor.setValue(fileContent)
  }
}

export class FileSaveAction implements editor.IActionDescriptor {
  id = 'awdur-file-save'
  label = 'Save'

  keybindings = [
    KeyMod.CtrlCmd | KeyCode.KEY_S
  ]

  async run(editor: editor.ICodeEditor, ...args: any[]): Promise<void> {
    let fileContent = editor.getValue()
    let result = await ipcRenderer.invoke('file-save', { filename: undefined, content: fileContent })
    if (!result.success) {
      alert("Save failed!")
    }
  }
}
