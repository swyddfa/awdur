export class WelcomeScreen extends HTMLElement {
  static readonly ELEMENT_NAME = 'welcome-screen'

  constructor() {
    super()
    let template = <HTMLTemplateElement>document.getElementById("welcome-screen")

    const shadow = this.attachShadow({ mode: 'closed' })
    shadow.appendChild(template.content.cloneNode(true))
  }
}
