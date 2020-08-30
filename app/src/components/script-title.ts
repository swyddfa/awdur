import { LitElement, html, internalProperty, property } from "lit-element";


export class ScriptTitle extends LitElement {
  public static ELEMENT_NAME = "script-title"

  @internalProperty()
  private readOnly = true

  @property({ attribute: 'title', reflect: true })
  public scriptTitle: string

  createRenderRoot() {
    return this
  }

  handleChange(event) {
    this.saveTitle()
  }

  handleClick(event) {
    if (this.readOnly) {
      this.editTitle()
    } else {
      this.saveTitle()
    }
  }

  editTitle() {
    this.readOnly = false

    let input = this.querySelector("input")
    input.disabled = false
    input.focus()
    input.select()
  }

  saveTitle() {
    let input = this.querySelector('input')
    input.disabled = true

    this.readOnly = true
    this.scriptTitle = input.value
  }

  render() {
    return html`
      <div class="flex">
        <input type="text"
               class="bg-gray-900 disabled:bg-gray-700 text-center rounded" type="text"
               disabled
               .value="${this.scriptTitle}"
               @change="${this.handleChange}"/>

        <button class="bg-gray-600 rounded p-1 ml-2" @click="${this.handleClick}">
          <svg class="w-6 h-6 ${this.readOnly ? '' : 'hidden'}"
               fill="none"
               stroke="currentColor"
               stroke-width="2"
               stroke-linecap="round"
               stroke-linejoin="round">
            <path d="M17 3a2.828 2.828 0 114 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>
          </svg>
          <svg class="w-6 h-6 ${this.readOnly ? 'hidden' : ''}"
               fill="none"
               stroke="currentColor"
               stroke-width="2"
               stroke-linecap="round"
               stroke-linejoin="round">
            <path d="M20 6L9 17l-5-5"/>
          </svg>
        </button>
      </div>
    `
  }
}