import { html, render } from "lit-html";

let template = () => html`
<div class="flex">
  <input data-id="title" class="bg-gray-900 disabled:bg-gray-700 text-center rounded" type="text" disabled value="Untitled" />
  <button data-id="edit-title" class="bg-gray-600 rounded p-1 ml-2">
    <svg data-id="pencil" class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M17 3a2.828 2.828 0 114 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>
    </svg>
    <svg data-id="check" class="w-6 h-6 hidden" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M20 6L9 17l-5-5"/>
    </svg>
  </button>
</div>
`

export class ScriptTitle extends HTMLElement {
  static readonly ELEMENT_NAME = 'script-title'

  private titleField: HTMLInputElement
  private pencilIcon: HTMLElement
  private checkIcon: HTMLElement

  constructor() {
    super()
  }

  connectedCallback() {
    render(template(), this)

    this.titleField = this.querySelector('[data-id="title"]')
    this.pencilIcon = this.querySelector('[data-id="pencil"]')
    this.checkIcon = this.querySelector('[data-id="check"]')

    this.querySelector('[data-id="edit-title"]').addEventListener('click', () => {
      if (this.titleField.disabled) {
        this.editTitle()
      } else {
        this.saveTitle()
      }
    })

    this.titleField.addEventListener('change', () => {
      this.saveTitle()
    })
  }

  editTitle() {
    this.titleField.disabled = false
    this.titleField.focus()
    this.titleField.select()

    this.pencilIcon.classList.add("hidden")
    this.checkIcon.classList.remove("hidden")
  }

  saveTitle() {
    this.titleField.disabled = true

    this.checkIcon.classList.add("hidden")
    this.pencilIcon.classList.remove("hidden")

    document.body.dispatchEvent(new CustomEvent("title-changed", { detail: { title: this.titleField.value } }))
  }

}