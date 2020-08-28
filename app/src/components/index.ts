import { WelcomeScreen } from "./welcome";
import { FountainEditor } from "./editor";

export function registerComponents() {
  let components = [
    FountainEditor,
    WelcomeScreen
  ]

  components.forEach(element => {
    if (!window.customElements.get(element.ELEMENT_NAME)) {
      window.customElements.define(element.ELEMENT_NAME, element)
    }
  })
}