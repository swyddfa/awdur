import * as idb from 'idb'
import { registerComponents } from "./components";
import { FountainEditor } from "./components/editor";
import { EditorToolbar } from "./components/editor-toolbar";
import './styles.css';
import { Script, ScriptAccess } from './services';

export class Application {

  private header: HTMLElement
  private appMain: HTMLElement
  private footer: HTMLElement

  private toolbar: EditorToolbar
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

  newScript() {
    this.initEditor()
    this.editor.newScript()
  }

  openScript() {
    const modal = document.createElement("file-open")
    this.appMain.append(modal)
  }

  async saveScript(event: CustomEvent) {
    let script = event.detail.script

    if (!script.id) {
      await this.scriptAccess.addScript(script)
      return
    }

    await this.scriptAccess.updateScript(script)
  }

  initEditor() {
    let welcome = this.appMain.querySelector("welcome-screen")
    if (welcome) {
      welcome.remove()
    }

    this.editor = <FountainEditor>document.createElement("fountain-editor")
    this.editor.addEventListener("save-script", (event: CustomEvent) => this.saveScript(event))
    this.appMain.append(this.editor)
  }
}