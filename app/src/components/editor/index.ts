import * as monaco from 'monaco-editor/esm/vs/editor/editor.api';
import { LitElement, html, property, PropertyValues } from "lit-element";
import { FileOpenAction, FileSaveAction } from './actions';
import { registerFountainLang } from './fountain';
import { EditorToolbar } from '../editor-toolbar';
import { Script } from '../../services';

registerFountainLang()

// @ts-ignore
self.MonacoEnvironment = {
  getWorkerUrl: function (moduleId, label) {
    return "./editor.worker.js"
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


export class FountainEditor extends LitElement {
  public static ELEMENT_NAME = 'fountain-editor'

  private toolbar: EditorToolbar
  private editor: monaco.editor.ICodeEditor

  private currentScript: Script

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

    this.toolbar = document.querySelector("editor-toolbar")
    this.toolbar.setAttribute("show", "true")
    this.toolbar.addEventListener('save-script', () => this.saveScript())
    this.dispatchEvent(new CustomEvent('ready'))
  }

  openScript(script: Script) {
    this.currentScript = script
    this.toolbar.scriptTitle = script.name
    this.editor.setValue(script.content)
  }

  saveScript() {
    this.currentScript.content = this.editor.getValue()
    this.currentScript.name = this.toolbar.scriptTitle

    this.dispatchEvent(new CustomEvent('save-script', { detail: { script: this.currentScript } }))
  }

}