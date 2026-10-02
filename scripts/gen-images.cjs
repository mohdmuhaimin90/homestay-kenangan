#!/usr/bin/env node
/**
 * Generate responsive WebP variants + an optimized LCP hero image.
 *
 * Outputs, for each source in public/images:
 *   <name>-320.webp     320w  quality 62   (home-page slider thumbnails)
 *   <name>.webp        1024w  quality 62   (default gallery variant)
 *   <name>-640.webp     640w  quality 62   (mobile)
 *   <name>-1280.webp   1280w  quality 62   (wide screens)
 * Gallery <source srcset> points at the width descriptor set.
 *
 * Hero image (kuala-terengganu/exterior) additionally gets:
 *   exterior-hero.webp  1280w quality 72   (sharp, used for LCP)
 *   exterior-hero.jpg   1280w quality 72   (fallback)
 */
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..', 'public', 'images');
const Q = 62;
// 320w covers the home-page slider thumbnails (321x428 CSS box). Without it the
// browser had to take the 640w file for a 321px slot, roughly tripling bytes.
const WIDTHS = [320, 640, 1024, 1280];

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (/\.(jpe?g|png)$/i.test(e.name)) out.push(p);
  }
  return out;
}

async function variant(src, dest, width, quality) {
  const img = sharp(src).rotate();
  const meta = await img.metadata();
  const target = meta.width && meta.width < width ? meta.width : width;
  await img
    .resize({ width: target, withoutEnlargement: true })
    .webp({ quality, effort: 6, smartSubsample: true })
    .toFile(dest);
  return fs.statSync(dest).size;
}

(async () => {
  const files = walk(ROOT).filter((f) => !/logo-source/i.test(f));
  let before = 0;
  let after = 0;
  let n = 0;

  for (const f of files) {
    const base = f.replace(/\.(jpe?g|png)$/i, '');
    if (/-320$|-640$|-1024$|-1280$|-hero$/i.test(base)) continue; // skip our own outputs
    before += fs.statSync(f).size;
    for (const w of WIDTHS) {
      const dest = `${base}-${w}.webp`;
      const size = await variant(f, dest, w, Q);
      if (w === 1024) after += size;
      n++;
    }
    const flat = `${base}.webp`;
    await variant(f, flat, 1024, Q);
    n++;
  }

  // Hero: sharper than gallery, with a width set so the browser does not pull a
  // 1280w file into an 800px-wide slot on a laptop. JPEG fallback included.
  const heroSrc = path.join(ROOT, 'kuala-terengganu', 'exterior.jpg');
  const heroBase = path.join(ROOT, 'kuala-terengganu', 'exterior-hero');
  await sharp(heroSrc).rotate().resize({ width: 1024 }).webp({ quality: 68, effort: 6 }).toFile(`${heroBase}.webp`);
  for (const w of [640, 1280]) {
    await sharp(heroSrc).rotate().resize({ width: w }).webp({ quality: 66, effort: 6 }).toFile(`${heroBase}-${w}.webp`);
  }
  await sharp(heroSrc).rotate().resize({ width: 1024 }).jpeg({ quality: 70, mozjpeg: true }).toFile(`${heroBase}.jpg`);

  console.log(`${n} responsive webp variants written.`);
  console.log(`gallery default (1024w) total: ${(before / 1024).toFixed(0)} KB jpg/png -> ${(after / 1024).toFixed(0)} KB webp`);
  console.log(`hero webp: ${(fs.statSync(`${heroBase}.webp`).size / 1024).toFixed(1)} KB`);
  console.log(`hero jpg : ${(fs.statSync(`${heroBase}.jpg`).size / 1024).toFixed(1)} KB`);
})();
