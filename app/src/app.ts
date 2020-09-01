import * as idb from 'idb'
import { registerComponents } from "./components";
import { FountainEditor } from "./components/editor";
import { EditorToolbar } from "./components/editor-toolbar";
import './styles.css';

const LOCAL_SCRIPTS_VERSION = 1

const dbMigration: idb.OpenDBCallbacks<unknown> = {
  upgrade: (db, oldVersion, newVersion, transaction) => {

    if (!db.objectStoreNames.contains("scripts")) {
      console.log("creating scripts collection")
      let scripts = db.createObjectStore('scripts', {
        keyPath: 'id',
        autoIncrement: true
      })

      scripts.createIndex("filename", "filename")
    }
  }
}

export abstract class Application {

  private header: HTMLElement
  private appMain: HTMLElement
  private footer: HTMLElement

  private toolbar: EditorToolbar
  private editor: FountainEditor

  private db: Promise<idb.IDBPDatabase<unknown>>

  constructor() {
    this.header = document.querySelector("header")
    this.appMain = document.querySelector("main")
    this.footer = document.querySelector("footer")

    this.toolbar = document.querySelector("editor-toolbar")
  }

  main() {
    registerComponents()

    // Get a handle on the database.
    this.db = idb.openDB('local-scripts', LOCAL_SCRIPTS_VERSION, dbMigration)

    const welcome = document.createElement("welcome-screen")
    welcome.addEventListener("new-script", () => this.newScript())
    this.appMain.appendChild(welcome)

  }

  newScript() {
    this.initEditor()
    this.toolbar.scriptTitle = "Untitled Script"
  }

  async handleSaveScript() {
    console.log("saving")
    let content = this.editor.getEditorContent()
    let filename = this.toolbar.scriptTitle

    let result = await this.saveScript(filename, content)
      .catch(err => {
        console.error(err)
        alert("Unable to save")
      })

    console.log('Saved: ', result)
  }

  async saveScript(filename: string, content: string) {
    let dbase = await this.db
    return await dbase.add('scripts', { filename: filename, content: content })
  }

  initEditor() {
    let welcome = this.appMain.querySelector("welcome-screen")
    if (welcome) {
      welcome.remove()
    }

    this.editor = <FountainEditor>document.createElement("fountain-editor")
    this.appMain.append(this.editor)

    this.toolbar.setAttribute("show", "true")
    this.toolbar.addEventListener("save-script", () => this.handleSaveScript())
  }
}