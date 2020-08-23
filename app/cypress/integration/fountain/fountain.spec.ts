/// <reference types="cypress" />
import * as monaco from "monaco-editor/esm/vs/editor/editor.api";
import { registerFountainLang } from "../../../src/editor/fountain";

// Ensure the fountain language is registered
registerFountainLang()

// Take the cartesian product of 2 arrays
// https://stackoverflow.com/questions/12303989/cartesian-product-of-multiple-arrays-in-javascript
function product(xs: any[], ys: any[]) {
  return [].concat(...xs.map(x => ys.map(y => [].concat(x, y))))
}

function generateSceneTestCases(): string[] {
  let testCases = []

  // Generate the rest based on the following 'seed' values
  let locations = [
    "Garage",
    "Car Park",
  ]
  locations.forEach(loc => {
    testCases.push(...[
      `.${loc}`,
      `.${loc.toLowerCase()}`,
      `.${loc.toUpperCase()}`,
    ])
  })

  let times = [
    "Day",
    "Night"
  ]
  product(locations, times).forEach(([loc, time]) => {
    testCases.push(...[
      `.${loc} - ${time}`,
      `.${loc.toLowerCase()} - ${time.toLowerCase()}`,
      `.${loc.toUpperCase()} - ${time.toUpperCase()}`,
    ])
  })


  let types = [
    "Int",
    "Ext",
    "Est",
    "Int/Ext",
  ]

  product(product(types, locations), times).forEach(example => {
    let type: string = example[0]
    let loc: string = example[1]
    let time: string = example[2]

    testCases.push(...[
      `${type} ${loc} - ${time}`,
      `${type}. ${loc} - ${time}`,
      `${type.toLowerCase()} ${loc} - ${time}`,
      `${type.toLowerCase()}. ${loc} - ${time}`,
      `${type.toUpperCase()} ${loc} - ${time}`,
      `${type.toUpperCase()}. ${loc} - ${time}`,
    ])
  })

  return testCases
}

describe("Fountain: Tokenizer", () => {

  //https://fountain.io/syntax#section-slug
  describe("scenes", () => {

    let testCases = generateSceneTestCases()
    testCases.forEach(testCase => {
      it(`scene heading: ${testCase}`, () => {

        let tokens = monaco.editor.tokenize(testCase, 'fountain')
        expect(tokens.length).to.equal(1)

        let line = tokens[0]
        expect(line.length).to.equal(1)

        let t = line[0]
        expect(t.language, 'fountain')
        expect(t.type).to.equal('scene.fountain')
      })
    })
  })

  describe("characters", () => {
    let testCases = [
      "ALICE",
      "MYSTERIOUS FIGURE",
      "BOB^",
      "CHARLIE ^"
    ]

    testCases.forEach(testCase => {
      it(`character: ${testCase}`, () => {

        let tokens = monaco.editor.tokenize(testCase, 'fountain')
        expect(tokens.length).to.equal(1)

        let line = tokens[0]
        expect(line.length).to.equal(1)

        let t = line[0]
        expect(t.language).to.equal('fountain')
        expect(t.type).to.equal('character.fountain')
      })
    })
  })

  describe("transition", () => {
    let testCases = [
      "> FADE TO BLACK",
      "CUT TO:"
    ]

    testCases.forEach(testCase => {
      it(`transition: ${testCase}`, () => {

        let tokens = monaco.editor.tokenize(testCase, 'fountain')
        expect(tokens.length).to.equal(1)

        let line = tokens[0]
        expect(line.length).to.equal(1)

        let t = line[0]
        expect(t.language).to.equal('fountain')
        expect(t.type).to.equal('transition.fountain')
      })
    })
  })

  describe('action', () => {
    let testCases = [
      'The car rolled to a stop.'
    ]

    testCases.forEach(testCase => {
      it(`action: ${testCase}`, () => {

        let tokens = monaco.editor.tokenize(testCase, 'fountain')
        expect(tokens.length).to.equal(1)

        let line = tokens[0]
        expect(line.length).to.equal(1)

        let t = line[0]
        expect(t.language).to.equal('fountain')
        expect(t.type).to.equal('action.fountain')
      })
    })
  })
})
