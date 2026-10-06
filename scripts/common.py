"""Shared helpers: config loading, palette, SVG escaping."""
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# GitHub-dark inspired palette, readable on both light and dark READMEs
BG = "#0d1117"
BORDER = "#30363d"
FG = "#c9d1d9"
DIM = "#8b949e"
ACCENT = "#58a6ff"
GREEN = "#3fb950"
YELLOW = "#d29922"
FONT = "'JetBrains Mono','Fira Code',Consolas,'Courier New',monospace"


def load_config():
    with open(ROOT / "config.json", encoding="utf-8") as f:
        return json.load(f)


def esc(text):
    return escape(str(text), {'"': "&quot;"})


def write(name, content):
    ASSETS.mkdir(exist_ok=True)
    path = ASSETS / name
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")
