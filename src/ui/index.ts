import { registerComponents } from "./components";
import { ScriptEditor } from "./editor";
import { ipcRenderer } from "electron";

interface FileOpenResult {
  canceled: boolean,
  filename: string,
  content: string
}

class Application {

  private container: HTMLElement
  private editor: ScriptEditor

  constructor(container: HTMLElement) {
    this.container = container
  }

  main() {
    const welcome = document.createElement("welcome-screen")
    this.container.append(welcome)

    // Initialise all event handlers
    this.container.addEventListener("new-script", () => this.newScript())
    this.container.addEventListener("open-script", () => this.openScript())
    this.container.addEventListener("save-script", () => this.saveScript())

    // And the event handlers from electron's main process.
    ipcRenderer.on("new-script", () => this.newScript())
    ipcRenderer.on("open-script", () => this.openScript())
    ipcRenderer.on("save-script", () => this.saveScript())
  }

  newScript() {
    this.initEditor()
  }

  async openScript() {
    let result: FileOpenResult = await ipcRenderer.invoke("file-open")
    if (result.canceled) {
      return
    }

    this.initEditor()
    this.editor.open(result)
  }

  async saveScript() {
    let content = this.editor.getScript()
    let result = await ipcRenderer.invoke("file-save", { filename: undefined, content: content })
    if (!result.success) {
      alert("Save failed!")
    }
  }

  private initEditor() {
    const welcome = this.container.querySelector('welcome-screen')
    if (welcome) {
      this.container.removeChild(welcome)
    }

    if (!this.editor) {
      this.editor = new ScriptEditor(this.container)
    }
  }
}

registerComponents()
let app = new Application(document.body)
app.main()
