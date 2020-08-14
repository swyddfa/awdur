import { registerComponents } from "./components";
import { ScriptEditor } from "./editor";
import { ipcRenderer } from "electron";

interface FileOpenResult {
  canceled: boolean,
  filename: string,
  content: string
}

interface FileSaveResult {
  success: boolean,
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
    this.container.addEventListener("title", (event: CustomEvent) => this.setTitle(event.detail))

    // And the event handlers from electron's main process.
    ipcRenderer.on("new-script", () => this.newScript())
    ipcRenderer.on("open-script", () => this.openScript())
    ipcRenderer.on("save-script", () => this.saveScript())
  }

  newScript() {
    this.initEditor()
    let script = { filename: 'Untitled', content: '' }
    this.editor.open(script)
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
    let script = this.editor.getActiveScript()
    if (!script) {
      return
    }

    if (script.filename.match(/Untitled.*/)) {
      script.filename = undefined
    }

    let result: FileSaveResult = await ipcRenderer.invoke("file-save", script)
    if (!result.success) {
      alert("Save failed!")
    }

    this.editor.open(result)
  }

  setTitle(path: string) {
    document.title = `${path} - Awdur`
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
