#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

INDEX = Path("index.html")
CSS_PATH = "assets/css/70-terminal-design-system.css"
JS_PATH = "assets/js/terminal-ui-polish.js"

def insert_after_last_css(text: str, href: str) -> str:
    if href in text:
        return text
    tag = f'    <link rel="stylesheet" href="{href}?v=terminal-ds-1">'
    matches = list(re.finditer(r'^\s*<link\s+rel="stylesheet"\s+href="assets/css/[^"]+(?:\?v=[^"]*)?">\s*$', text, flags=re.M))
    if matches:
        m = matches[-1]
        return text[:m.end()] + "\n" + tag + text[m.end():]
    head = text.find("</head>")
    if head != -1:
        return text[:head] + tag + "\n" + text[head:]
    raise RuntimeError("Cannot find stylesheet insertion point in index.html")

def insert_before_body_end(text: str, src: str) -> str:
    if src in text:
        return text
    tag = f'    <script src="{src}?v=terminal-ds-1"></script>'
    body_end = text.rfind("</body>")
    if body_end != -1:
        return text[:body_end] + tag + "\n" + text[body_end:]
    return text + "\n" + tag + "\n"

def main() -> None:
    if not INDEX.exists():
        raise SystemExit("index.html not found")

    text = INDEX.read_text(encoding="utf-8")

    text = re.sub(r'\s*<script\s+src="https://cdn\.tailwindcss\.com"></script>\s*', "\n", text)
    text = re.sub(r'\s*<script\s+src="assets/js/00-tailwind-config\.js"></script>\s*', "\n", text)

    if "assets/css/tailwind-built.css" not in text:
        text = insert_after_last_css(text, "assets/css/tailwind-built.css")
    if "assets/css/60-design-token-denoise.css" not in text:
        text = insert_after_last_css(text, "assets/css/60-design-token-denoise.css")

    text = insert_after_last_css(text, CSS_PATH)
    text = insert_before_body_end(text, JS_PATH)

    text = re.sub(
        r'<script src="assets/js/quant-main-display\.js(?:\?v=[^"]*)?"></script>',
        '<script src="assets/js/quant-main-display.js?v=no-chip-terminal"></script>',
        text,
    )

    # Collapse accidental duplicate terminal overlay references.
    text = re.sub(
        r'(\s*<link rel="stylesheet" href="assets/css/70-terminal-design-system\.css\?v=terminal-ds-1">\s*)+',
        '\n    <link rel="stylesheet" href="assets/css/70-terminal-design-system.css?v=terminal-ds-1">\n',
        text,
    )
    text = re.sub(
        r'(\s*<script src="assets/js/terminal-ui-polish\.js\?v=terminal-ds-1"></script>\s*)+',
        '\n    <script src="assets/js/terminal-ui-polish.js?v=terminal-ds-1"></script>\n',
        text,
    )

    INDEX.write_text(text, encoding="utf-8")
    print("OK applied terminal design-system overlay to index.html")

if __name__ == "__main__":
    main()
