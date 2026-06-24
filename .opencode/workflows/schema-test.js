export const meta = {
  name: "schema-test",
  description: "Test structured output"
}

log("Testing agent with schema")
const result = await agent("What is 2+2? Answer with the number.", {
  schema: {
    type: "object",
    properties: {
      answer: { type: "number" },
      explanation: { type: "string" }
    },
    required: ["answer"]
  }
})
log("Result type: " + typeof result)
log("Result value: " + JSON.stringify(result).substring(0, 300))
return result
