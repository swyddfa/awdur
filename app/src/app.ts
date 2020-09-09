import { registerComponents } from "./components";
import { FountainEditor } from "./components/editor";
import './styles.css';
import { Script, ScriptAccess } from './services';

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

    this.editor = <FountainEditor>document.createElement("fountain-editor")
    this.editor.addEventListener("save-script", (event: CustomEvent) => this.saveScript(event))
    this.editor.addEventListener("ready", () => onReady(this.editor), { once: true })
    this.appMain.append(this.editor)
  }
}
