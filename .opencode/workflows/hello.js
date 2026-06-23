export const meta = {
  name: 'hello',
  description: 'Simple test workflow',
  phases: [{ title: 'greet' }],
}

phase('greet')
log('hello from bare globals!')
const x = 1 + 1
log('math works: ' + x)
return { message: 'hello world', sum: x }
