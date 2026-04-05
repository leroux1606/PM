import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const out = path.join(root, "out");
const dest = path.join(root, "..", "backend", "site");

if (!fs.existsSync(out)) {
  console.error("Missing frontend/out. Run: npm run build");
  process.exit(1);
}

fs.rmSync(dest, { recursive: true, force: true });
fs.cpSync(out, dest, { recursive: true });
console.log(`Copied ${out} -> ${dest}`);
