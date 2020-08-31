import { LitElement, html } from "lit-element";

const VERSION = "0.1.0-beta.1"

export class Version extends LitElement {
  public static ELEMENT_NAME = "app-version"

  createRenderRoot() {
    return this
  }

  render() {
    return html`<div>v${VERSION}</div>`
  }
}