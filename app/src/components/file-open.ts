import { LitElement, html } from "lit-element";


export class FileOpenModal extends LitElement {
  public static ELEMENT_NAME = "file-open"

  createRenderRoot() {
    return this;
  }

  render() {
    return html`
      <div class="absolute top-0 left-0 h-screen w-screen grid place-center bg-transparent ">
        <div class="bg-white rounded p-4">

          <div class="flex justify-between">
            <div class="border-r">Local</div>
            <div class="flex-grow ml-2">Script one</div>
          </div>

          <div class="flex justify-end">
            <button class="px-4 py-2 bg-gray-700 text-gray-200 rounded">Cancel</button>
            <button class="px-4 py-2 bg-gray-700 text-gray-200 rounded ml-2">Open</button>
          </div>
        </div>
      </div>
    `
  }
}