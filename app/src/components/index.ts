import { WelcomeScreen } from "./welcome";
import { FountainEditor } from "./editor";
import { EditorToolbar } from "./editor-toolbar";
import { ScriptTitle } from "./script-title";
import { Icon } from "./icon";
import { Version } from "./version";
import { FileOpenModal } from "./file-open";

export function registerComponents() {
  let components = [
    EditorToolbar,
    FileOpenModal,
    FountainEditor,
    Icon,
    ScriptTitle,
    Version,
    WelcomeScreen
  ]

  components.forEach(element => {
    if (!window.customElements.get(element.ELEMENT_NAME)) {
      window.customElements.define(element.ELEMENT_NAME, element)
    }
  })
}