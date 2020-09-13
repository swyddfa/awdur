import { LitElement, html, property } from "lit-element";
import { ScriptAccess, Script } from "../services";
import { Icon } from "./icon";


export class FileOpenModal extends LitElement {
  public static ELEMENT_NAME = "file-open"

  public scriptAccess: ScriptAccess

  @property({ attribute: false })
  private localScripts: Script[]

  @property()
  private selectedScript: Script

  createRenderRoot() {
    return this;
  }

  cancel() {
    this.dispatchEvent(new CustomEvent('close'))
  }

  open() {
    this.dispatchEvent(new CustomEvent("close", { detail: { script: this.selectedScript } }))
  }

  handleSelect(event: Event) {
    let target = <HTMLSelectElement>event.target
    this.localScripts.forEach(script => {
      if (script.id === target.value) {
        this.selectedScript = script
      }
    })
  }

  async firstUpdated(changedProperties) {
    let scripts = await this.scriptAccess.getScripts()
    this.localScripts = scripts
  }

  render() {
    return html`
      <div class="absolute top-0 left-0 h-screen w-screen grid grid-cols-4 grid-rows-4 bg-transparent">
        <div class="bg-white rounded border flex flex-col col-span-2 col-start-2 row-span-2 row-start-2">

        <div class="border-b text-2xl text-center px-2 py-1">
          Open Script
        </div>

          <div class="flex flex-grow justify-between">
            <div class="border-r">
              <span class="flex items-center p-2">
                <x-icon name=${Icon.FOLDER} class="inline-block w-6 h-6"></x-icon>
                <span class="ml-2 text-xl">Local</span>
              </span>
            </div>
            <div class="flex-grow">
              <select class=" bg-white p-1 w-full h-full" @change=${this.handleSelect} multiple>
                ${this.localScripts?.map(s => html`<option class="py-2" value="${s.id}">${s.name}</option>`)}
              </select>
            </div>
          </div>

          <div class="flex justify-end p-4 border-t">
            <button @click="${this.cancel}"
                    class="px-4 py-2 bg-gray-700 text-gray-200 rounded">Cancel</button>
            <button @click="${this.open}"
                    class="px-4 py-2 bg-gray-700 text-gray-200 rounded ml-2">Open</button>
          </div>
        </div>
      </div>
    `
  }
}