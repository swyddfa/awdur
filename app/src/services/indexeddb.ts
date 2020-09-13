import * as idb from "idb";
import { v4 as uuid4 } from "uuid";
import { ScriptAccess, Script } from ".";

const dbMigration: idb.OpenDBCallbacks<unknown> = {
  upgrade: (db, oldVersion, newVersion, transaction) => {

    if (!db.objectStoreNames.contains(IndexedDBScriptAccess.DB_NAME)) {
      let scripts = db.createObjectStore(IndexedDBScriptAccess.DB_NAME, {
        keyPath: 'id'
      })

      scripts.createIndex("name", "name")
    }
  }
}

export class IndexedDBScriptAccess implements ScriptAccess {
  private static readonly DB_VERSION = 1
  public static readonly DB_NAME = "scripts"

  private db: Promise<idb.IDBPDatabase<unknown>>

  constructor() {
    this.db = idb.openDB(IndexedDBScriptAccess.DB_NAME, IndexedDBScriptAccess.DB_VERSION, dbMigration)
  }

  async addScript(script: Script): Promise<Script> {
    let record = { ...script }

    if (!record.id) {
      record.id = uuid4()
    }

    let db = await this.db
    await db.add(IndexedDBScriptAccess.DB_NAME, record)
    return record
  }

  async updateScript(script: Script): Promise<Script> {
    let db = await this.db
    let existing = await this.getScript(script.id)

    await db.put(IndexedDBScriptAccess.DB_NAME, script)
    return script
  }

  async getScript(id: string): Promise<Script> {
    let db = await this.db
    let result = await db.get(IndexedDBScriptAccess.DB_NAME, id)

    if (!result) {
      throw new Error(`Script with id '${id}' does not exist`)
    }

    return result
  }

  async getScripts(): Promise<Script[]> {
    let db = await this.db

    return await db.getAll(IndexedDBScriptAccess.DB_NAME)
  }


}