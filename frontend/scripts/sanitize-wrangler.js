import fs from 'fs'
import path from 'path'

const wranglerPath = path.resolve('dist/client/wrangler.json')
if (fs.existsSync(wranglerPath)) {
  fs.unlinkSync(wranglerPath)
  console.log('Removed generated wrangler.json')
} else {
  console.log('No generated wrangler.json found')
}
// scripts/sanitize-wrangler.js
import fs from 'fs';
const path = 'dist/client/wrangler.json';
if (fs.existsSync(path)) {
  const config = JSON.parse(fs.readFileSync(path, 'utf-8'));
  if (config.triggers) {
    delete config.triggers;
    fs.writeFileSync(path, JSON.stringify(config, null, 2));
    console.log('Removed triggers from dist/client/wrangler.json');
  }
}
