import { WelcomeScreen } from "./welcome";
import { AppMain } from "./app";

export function registerComponents() {
  let components = [
    AppMain,
    WelcomeScreen
  ]

  components.forEach(element => {
    if (!window.customElements.get(element.ELEMENT_NAME)) {
      window.customElements.define(element.ELEMENT_NAME, element)
    }
  })
}