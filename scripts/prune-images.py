#!/usr/bin/env python3
"""
Prune unused image sources from public/images so the deploy bundle stays lean.

Reads the BUILT dist/ to learn which image URLs are actually referenced, then
deletes public/ images that no page points at.

The build embeds gallery configs inside HTML attributes where quotes are
entity-escaped (&quot;), so this script unescapes entities before matching.

Keeps:
  - every image referenced by any built page (HTML/JS/XML), including all
    -640/-1024/-1280 srcset siblings and the flat 1024w file
  - files listed in KEEP_ALWAYS (og:image, <picture> fallbacks, build inputs)
Drops:
  - photo_*.jpg intermediates (duplicates of hand-named files) and their webp
  - logo-source.jpg
  - anything else not reachable from the built site

NEVER run this against a stale dist/. The script refuses to run when dist/ is
missing, and you should rebuild immediately before pruning.

Usage: python3 scripts/prune-images.py [--apply]
"""
import html
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
PUBLIC = ROOT / 'public'
APPLY = '--apply' in sys.argv

if not DIST.is_dir():
    sys.exit('dist/ not found - run `npx astro build` first (prune reads the build to know what is referenced)')

KEEP_ALWAYS = {
    'images/kuala-terengganu/exterior.jpg',      # og:image + JSON-LD
    'images/logo.png', 'images/logo-dark.png',   # <picture> fallbacks
    'favicon.svg', 'favicon.ico',
    'favicon-16x16.png', 'favicon-32x32.png',    # referenced from <head>, not <img>
    'favicon-192x192.png', 'favicon-512x512.png',  # PWA manifest icons
    'apple-touch-icon.png',
    'og-image.jpg',
}

IMG_RE = re.compile(r'/images/[^"\'\'<>&]+?\.(?:jpe?g|png|webp)', re.I)


def referenced_urls():
    """Collect every /images/... URL any built page points at.

    Filenames contain spaces and the gallery configs embed them in escaped
    attributes, so unescape entities first and match on the file extension
    instead of assuming the URL ends at the first space.
    """
    urls = set()
    files = list(DIST.rglob('*.html')) + list(DIST.rglob('*.js')) + list(DIST.rglob('*.xml'))
    for f in files:
        text = html.unescape(f.read_text(errors='ignore'))
        for piece in IMG_RE.findall(text):
            urls.add(urllib.parse.unquote(piece).lstrip('/'))
    return urls


refs = referenced_urls()

keep = set(KEEP_ALWAYS)
for r in refs:
    keep.add(r)
    base = re.sub(r'\.(jpe?g|png|webp)$', '', r)
    for suffix in ('', '-320', '-640', '-1024', '-1280'):
        keep.add(f'{base}{suffix}.webp')
    keep.add(f'{base}-hero.webp')
    keep.add(f'{base}-hero.jpg')

# Safety net: if the scan found suspiciously few images, refuse to delete.
if len(refs) < 20:
    sys.exit(f'only {len(refs)} referenced images found - dist/ looks stale, rebuild and retry')

removed = freed = 0
for p in sorted(PUBLIC.rglob('*')):
    if not p.is_file() or p.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp'):
        continue
    rel = p.relative_to(PUBLIC).as_posix()
    if rel in keep:
        continue
    freed += p.stat().st_size
    removed += 1
    print(f'{"REMOVE" if APPLY else "would remove"} {rel}')
    if APPLY:
        p.unlink()

print(f'\nreferenced image URLs: {len(refs)} | kept: {len(keep)}')
print(f'{removed} files, {freed/1024/1024:.1f} MB {"freed" if APPLY else "to free"}')
if not APPLY:
    print('rerun with --apply to delete')
