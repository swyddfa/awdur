import * as monaco from 'monaco-editor/esm/vs/editor/editor.api';

export class FileOpenAction implements monaco.editor.IActionDescriptor {
  id = 'awdur-file-open'
  label = 'Open File'

  keybindings = [
    monaco.KeyMod.CtrlCmd | monaco.KeyCode.KEY_O,
  ]

  run(editor: monaco.editor.ICodeEditor, ...args: any[]) {
    let container = editor.getContainerDomNode()
    container.dispatchEvent(new CustomEvent("open-script"))
  }
}

export class FileSaveAction implements monaco.editor.IActionDescriptor {
  id = 'awdur-file-save'
  label = 'Save'

  keybindings = [
    monaco.KeyMod.CtrlCmd | monaco.KeyCode.KEY_S
  ]

  run(editor: monaco.editor.ICodeEditor, ...args: any[]) {
    let container = editor.getContainerDomNode()
    container.dispatchEvent(new CustomEvent("save-script"))
  }
}
