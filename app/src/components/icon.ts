import { LitElement, html, property } from "lit-element";

/**
 * Inserts the SVG code for the given icon into the page.
 *
 * Icons sourced from:
 * - Feather Icons: https://feathericons.com/
 * - Simple Icons: https://simpleicons.org/
 */
export class Icon extends LitElement {
  public static ELEMENT_NAME = "x-icon"

  public static CHECK = "check"
  public static COLUMNS = "columns"
  public static FILE = "file"
  public static FOLDER = "folder"
  public static GITHUB = "github"
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

      case Icon.GITHUB:
        return html`
          <svg class="w-full h-full"
               viewBox="0 0 24 24">
            <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
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