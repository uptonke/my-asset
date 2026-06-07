#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

INDEX = Path('index.html')
if not INDEX.exists():
    raise SystemExit('index.html not found. Run this from repo root.')

html = INDEX.read_text(encoding='utf-8')
original = html

# 1) Remove Tailwind CDN runtime and CDN config script.
html = html.replace('    <script src="https://cdn.tailwindcss.com"></script>\n', '    <link rel="stylesheet" href="assets/css/tailwind-built.css">\n')
html = html.replace('    <script src="assets/js/00-tailwind-config.js"></script>\n', '')

# 2) Add denoise layer after the existing 00–50 custom CSS stack.
denoise_link = '    <link rel="stylesheet" href="assets/css/60-design-token-denoise.css">\n'
if 'assets/css/60-design-token-denoise.css' not in html:
    target = '    <link rel="stylesheet" href="assets/css/50-bloomberg-terminal-hard.css">\n'
    if target in html:
        html = html.replace(target, target + denoise_link)
    else:
        html = html.replace('</head>', denoise_link + '</head>')

# 3) Cache-bust the no-chip quant display file.
html = html.replace('assets/js/quant-main-display.js"></script>', 'assets/js/quant-main-display.js?v=12.0-no-chip"></script>')
html = html.replace('assets/js/quant-main-display.js?v=12.0-no-chip?v=12.0-no-chip"></script>', 'assets/js/quant-main-display.js?v=12.0-no-chip"></script>')

if html != original:
    INDEX.write_text(html, encoding='utf-8')
    print('OK patched index.html: Tailwind CDN removed, denoise CSS added, quant display cache-busted.')
else:
    print('No changes needed in index.html.')
