import { editor } from 'monaco-editor/esm/vs/editor/editor.api';
import { FileOpenAction, FileSaveAction } from './actions';
import { registerFountainLang } from './fountain';

registerFountainLang()

// @ts-ignore
self.MonacoEnvironment = {
  getWorkerUrl: function (moduleId, label) {
    return "./editor.worker.bundle.js"
  }
}

export interface ScriptFile {
  filename: string,
  content: string
}

export class ScriptEditor {

  private editor: editor.IStandaloneCodeEditor

  constructor(container: HTMLElement) {
    let edit = editor.create(container, {
      value: '',
      language: 'fountain',
      lineNumbers: 'off',
      wordWrap: 'on',
      minimap: { enabled: false }
    })

    edit.addAction(new FileOpenAction())
    edit.addAction(new FileSaveAction())

    //@ts-ignore
    let resizer = new ResizeObserver(e => {
      let dimensions = e[0].contentRect
      edit.layout({ width: dimensions.width, height: dimensions.height })
    })
    resizer.observe(container)

    this.editor = edit
  }

  open(result: ScriptFile) {
    this.editor.setValue(result.content)
  }

  getScript(): string {
    return this.editor.getValue()
  }

}
