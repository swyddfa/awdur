import { registerComponents } from "./components";
import { FountainEditor } from "./components/editor";
import { EditorToolbar } from "./components/editor-toolbar";
import './styles.css';

export abstract class Application {

  private header: HTMLElement
  private appMain: HTMLElement
  private footer: HTMLElement

  private toolbar: EditorToolbar
  private editor: FountainEditor

  constructor() {
    this.header = document.querySelector("header")
    this.appMain = document.querySelector("main")
    this.footer = document.querySelector("footer")

    this.toolbar = document.querySelector("editor-toolbar")
  }

  main() {
    registerComponents()

    const welcome = document.createElement("welcome-screen")
    this.appMain.appendChild(welcome)
    this.appMain.addEventListener("new-script", () => this.newScript())

    // Initialise all event handlers
    //this.container.addEventListener("open-script", () => this.openScript())
    //this.container.addEventListener("save-script", () => this.saveScript())
  }

  newScript() {
    console.log("app: new script")
    this.initEditor()
    this.toolbar.setAttribute("show", "true")
    this.toolbar.scriptTitle = "Untitled"
  }

  initEditor() {
    let welcome = this.appMain.querySelector("welcome-screen")
    if (welcome) {
      welcome.remove()
    }

    this.editor = <FountainEditor>document.createElement("fountain-editor")
    this.appMain.append(this.editor)

  }
}