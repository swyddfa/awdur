import * as monaco from 'monaco-editor/esm/vs/editor/editor.api';
import { html, render } from "lit-html";
import { FileOpenAction, FileSaveAction } from './actions';
import { registerFountainLang } from './fountain';
import { EditorToolbar } from '../editor-toolbar';

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

let template = () => html`
<div class="flex flex-col h-screen overflow-hidden">
  <editor-toolbar data-ref="toolbar"></editor-toolbar>
  <div class="flex-grow p-1 bg-white" data-ref="editor"></div>
  <footer>
    <span></span>
  </footer>
</div>
`

export class FountainEditor extends HTMLElement {
  static readonly ELEMENT_NAME = 'fountain-editor'

  private container: HTMLElement
  private toolbar: EditorToolbar
  private editor: monaco.editor.ICodeEditor

  constructor() {
    super()
  }

  connectedCallback() {
    render(template(), this)

    let editorContainer = <HTMLElement>this.querySelector('[data-ref="editor"]')
    this.editor = newEditor(editorContainer)

    this.toolbar = this.querySelector('[data-ref="toolbar"]')
  }
}