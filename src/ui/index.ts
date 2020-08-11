
import { registerFountainLang } from "./fountain";
import { createEditor } from "./editor";
import "./index.css"


registerFountainLang()

const container = document.createElement("div")
container.className = "editor"
document.body.append(container)

createEditor(container)