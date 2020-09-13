import { LitElement, html, property } from "lit-element";
import { Icon } from "./icon";

export class EditorToolbar extends LitElement {
  static readonly ELEMENT_NAME = "editor-toolbar"

  @property()
  public scriptTitle: string

  @property({ type: Boolean, attribute: 'show', reflect: true })
  public showToolbar: boolean

  constructor() {
    super()
  }

  createRenderRoot() {
    return this
  }

  handleNew() {
    this.dispatchEvent(new CustomEvent("new-script"))
  }

  handleSave() {
    this.dispatchEvent(new CustomEvent('save-script'))
  }

  handleOpen() {
    this.dispatchEvent(new CustomEvent('open-script'))
  }

  handleRename(event: CustomEvent) {
    let title = event.detail.title
    this.scriptTitle = title
    this.handleSave()
  }

  render() {
    return html`
      <div class="bg-gray-700 p-2 flex justify-between items-center w-full transition-opacity duration-200 ease-in-out text-gray-300 ${this.showToolbar ? '' : 'opacity-0'}">

        <span>
          <button class="rounded p-1 leading-none" @click=${this.handleNew}>
            <x-icon name="${Icon.FILE}" class="inline-block w-6 h-6"></x-icon>
          </button>
          <button class="rounded p-1 ml-2 leading-none" @click=${this.handleSave}>
            <x-icon name="${Icon.SAVE}" class="inline-block w-6 h-6"></x-icon>
          </button>
          <button class="rounded p-1 ml-2 leading-none" @click=${this.handleOpen}>
            <x-icon name="${Icon.FOLDER}" class="inline-block w-6 h-6"></x-icon>
          </button>
        </span>

        <script-title @rename="${this.handleRename}" .title="${this.scriptTitle}"></script-title>
        <span>
          <button class="rounded p-1 ml-2 leading-none" @click=${this.handleSave}>
            <x-icon name="${Icon.COLUMNS}" class="inline-block w-6 h-6"></x-icon>
          </button>
        </span>
      </div>
    `
  }
}