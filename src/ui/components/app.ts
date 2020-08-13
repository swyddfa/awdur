import { editor } from 'monaco-editor/esm/vs/editor/editor.api'
import { createEditor } from "../editor"
import { ipcRenderer } from 'electron'

export class AppMain extends HTMLElement {
  static readonly ELEMENT_NAME = 'app-main'
  private editor: editor.IStandaloneCodeEditor

  constructor() {
    super()
  }

  connectedCallback() {
    const welcome = document.createElement("welcome-screen")
    welcome.addEventListener("new-script", () => this.newScript())
    welcome.addEventListener("open-script", () => this.openScript())

    document.body.append(welcome)
  }



  newScript() {
    this.closeWelcomeScreen()
    this.editor = createEditor(document.body)
  }

  async openScript() {
    let fileContent = await ipcRenderer.invoke("file-open")
    this.closeWelcomeScreen()
    this.editor = createEditor(document.body, fileContent)
  }

  closeWelcomeScreen() {
    const welcome = document.querySelector("welcome-screen")
    if (welcome) {
      document.body.removeChild(welcome)
    }
  }
}
