import { html, render } from "lit-html";

let template = () => html`
<style>
  .welcome {
    height: 100%;
    display: grid;
    place-items: center;
  }
  .content {
    padding: 2rem;
    background: white;
    border-radius: 5px;
    box-shadow: 2px 2px #ddd;
  }

  h1 {text-align: center}
  button {margin: 1em;}
</style>
<div class="welcome">
  <div class="content">
    <h1>Awdur</h1>
    <button id="new">New</button>
    <button id="open">Open</button>
  </div>
</div>
`

export class WelcomeScreen extends HTMLElement {
  static readonly ELEMENT_NAME = 'welcome-screen'

  constructor() {
    super()
  }

  connectedCallback() {
    const shadow = this.attachShadow({ mode: 'closed' })
    render(template(), shadow)

    const newScript = shadow.getElementById("new");
    newScript.addEventListener("click", () => {
      this.parentElement.dispatchEvent(new CustomEvent("new-script"))
    })

    const openScript = shadow.getElementById("open")
    openScript.addEventListener("click", () => {
      this.parentElement.dispatchEvent(new CustomEvent("open-script"))
    })
  }
}
