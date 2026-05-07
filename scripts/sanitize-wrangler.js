import fs from 'fs'
import path from 'path'

const wranglerPath = path.resolve('dist/client/wrangler.json')
if (fs.existsSync(wranglerPath)) {
  fs.unlinkSync(wranglerPath)
  console.log('Removed generated wrangler.json')
} else {
  console.log('No generated wrangler.json found')
}
