import { LitElement, html } from "lit-element";


export class WelcomeScreen extends LitElement {
  public static ELEMENT_NAME = 'welcome-screen'

  createRenderRoot() {
    return this
  }

  newScript() {
    this.dispatchEvent(new CustomEvent("new-script"))
  }

  openScript() {
    this.dispatchEvent(new CustomEvent("open-script"))
  }

  render() {
    return html`
      <div class="h-full grid place-center bg-gray-200">
        <div class="bg-white p-10 rounded shadow-sm text-center">
          <h1 class="text-4xl">Awdur</h1>
          <button class="px-4 py-2 bg-gray-700 text-gray-200 rounded"
                  @click=${this.newScript}>
            New
          </button>
          <button class="px-4 py-2 bg-gray-700 text-gray-200 rounded"
                  @click="${this.openScript}">
            Open
          </button>
        </div>
      </div>
`

  }
}
