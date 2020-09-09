/// <reference types="cypress" />

describe("Welcome", () => {
  describe("First Load", () => {
    it("the window should have the title 'Awdur'", () => {
      cy.visit("http://localhost:9000")
      cy.title().should("equal", "Awdur")
    })
  })

  describe("New Script", () => {
    it("clicking new script should create a new untitled script", () => {
      cy.visit("http://localhost:9000")

      cy.contains("New").click()
      cy.title().should("equal", "Untitled - Awdur")
    })
  })
})
