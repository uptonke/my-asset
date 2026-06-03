#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

INDEX = Path("index.html")
CSS = "assets/css/80-terminal-ia-phase2.css"
JS = "assets/js/terminal-ia-phase2.js"


def insert_after_last_css(text: str, href: str) -> str:
    if href in text:
        return text
    tag = f'    <link rel="stylesheet" href="{href}?v=ia-phase2">'
    pattern = r'^\s*<link\s+rel="stylesheet"\s+href="assets/css/[^"]+(?:\?v=[^"]*)?">\s*$'
    matches = list(re.finditer(pattern, text, flags=re.M))
    if matches:
        m = matches[-1]
        return text[:m.end()] + "\n" + tag + text[m.end():]
    head = text.find("</head>")
    if head != -1:
        return text[:head] + tag +