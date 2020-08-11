import * as monaco from 'monaco-editor';
import { FileOpenAction, FileSaveAction } from './editing/actions';

// @ts-ignore
self.MonacoEnvironment = {
  getWorkerUrl: function (moduleId, label) {
    return "./editor.worker.bundle.js"
  }
}

export function createEditor(container: HTMLElement) {

  let editor = monaco.editor.create(container, {
    value: '',
    language: 'fountain',
    lineNumbers: "off",
    wordWrap: 'on',
    minimap: { enabled: false }
  })


  editor.addAction(new FileOpenAction())
  editor.addAction(new FileSaveAction())
  console.log(editor.getModel())

  //@ts-ignore
  let resizer = new ResizeObserver(e => {
    let dims = e[0].contentRect
    editor.layout({ width: dims.width, height: dims.height })
  })
  resizer.observe(container)


  return editor
}