import { WelcomeScreen } from "./welcome";
import { FountainEditor } from "./editor";
import { EditorToolbar } from "./editor-toolbar";
import { ScriptTitle } from "./script-title";
import { Icon } from "./editor/icon";

export function registerComponents() {
  let components = [
    EditorToolbar,
    FountainEditor,
    Icon,
    ScriptTitle,
    WelcomeScreen
  ]

  components.forEach(element => {
    if (!window.customElements.get(element.ELEMENT_NAME)) {
      window.customElements.define(element.ELEMENT_NAME, element)
    }
  })
}