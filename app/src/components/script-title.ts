import { LitElement, html, internalProperty, property } from "lit-element";
import { Icon } from "./icon";


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

    this.dispatchEvent(new CustomEvent('rename', { detail: { title: input.value } }))
  }

  render() {
    return html`
      <div class="flex">
        <input type="text"
               class="bg-gray-900 disabled:bg-gray-700 text-center rounded" type="text"
               disabled
               .value="${this.scriptTitle}"
               @change="${this.handleChange}"/>

        <button class="rounded leading-none p-1 ml-2" @click="${this.handleClick}">
          <x-icon name="${Icon.PENCIL}" class="inline-block w-6 h-6 ${this.readOnly ? '' : 'hidden'}"></x-icon>
          <x-icon name="${Icon.CHECK}" class=" inline-block w-6 h-6 ${this.readOnly ? 'hidden' : ''}"></x-icon>
        </button>
      </div>
    `
  }
}