#!/usr/bin/env python3
from pathlib import Path
import re

p = Path("index.html")
text = p.read_text(encoding="utf-8")
text = re.sub(r'\s*<link rel="stylesheet" href="assets/css/70-terminal-design-system\.css\?v=terminal-ds-1">\s*', "\n", text)
text = re.sub(r'\s*<script src="assets/js/terminal-ui-polish\.js\?v=terminal-ds-1"></script>\s*', "\n", text)
p.write_text(text, encoding="utf-8")
print("OK removed terminal design-system overlay references from index.html")
