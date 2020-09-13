import { registerComponents } from "./components";
import { FountainEditor } from "./components/editor";
import './styles.css';
import { Script, ScriptAccess } from './services';
import { FileOpenModal } from "./components/file-open";

export class Application {

  private header: HTMLElement
  private appMain: HTMLElement
  private footer: HTMLElement

  private editor: FountainEditor

  constructor(private scriptAccess: ScriptAccess) {
    this.header = document.querySelector("header")
    this.appMain = document.querySelector("main")
    this.footer = document.querySelector("footer")

  }

  main() {
    registerComponents()

    const welcome = document.createElement("welcome-screen")
    welcome.addEventListener("new-script", () => this.newScript())
    welcome.addEventListener("open-script", () => this.openScript())
    this.appMain.appendChild(welcome)

  }

  async newScript() {
    let script: Script = { name: 'Untitled', content: '' }
    script = await this.scriptAccess.addScript(script)

    this.initEditor((editor: FountainEditor) => {
      editor.openScript(script)
    })
  }

  async openScript() {
    let modal = <FileOpenModal>document.createElement("file-open")
    modal.scriptAccess = this.scriptAccess
    modal.addEventListener('close', (event: CustomEvent) => this.handleModalClose(event, modal), { once: true })
    this.appMain.append(modal)
  }

  handleModalClose(event: CustomEvent, modal: FileOpenModal) {
    this.appMain.removeChild(modal)

    if (!event.detail || !event.detail.script) {
      return
    }

    let script: Script = event.detail.script
    this.initEditor((editor: FountainEditor) => {
      editor.openScript(script)
    })
  }

  async saveScript(event: CustomEvent) {
    let script = event.detail.script
    await this.scriptAccess.updateScript(script)
  }

  initEditor(onReady) {
    let welcome = this.appMain.querySelector("welcome-screen")
    if (welcome) {
      welcome.remove()
    }

    if (this.editor) {
      onReady(this.editor)
      return
    }

    this.editor = <FountainEditor>document.createElement("fountain-editor")
    this.editor.addEventListener('new-script', () => this.newScript())
    this.editor.addEventListener("save-script", (event: CustomEvent) => this.saveScript(event))
    this.editor.addEventListener("open-script", () => this.openScript())
    this.editor.addEventListener("ready", () => onReady(this.editor), { once: true })
    this.appMain.append(this.editor)
  }

}