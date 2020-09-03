/// <reference types="cypress" />
import { v4 as uuid4 } from "uuid";
import { IndexedDBScriptAccess } from "../../../src/services/indexeddb";
import { Script } from "../../../src/services";


describe("Indexed DB Access", () => {
  let access = new IndexedDBScriptAccess()

  describe("Add Script", () => {

    it('should generate an id if none given', async () => {
      let script: Script = { name: "Example Script", content: "An example script." }
      let added = await access.addScript(script)

      assert.equal(added.name, script.name)
      assert.equal(added.content, script.content)
      assert.isNotNull(added.id)
    })

    it('should enforce the use of unique ids', async () => {
      let id = uuid4()
      let original: Script = { id: id, name: "Original Script", content: "The original script" }
      await access.addScript(original)

      let duplicate: Script = { id: id, name: "Duplicate Script", content: "This script clashes" }

      try {
        await access.addScript(duplicate)
        assert.fail("Unexpected success")
      } catch (err) {
        assert.isTrue(err.message.includes("Key already exists"), err.message)
      }
    })
  })

  describe("Update Script", () => {
    it("should throw an error if there is not a matching existing script", async () => {
      let id = uuid4()
      let script: Script = { id: id, name: 'Bad Update', content: "This should not update." }

      try {
        let r = await access.updateScript(script)
        assert.fail(`Unexpected success ${r}`)
      } catch (err) {
        let msg = err.message
        assert.isTrue(msg.includes(`'${id}' does not exist`), msg)
      }
    })

    it("should allow for an existing script's contents to be changed", async () => {
      let script: Script = { name: 'My Script', content: "Initial content" }
      script = await access.addScript(script)

      script.name = 'My Updated Script'
      script.content = "With Updated Content"

      script = await access.updateScript(script)

      let result = await access.getScript(script.id)
      assert.equal(result.name, script.name)
      assert.equal(result.content, script.content)
    })

  })

  describe("Get Script", () => {
    it("should return the script as referenced by its id", async () => {
      let id = uuid4()
      let script: Script = { id: id, name: "My Script", content: "My script's content" }
      await access.addScript(script)

      let result = await access.getScript(script.id)
      assert.equal(script.id, result.id)
      assert.equal(script.name, result.name)
      assert.equal(script.content, result.content)
    })

    it("should throw an error if the script cannot be found", async () => {
      try {
        let r = await access.getScript("bad-id")
        assert.fail(`Unexpected success: ${r}`)
      } catch (err) {
        let msg = err.message
        assert.isTrue(msg.includes("'bad-id' does not exist"), msg)
      }
    })
  })
})