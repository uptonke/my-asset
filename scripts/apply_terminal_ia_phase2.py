#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

INDEX = Path("index.html")
CSS = "assets/css/80-terminal-ia-phase2.css"
TYPOGRAPHY_CSS = "assets/css/90-typography.css"
JS = "assets/js/terminal-ia-phase2.js"


def insert_after_last_css(text: str, href: str, version: str = "ia-phase2") -> str:
    if href in text:
        return text

    tag = f'    <link rel="stylesheet" href="{href}?v={version}">'
    pattern = r'^\s*<link\s+rel="stylesheet"\s+href="assets/css/[^"]+(?:\?v=[^"]*)?">\s*$'
    matches = list(re.finditer(pattern, text, flags=re.M))

    if matches:
        m = matches[-1]
        return text[: m.end()] + "\n" + tag + text[m.end() :]

    head = text.find("</head>")
    if head != -1:
        return text[:head] + tag + "\n" + text[head:]

    raise RuntimeError("Cannot find stylesheet insertion point in index.html")


def insert_before_body_end(text: str, src: str) -> str:
    if src in text:
        return text

    tag = f'    <script src="{src}?v=ia-phase2"></script>'
    body_end = text.rfind("</body>")

    if body_end != -1:
        return text[:body_end] + tag + "\n" + text[body_end:]

    return text + "\n" + tag + "\n"


def main() -> None:
    if not INDEX.exists():
        raise SystemExit("index.html not found")

    text = INDEX.read_text(encoding="utf-8")

    if 'rel="icon"' not in text and "rel='icon'" not in text:
        head = text.find("</head>")
        if head != -1:
            text = text[:head] + '    <link rel="icon" href="data:,">\n' + text[head:]

    text = insert_after_last_css(text, CSS, "ia-phase2")
    text = insert_after_last_css(text, TYPOGRAPHY_CSS, "typography-1")
    text = insert_before_body_end(text, JS)

    text = re.sub(
        r'(\s*<link rel="stylesheet" href="assets/css/80-terminal-ia-phase2\.css\?v=ia-phase2">\s*)+',
        '\n    <link rel="stylesheet" href="assets/css/80-terminal-ia-phase2.css?v=ia-phase2">\n',
        text,
    )
    text = re.sub(
        r'(\s*<link rel="stylesheet" href="assets/css/90-typography\.css\?v=typography-1">\s*)+',
        '\n    <link rel="stylesheet" href="assets/css/90-typography.css?v=typography-1">\n',
        text,
    )
    text = re.sub(
        r'(\s*<script src="assets/js/terminal-ia-phase2\.js\?v=ia-phase2"></script>\s*)+',
        '\n    <script src="assets/js/terminal-ia-phase2.js?v=ia-phase2"></script>\n',
        text,
    )

    INDEX.write_text(text, encoding="utf-8")
    print("OK applied terminal IA phase2 and typography stylesheet.")


if __name__ == "__main__":
    main()

