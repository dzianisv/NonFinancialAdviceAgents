export const meta = {
  name: 'agent-test',
  description: 'Test agent call',
}

log('calling agent')
const result = await agent('What is 2 + 2? Reply with just the number.')
log('result type: ' + typeof result)
log('result value: ' + String(result).substring(0, 200))
if (result && typeof result === 'object') {
  log('result keys: ' + Object.keys(result).join(', '))
  log('result.text: ' + String(result.text).substring(0, 200))
  log('result.data: ' + String(result.data).substring(0, 200))
}
return { answer: result }
