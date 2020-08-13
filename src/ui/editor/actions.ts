import { editor, KeyCode, KeyMod } from 'monaco-editor/esm/vs/editor/editor.api';
import { ipcRenderer } from "electron";

export class FileOpenAction implements editor.IActionDescriptor {
  id = 'awdur-file-open'
  label = 'Open File'

  keybindings = [
    KeyMod.CtrlCmd | KeyCode.KEY_O,
  ]

  run(editor: editor.ICodeEditor, ...args: any[]) {
    let container = editor.getContainerDomNode()
    container.dispatchEvent(new CustomEvent("open-script"))
  }
}

export class FileSaveAction implements editor.IActionDescriptor {
  id = 'awdur-file-save'
  label = 'Save'

  keybindings = [
    KeyMod.CtrlCmd | KeyCode.KEY_S
  ]

  run(editor: editor.ICodeEditor, ...args: any[]) {
    let container = editor.getContainerDomNode()
    container.dispatchEvent(new CustomEvent("save-script"))
  }
}
