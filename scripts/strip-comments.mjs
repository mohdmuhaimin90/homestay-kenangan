/**
 * Strip HTML comments and collapse whitespace in built pages.
 *
 * Astro keeps component comments in the output. They are harmless but they ship
 * to every visitor, and audit tooling that scans for <img> tags without alt text
 * (or similar) can false-positive on commented-out markup.
 */
import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const DIST = new URL('../dist/', import.meta.url).pathname;

async function walk(dir) {
  const out = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const p = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...await walk(p));
    else if (entry.name.endsWith('.html')) out.push(p);
  }
  return out;
}

let changed = 0;
for (const file of await walk(DIST)) {
  const before = await readFile(file, 'utf8');
  // Remove comments, but keep conditional comments used by old IE shims.
  const after = before.replace(/<!--(?!\[if)[\s\S]*?-->/g, '').replace(/\n{3,}/g, '\n\n');
  if (after !== before) {
    await writeFile(file, after);
    changed += 1;
  }
}
console.log(`strip-comments: cleaned ${changed} HTML files`);
