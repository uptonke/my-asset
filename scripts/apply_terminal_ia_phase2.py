#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path
INDEX=Path("index.html")
CSS="assets/css/80-terminal-ia-phase2.css"
JS="assets/js/terminal-ia-phase2.js"
def insert_after_last_css(text,href):
    if href in text: return text
    tag=f'    <link rel="stylesheet" href="{href}?v=ia-phase2">'
    matches=list(re.finditer(r'^\s*<link\s+rel="stylesheet"\s+href="assets/css/[^"]+(?:\?v=[^"]*)?">\s*$',text,flags=re.M))
    if matches:
        m=matches[-1];return text[:m.end()]+"
"+tag+text[m.end():]
    head=text.find("</head>")
    if head!=-1: return text[:head]+tag+"
"+text[head:]
    raise RuntimeError("Cannot find </head>")
def insert_before_body_end(text,src):
    if src in text: return text
    tag=f'    <script src="{src}?v=ia-phase2"></script>'
    body_end=text.rfind("</body>")
    if body_end!=-1: return text[:body_end]+tag+"
"+text[body_end:]
    return text+"
"+tag+"
"
def main():
    if not INDEX.exists(): raise SystemExit("index.html not found")
    text=INDEX.read_text(encoding="utf-8")
    if 'rel="icon"' not in text and "rel='icon'" not in text:
        head=text.find("</head>")
        if head!=-1: text=text[:head]+'    <link rel="icon" href="data:,">
'+text[head:]
    text=insert_after_last_css(text,CSS)
    text=insert_before_body_end(text,JS)
    text=re.sub(r'(\s*<link rel="stylesheet" href="assets/css/80-terminal-ia-phase2\.css\?v=ia-phase2">\s*)+','
    <link rel="stylesheet" href="assets/css/80-terminal-ia-phase2.css?v=ia-phase2">
',text)
    text=re.sub(r'(\s*<script src="assets/js/terminal-ia-phase2\.js\?v=ia-phase2"></script>\s*)+','
    <script src="assets/js/terminal-ia-phase2.js?v=ia-phase2"></script>
',text)
    INDEX.write_text(text,encoding="utf-8")
    print("OK applied terminal IA phase2 through step 4.")
if __name__=="__main__": main()
