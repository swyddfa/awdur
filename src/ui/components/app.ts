import { editor } from 'monaco-editor/esm/vs/editor/editor.api'
import { createEditor } from "../editor"

export class AppMain extends HTMLElement {
  static readonly ELEMENT_NAME = 'app-main'
  private editor: editor.IStandaloneCodeEditor

  constructor() {
    super()
  }

  connectedCallback() {
    const welcome = document.createElement("welcome-screen")
    welcome.addEventListener("new-script", this.onNewScript.bind(this))
    welcome.addEventListener("open-script", this.onOpenScript.bind(this))

    document.body.append(welcome)
  }

  onNewScript() {
    const welcome = document.querySelector("welcome-screen")
    document.body.removeChild(welcome)
    this.editor = createEditor(document.body)
  }

  onOpenScript() {

  }
}
