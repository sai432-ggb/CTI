import fs from 'fs';

const path = './dist/client/wrangler.json';

if (!fs.existsSync(path)) {
  console.log('wrangler.json not found, skipping sanitization');
  process.exit(0);
}

const cfg = JSON.parse(fs.readFileSync(path, 'utf8'));

// Remove unsupported keys
const allowed = ['name','main','compatibility_date','type','routes','triggers','build','site'];
for (const k of Object.keys(cfg)) {
  if (!allowed.includes(k)) {
    console.log(`Removing unsupported field: ${k}`);
    delete cfg[k];
  }
}

// Fix triggers: remove if empty or invalid
if (cfg.triggers) {
  if (!cfg.triggers.crons || cfg.triggers.crons.length === 0) {
    console.log('Removing empty triggers block');
    delete cfg.triggers;
  } else {
    // Ensure proper structure
    if (!cfg.triggers.crons) {
      cfg.triggers.crons = [];
    }
  }
}

// Ensure minimal valid structure for Pages deployment
if (!cfg.compatibility_date) {
  cfg.compatibility_date = "2026-01-01";
}

if (!cfg.type) {
  cfg.type = "javascript";
}

// Add required fields for Pages deployment
if (!cfg.main) {
  cfg.main = "../server/server.js";
}

if (!cfg.assets) {
  cfg.assets = {
    "directory": "./dist"
  };
}

fs.writeFileSync(path, JSON.stringify(cfg, null, 2));
console.log('Sanitized wrangler.json successfully');
