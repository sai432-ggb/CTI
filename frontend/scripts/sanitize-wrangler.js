import fs from 'fs';
import path from 'path';

const configPath = path.resolve('./dist/client/wrangler.json');

if (!fs.existsSync(path)) {
  console.log('wrangler.json not found, skipping sanitization');
  process.exit(0);
}

const cfg = JSON.parse(fs.readFileSync(path, 'utf8'));

// Remove unsupported keys completely
const unsupported = [
  'definedEnvironments','ai_search_namespaces','ai_search','secrets_store_secrets',
  'artifacts','unsafe_hello_world','flagship','worker_loaders','ratelimits',
  'vpc_services','vpc_networks','python_modules','configPath','userConfigPath',
  'topLevelName','legacy_env','compatibility_flags','jsx_factory','jsx_fragment',
  'rules','assets','vars','durable_objects','workflows','migrations',
  'kv_namespaces','cloudchamber','send_email','queues','r2_buckets',
  'd1_databases','vectorize','analytics_engine_datasets','dispatch_namespaces',
  'mtls_certificates','pipelines','logfwdr','no_bundle'
];

for (const k of Object.keys(cfg)) {
  if (unsupported.includes(k)) {
    console.log(`Removing unsupported field: ${k}`);
    delete cfg[k];
  }
}

// Remove triggers entirely - it's causing issues
if (cfg.triggers) {
  console.log('Removing triggers block entirely');
  delete cfg.triggers;
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
