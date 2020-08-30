import { LitElement, html, property } from "lit-element";

/**
 * Inserts the SVG code for the given icon into the page.
 *
 * Icons sourced from:
 * - Feather Icons: https://feathericons.com/
 */
export class Icon extends LitElement {
  public static ELEMENT_NAME = "x-icon"

  public static CHECK = "check"
  public static COLUMNS = "columns"
  public static FILE = "file"
  public static FOLDER = "folder"
  public static PENCIL = "pencil"
  public static SAVE = "save"

  @property({ reflect: true })
  public name: string

  createRenderRoot() {
    return this
  }

  render() {
    switch (this.name) {
      case Icon.CHECK:
        return html`
          <svg class="w-full h-full"
               fill="none"
               stroke="currentColor"
               stroke-width="2"
               stroke-linecap="round"
               stroke-linejoin="round">
            <path d="M20 6L9 17l-5-5"/>
          </svg>
        `

      case Icon.COLUMNS:
        return html`
          <svg class="w-full h-full"
               fill="none"
               stroke="currentColor"
               stroke-width="2"
               stroke-linecap="round"
               stroke-linejoin="round">
             <path d="M12 3h7a2 2 0 012 2v14a2 2 0 01-2 2h-7m0-18H5a2 2 0 00-2 2v14a2 2 0 002 2h7m0-18v18"/>
          </svg>
        `

      case Icon.FILE:
        return html`
          <svg class="w-full h-full"
               fill="none"
               stroke="currentColor"
               stroke-width="2"
               stroke-linecap="round"
               stroke-linejoin="round">
            <path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/>
            <path d="M13 2v7h7"/>
          </svg>
        `

      case Icon.FOLDER:
        return html`
          <svg class="w-full h-full"
               fill="none"
               stroke="currentColor"
               stroke-width="2"
               stroke-linecap="round"
               stroke-linejoin="round">
            <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
          </svg>
        `

      case Icon.PENCIL:
        return html`
          <svg class="w-full h-full"
               fill="none"
               stroke="currentColor"
               stroke-width="2"
               stroke-linecap="round"
               stroke-linejoin="round">
            <path d="M17 3a2.828 2.828 0 114 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>
          </svg>
        `

      case Icon.SAVE:
        return html`
          <svg class="w-full h-full"
               fill="none"
               stroke="currentColor"
               stroke-width="2"
               stroke-linecap="round"
               stroke-linejoin="round">
            <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/>
            <path d="M17 21v-8H7v8M7 3v5h8"/>
          </svg>
        `
    }
  }

}