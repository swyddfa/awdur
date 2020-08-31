import * as monaco from 'monaco-editor/esm/vs/editor/editor.api';
import { LitElement, html } from "lit-element";
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
    console.log(e)
    let dimensions = e[0].contentRect
    console.log(dimensions)
    editor.layout({ width: dimensions.width, height: dimensions.height })
  })
  resizer.observe(container)

  return editor
}


export class FountainEditor extends LitElement {
  public static ELEMENT_NAME = 'fountain-editor'

  private toolbar: EditorToolbar
  private editor: monaco.editor.ICodeEditor

  createRenderRoot() {
    return this
  }

  render() {
    return html`
      <div class="h-full bg-white" data-ref="editor"></div>
    `
  }

  firstUpdated(changedProperties) {
    let container = <HTMLElement>this.querySelector('[data-ref="editor"]')
    this.editor = newEditor(container)
  }

}