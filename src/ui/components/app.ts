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
    document.body.addEventListener("new-script", () => this.newScript())
    document.body.addEventListener("open-script", () => this.openScript())
    document.body.addEventListener("save-script", () => this.saveScript())
  }

  newScript() {
    this.closeWelcomeScreen()
    let editor = this.getOrCreateEditor()
  }

  async openScript() {
    let result = await ipcRenderer.invoke("file-open")
    if (result.canceled) {
      return
    }

    this.closeWelcomeScreen()
    this.editor = this.getOrCreateEditor()
    this.editor.setValue(result.content)
  }

  async saveScript() {
    let content = this.editor.getValue()
    let result = await ipcRenderer.invoke("file-save", { filname: undefined, content: content })
    if (!result.success) {
      alert("Save failed!")
    }
  }

  closeWelcomeScreen() {
    const welcome = document.querySelector("welcome-screen")
    if (welcome) {
      document.body.removeChild(welcome)
    }
  }

  getOrCreateEditor(): editor.IStandaloneCodeEditor {
    if (this.editor) {
      return this.editor
    }

    this.editor = createEditor(document.body)
    return this.editor
  }
}
