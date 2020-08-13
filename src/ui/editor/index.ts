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

export function createEditor(container: HTMLElement) {

  let scriptEditor = editor.create(container, {
    value: '',
    language: 'fountain',
    lineNumbers: "off",
    wordWrap: 'on',
    minimap: { enabled: false }
  })


  scriptEditor.addAction(new FileOpenAction())
  scriptEditor.addAction(new FileSaveAction())

  //@ts-ignore
  let resizer = new ResizeObserver(e => {
    let dims = e[0].contentRect
    scriptEditor.layout({ width: dims.width, height: dims.height })
  })
  resizer.observe(container)


  return scriptEditor
}