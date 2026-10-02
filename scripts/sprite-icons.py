#!/usr/bin/env python3
"""
Replace repeated inline <svg> blocks with <Icon name="..."/> component calls.

Only rewrites the exact SVG markup that appears in the site's components, and
only when the same markup repeats. Run with --apply to write.

The Icon component lives in src/components/Icon.astro and holds the path set.
"""
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path('/tmp/hk/src')
APPLY = '--apply' in sys.argv

# Map from a stable fragment of the svg's inner markup to an Icon name.
SIGNATURES = [
    ('<circle cx="11" cy="11" r="8"', 'search'),
    ('M22 16.92v3a2 2 0 0 1-2.18 2', 'phone'),
    ('<line x1="19" y1="12" x2="5" y2="12"', 'arrow-left'),
    ('<line x1="5" y1="12" x2="19" y2="12"', 'arrow-right'),
    ('<line x1="12" y1="5" x2="12" y2="19"', 'arrow-down'),
    ('<polyline points="6 9 12 15 18 9"', 'chevron-down'),
    ('<polyline points="9 18 15 12 9 6"', 'chevron-right'),
    ('<polyline points="15 18 9 12 15 6"', 'chevron-left'),
    ('<circle cx="12" cy="12" r="10"', 'clock'),
    ('<path d="M21 10c0 7-9 13-9 13s-9-6-9-13', 'map'),
    ('<polyline points="20 6 9 17 4 12"', 'check'),
    ('<line x1="18" y1="6" x2="6" y2="18"', 'x'),
    ('<path d="M4 4h16c1.1 0 2 .9 2 2v12', 'mail'),
    ('<line x1="3" y1="12" x2="21" y2="12"', 'menu'),
    ('<path d="M3 9l9-7 9 7v11', 'home'),
    ('<path d="M5 12.55a11 11 0 0 1 14.08 0"', 'wifi'),
    ('<polygon points="12 2 15.09 8.26 22 9.27"', 'star'),
    ('<path d="M18 13v6a2 2 0 0 1-2 2H5', 'external-link'),
    ('<path d="M17 21v-2a4 4 0 0 0-4-4H5', 'users'),
]


def icon_for(inner: str):
    for frag, name in SIGNATURES:
        if frag in inner:
            return name
    return None


targets = sorted(ROOT.rglob('*.astro'))
total = 0
for f in targets:
    if f.name == 'Icon.astro':
        continue
    s = f.read_text()
    orig = s

    def repl(m):
        global total
        tag = m.group(0)
        name = icon_for(tag)
        if not name:
            return tag
        # preserve size and class if present
        size = re.search(r'width="(\d+)"', tag)
        cls = re.search(r'class="([^"]*)"', tag)
        sw = re.search(r'stroke-width="([\d.]+)"', tag)
        attrs = []
        if size:
            attrs.append(f'size={{{size.group(1)}}}')
        if cls and cls.group(1).strip():
            attrs.append(f'class="{cls.group(1)}"')
        if sw:
            attrs.append(f'strokeWidth={{{sw.group(1)}}}')
        total += 1
        return f'<Icon name="{name}"' + ('' if not attrs else ' ' + ' '.join(attrs)) + ' />'

    s = re.sub(r'<svg\b.*?</svg>', repl, s, flags=re.S)

    if s != orig:
        # ensure the import exists
        if "from './Icon.astro'" not in s and "from '../components/Icon.astro'" not in s:
            depth = len(f.relative_to(ROOT).parts) - 1
            rel = ('../' * depth) + 'components/Icon.astro'
            if f.parent.name == 'components':
                rel = './Icon.astro'
            s = s.replace('---\n', f"---\nimport Icon from '{rel}';\n", 1)
        print(f'{"WROTE" if APPLY else "would write"} {f.relative_to(ROOT)}')
        if APPLY:
            f.write_text(s)

print(f'\n{total} svg tags converted to <Icon/>')
if not APPLY:
    print('rerun with --apply to write')
