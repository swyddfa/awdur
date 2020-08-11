
import { registerFountainLang } from "./fountain";
import { createEditor } from "./editor";
import { registerComponents } from "./components";
import "./index.css"

registerComponents()
const welcome = document.createElement("welcome-screen")
document.body.append(welcome)

/*
registerFountainLang()
const container = document.createElement("div")
container.className = "editor"
document.body.append(container)

createEditor(container)
*/
