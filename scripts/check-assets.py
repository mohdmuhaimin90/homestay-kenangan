#!/usr/bin/env python3
"""
Guard against broken links: every local asset URL the built HTML references must
exist on disk in dist/. Handles srcset with spaces in filenames.

Usage: python3 scripts/check-assets.py
Exit 0 = clean, 1 = broken references found.
"""
import re
import sys
import urllib.parse
from pathlib import Path

DIST = Path(__file__).resolve().parent.parent / 'dist'
ASSET_RE = re.compile(r'\.(jpe?g|png|webp|svg|ico|css|js|xml|txt|json|webmanifest)$', re.I)


def parse_srcset(value: str) -> list[str]:
    """Split a srcset into URLs. Filenames may contain spaces, so only treat a
    comma as a separator when the next candidate ends with a W/x descriptor."""
    urls = []
    for part in re.split(r',\s*(?=[^\s,])', value):
        tokens = part.strip().split()
        if not tokens:
            continue
        if tokens[-1].endswith(('w', 'x')):
            tokens = tokens[:-1]
        urls.append(' '.join(tokens))
    return urls


broken = []
checked = 0
seen = set()
for page in sorted(DIST.rglob('*.html')):
    html = page.read_text(errors='ignore')
    for attr in ('srcset', 'src', 'href'):
        for m in re.finditer(rf'{attr}="([^"]+)"', html):
            value = m.group(1)
            urls = parse_srcset(value) if attr == 'srcset' else [value]
            for url in urls:
                if not url.startswith('/') or not ASSET_RE.search(url):
                    continue
                key = (page.name, url)
                if key in seen:
                    continue
                seen.add(key)
                checked += 1
                if not (DIST / urllib.parse.unquote(url).lstrip('/')).exists():
                    broken.append((page.relative_to(DIST).as_posix(), url))

print(f'checked {checked} unique local asset URLs')
if broken:
    print(f'BROKEN ({len(broken)}):')
    for page, url in broken:
        print(f'  {page} -> {url}')
    sys.exit(1)
print('OK - no broken asset references')
