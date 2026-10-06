"""Step 3: turn a photo into ASCII art (assets/portrait.txt).

Usage: python scripts/ascii_art.py [photo] [width]
If no photo exists, renders the configured name as a block-letter fallback.
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

from common import ASSETS, ROOT, load_config

# Dark -> light. Text is drawn light-on-dark, so dense glyphs = bright pixels.
RAMP = " .'`^,:;Il!i~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
SIMPLE_RAMP = " .:-=+*#%@"  # cleaner for flat graphics like the name fallback
CHAR_ASPECT = 0.55  # monospace glyphs are ~2x taller than wide


def prepare(img, invert=False):
    img = ImageOps.exif_transpose(img).convert("L")
    if invert:  # light-background photos: make the background blank
        img = ImageOps.invert(img)
    img = ImageOps.autocontrast(img, cutoff=2)
    img = ImageOps.equalize(img)
    return img.filter(ImageFilter.SHARPEN)


def fallback_image(text):
    font = None
    for name in ("DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf"):
        try:
            font = ImageFont.truetype(name, 220)
            break
        except OSError:
            continue
    font = font or ImageFont.load_default()
    box = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0] + 40, box[3] - box[1] + 40
    img = Image.new("L", (w, h), 0)
    ImageDraw.Draw(img).text((20 - box[0], 20 - box[1]), text, fill=255, font=font)
    return img


def to_ascii(img, width, ramp=RAMP):
    height = max(1, round(img.height / img.width * width * CHAR_ASPECT))
    small = np.asarray(img.resize((width, height), Image.LANCZOS), dtype=np.float32) / 255
    idx = (small * (len(ramp) - 1)).round().astype(int)
    lines = ["".join(ramp[i] for i in row).rstrip() for row in idx]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def main():
    cfg = load_config()
    photo = ROOT / (sys.argv[1] if len(sys.argv) > 1 else cfg.get("photo", "assets/photo.jpg"))
    width = int(sys.argv[2]) if len(sys.argv) > 2 else cfg.get("ascii_width", 64)
    if photo.exists():
        art = to_ascii(prepare(Image.open(photo), cfg.get("ascii_invert", False)), width)
    else:
        print(f"no photo at {photo}, using name fallback")
        art = to_ascii(fallback_image(cfg.get("name", cfg["github_user"])), width, SIMPLE_RAMP)
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "portrait.txt").write_text(art + "\n", encoding="utf-8")
    print(art)


if __name__ == "__main__":
    main()
