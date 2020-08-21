import { ScriptEditor } from "../../app/src/editor";

export abstract class Application {

  private container: HTMLElement
  private editor: ScriptEditor

  constructor(container: HTMLElement) {
    this.container = container
  }

  main() {
    const welcome = document.createElement("welcome-screen")
    this.container.append(welcome)

    // Initialise all event handlers
    //this.container.addEventListener("new-script", () => this.newScript())
    //this.container.addEventListener("open-script", () => this.openScript())
    //this.container.addEventListener("save-script", () => this.saveScript())
  }
}
