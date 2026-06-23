export default {
  meta: { name: 'standard-test', description: 'Test standard format' },
  async run(args, ctx) {
    ctx.log('calling agent via ctx')
    const result = await ctx.agent({ prompt: 'What is 2 + 2? Reply with just the number.' })
    ctx.log('result: ' + JSON.stringify(result))
    return { text: result?.text, data: result?.data, keys: result ? Object.keys(result) : null }
  }
}
