import { html, render } from "lit-html";

let template = () => html`
  <div class="bg-gray-700 p-4 flex justify-between items-center w-full text-gray-300">
    <button class="bg-gray-600 rounded p-1">
      <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/>
        <path d="M17 21v-8H7v8M7 3v5h8"/>
      </svg>
    </button>

    <script-title></script-title>
    <span></span>
  </div>
`

export class EditorToolbar extends HTMLElement {
  static readonly ELEMENT_NAME = "editor-toolbar"

  private scriptTitle: HTMLElement

  constructor() {
    super()
  }

  connectedCallback() {
    render(template(), this)

    this.scriptTitle
  }
}