import { html, render } from "lit-html";
import { registerComponents } from "./components";
import { FountainEditor } from "./components/editor";
import { EditorToolbar } from "./components/editor-toolbar";
import './styles.css';

let template = () => html`
<div class="flex flex-col h-screen overflow-hidden">
  <header>
    <editor-toolbar></editor-toolbar>
  </header>
  <main class="flex-grow p-1 bg-white">
    <fountain-editor></fountain-editor>
  </main>
  <footer>
    <span></span>
  </footer>
</div>
`

export abstract class Application {

  private container: HTMLElement
  private toolbar: EditorToolbar
  private editor: FountainEditor

  constructor(container: HTMLElement) {
    this.container = container
  }

  main() {
    registerComponents()

    const welcome = document.createElement("welcome-screen")
    this.container.append(welcome)

    // Initialise all event handlers
    document.body.addEventListener("title-changed", (event: CustomEvent) => this.changeTitle(event))
    document.body.addEventListener("new-script", () => this.newScript())
    //this.container.addEventListener("open-script", () => this.openScript())
    //this.container.addEventListener("save-script", () => this.saveScript())
  }

  newScript() {
    this.initEditor()
  }

  changeTitle(event: CustomEvent) {
    let title = event.detail.title
    document.title = `${title} - Awdur`
  }

  initEditor() {
    let welcome = this.container.querySelector("welcome-screen")
    if (welcome) {
      welcome.remove()
    }

    render(template(), this.container)
  }
}