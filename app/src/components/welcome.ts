import { html, render } from "lit-html";

let template = () => html`
<div class="h-screen grid place-center">
  <div class="bg-gray-100 p-10 rounded shadow-sm text-center">
    <h1 class="text-4xl">Awdur</h1>
    <button id="new" class="px-4 py-2 bg-gray-700 text-gray-200 rounded">New</button>
    <button id="open" class="px-4 py-2 bg-gray-700 text-gray-200 rounded">Open</button>
  </div>
</div>
`

export class WelcomeScreen extends HTMLElement {
  static readonly ELEMENT_NAME = 'welcome-screen'

  constructor() {
    super()
  }

  connectedCallback() {
    render(template(), this)

    const newScript = this.querySelector("#new");
    newScript.addEventListener("click", () => {
      this.parentElement.dispatchEvent(new CustomEvent("new-script"))
    })

    const openScript = this.querySelector("#open")
    openScript.addEventListener("click", () => {
      this.parentElement.dispatchEvent(new CustomEvent("open-script"))
    })
  }
}
