import { LitElement, html, property } from "lit-element";
import { Icon } from "./editor/icon";

export class EditorToolbar extends LitElement {
  static readonly ELEMENT_NAME = "editor-toolbar"

  @property()
  private scriptTitle: string

  constructor() {
    super()
    this.scriptTitle = "Untitled Script"
  }

  createRenderRoot() {
    return this
  }

  handleNew() {
    console.log("New script")
  }

  handleSave() {
    console.log("Save script")
  }

  render() {
    return html`
      <div class="bg-gray-700 p-4 flex justify-between items-center w-full text-gray-300">

        <span>
          <button class="bg-gray-600 rounded p-1 leading-none" @click=${this.handleNew}>
            <x-icon name="${Icon.FILE}" class="inline-block w-6 h-6"></x-icon>
          </button>
          <button class="bg-gray-600 rounded p-1 ml-2 leading-none" @click=${this.handleSave}>
            <x-icon name="${Icon.SAVE}" class="inline-block w-6 h-6"></x-icon>
          </button>
          <button class="bg-gray-600 rounded p-1 ml-2 leading-none" @click=${this.handleSave}>
            <x-icon name="${Icon.FOLDER}" class="inline-block w-6 h-6"></x-icon>
          </button>
        </span>

        <script-title .title="${this.scriptTitle}"></script-title>
        <span>
          <button class="bg-gray-600 rounded p-1 ml-2 leading-none" @click=${this.handleSave}>
            <x-icon name="${Icon.COLUMNS}" class="inline-block w-6 h-6"></x-icon>
          </button>
        </span>
      </div>
    `
  }
}