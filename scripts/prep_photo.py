"""Step 3a: prep a portrait photo for ASCII conversion (run locally, once per photo).

  python scripts/prep_photo.py source-photo.jpg   ->  source-prepped.png

1. Remove the background (rembg) so only the subject is left.
2. Boost local contrast with CLAHE so a flatly lit face gets real highlights/shadows.
3. Composite onto pure white so the background maps to spaces in the ASCII ramp.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source-prepped.png"


def main():
    src = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "source-photo.jpg")
    img = ImageOps.exif_transpose(Image.open(src)).convert("RGBA")

    try:
        from rembg import remove
        img = remove(img)
    except ImportError:
        print("rembg not installed; keeping the original background")

    alpha = np.asarray(img.getchannel("A"), dtype=np.float32) / 255
    gray = np.asarray(img.convert("L"))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray).astype(np.float32)

    # composite onto white
    out = gray * alpha + 255 * (1 - alpha)

    # crop to the subject's bounding box (plus a little margin)
    ys, xs = np.where(alpha > 0.1)
    if len(xs):
        m = int(0.04 * max(out.shape))
        y0, y1 = max(ys.min() - m, 0), min(ys.max() + m, out.shape[0])
        x0, x1 = max(xs.min() - m, 0), min(xs.max() + m, out.shape[1])
        out = out[y0:y1, x0:x1]

    Image.fromarray(out.clip(0, 255).astype(np.uint8), "L").save(OUT)
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
