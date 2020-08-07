import * as monaco from 'monaco-editor'
import "./index.css"

// @ts-ignore
self.MonacoEnvironment = {
  getWorkerUrl: function (moduleId, label) {
    return "./editor.worker.bundle.js"
  }
}

monaco.editor.create(document.body, {
  value: "Hello!",
  lineNumbers: "off",
  minimap: { enabled: false }
})