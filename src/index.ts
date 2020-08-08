import * as monaco from 'monaco-editor'
import { EXAMPLE_SCRIPT } from "./script";
import "./index.css"

// @ts-ignore
self.MonacoEnvironment = {
  getWorkerUrl: function (moduleId, label) {
    return "./editor.worker.bundle.js"
  }
}

monaco.languages.register({ id: 'fountain' })
monaco.languages.setMonarchTokensProvider('fountain', {
  tokenizer: {
    root: [
      { include: '@sceneHeadings' },
      { include: '@transitions' },
      { include: '@characters' }
    ],

    sceneHeadings: [
      [/^([eEiI][nNxX][tT])?\..*$/, 'invalid']
    ],

    characters: [
      [/^[A-Z ]+\^?$/, 'type']
    ],

    transitions: [
      [/>[^<]+$/, 'string'],
      [/[A-Z ]+TO:/, 'string']
    ]
  }
})

monaco.editor.create(document.body, {
  value: EXAMPLE_SCRIPT,
  language: 'fountain',
  lineNumbers: "off",
  minimap: { enabled: false }
})