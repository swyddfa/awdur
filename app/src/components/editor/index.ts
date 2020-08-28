import * as monaco from 'monaco-editor/esm/vs/editor/editor.api';
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


function newEditor(container: HTMLElement) {

  let editor = monaco.editor.create(container, {
    value: '',
    language: 'fountain',
    lineNumbers: 'off',
    wordWrap: 'on',
    minimap: { enabled: false }
  })

  editor.addAction(new FileOpenAction())
  editor.addAction(new FileSaveAction())

  //@ts-ignore
  let resizer = new ResizeObserver(e => {
    let dimensions = e[0].contentRect
    editor.layout({ width: dimensions.width, height: dimensions.height })
  })
  resizer.observe(container)

  return editor
}

export class FountainEditor extends HTMLElement {
  static readonly ELEMENT_NAME = 'fountain-editor'

  private container: HTMLElement
  private editor: monaco.editor.ICodeEditor

  constructor() {
    super()
  }

  connectedCallback() {
    this.container = document.createElement("div")
    this.container.style.height = "100%";
    this.appendChild(this.container)

    this.editor = newEditor(this.container)
  }
}