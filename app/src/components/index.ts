import { WelcomeScreen } from "./welcome";

export function registerComponents() {
  let components = [
    WelcomeScreen
  ]

  components.forEach(element => {
    if (!window.customElements.get(element.ELEMENT_NAME)) {
      window.customElements.define(element.ELEMENT_NAME, element)
    }
  })
}