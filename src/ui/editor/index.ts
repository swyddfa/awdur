import { editor, Uri } from 'monaco-editor/esm/vs/editor/editor.api';
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
  private scripts: Map<string, editor.ITextModel>

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
    this.scripts = new Map();
  }

  open(file: ScriptFile) {

    if (this.scripts.has(file.filename)) {
      let script = this.scripts.get(file.filename)
      script.setValue(file.content)
      this.editor.setModel(script)

      return
    }

    let script = editor.createModel(file.content, 'fountain', Uri.parse(file.filename))
    this.scripts.set(file.filename, script)
    this.editor.setModel(script)
  }

  getActiveScript(): ScriptFile | undefined {
    let script = this.editor.getModel();
    if (!script) {
      return
    }

    return {
      filename: script.uri.path,
      content: script.getValue()
    }
  }

  getScript(filename: string): ScriptFile | undefined {
    if (!this.scripts.has(filename)) {
      return
    }

    let script = this.scripts.get(filename)
    return {
      filename: script.uri.path,
      content: script.getValue()
    }

  }

}
