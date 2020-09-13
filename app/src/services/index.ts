/**
 * Captures the data contained in a script.
 */
export interface Script {

  /**
   * A unique id for the script.
   */
  id?: string,

  /**
   * Human readable name for the script
   */
  name: string,

  /**
   * The actual text that makes up the script.
   */
  content: string
}

/**
 * An interface that provides a generic way to expose scripts stored in various
 * storage locations.
 */
export interface ScriptAccess {

  /**
   * Add a new script
   */
  addScript(script: Script): Promise<Script>

  /**
   * Get a script given its id.
   */
  getScript(id: string): Promise<Script>

  /**
   * Get list of scripts in the db.
   */
  getScripts(): Promise<Script[]>

  /**
   * Update a script
   */
  updateScript(script: Script): Promise<Script>
}