import { registerComponents } from "./components";
import './styles.css'

export abstract class Application {

  private container: HTMLElement
  private editor: ScriptEditor

  constructor(container: HTMLElement) {
    this.container = container
  }

  main() {
    registerComponents()

    const welcome = document.createElement("welcome-screen")
    this.container.append(welcome)

    // Initialise all event handlers
    this.container.addEventListener("new-script", () => this.newScript())
    //this.container.addEventListener("open-script", () => this.openScript())
    //this.container.addEventListener("save-script", () => this.saveScript())
  }

  newScript() {
    this.initEditor()
  }

  initEditor() {
    let welcome = this.container.querySelector("welcome-screen")
    if (welcome) {
      welcome.remove()
    }

    this.editor = new ScriptEditor(this.container);
  }
}