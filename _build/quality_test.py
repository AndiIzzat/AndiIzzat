"""Measure where JPEG encoding hurts, and compare candidate settings."""
from PIL import Image
import numpy as np, io

im = Image.open(r"C:\Users\andii\Documents\iashari-profile\banner.png").convert("RGB")
a = np.asarray(im).astype(np.float64)

# Regions that matter most: thin outlined wordmark, smooth sky gradient.
REGIONS = {
    "wordmark (thin strokes)": (60, 260, 1020, 400),
    "sky (smooth gradient)":   (0, 0, 1080, 240),
    "label [prototype]":       (830, 233, 914, 259),
    "whole image":             (0, 0, 1080, 721),
}

def err(enc, box):
    x0, y0, x1, y1 = box
    d = np.abs(np.asarray(enc).astype(np.float64)[y0:y1, x0:x1] - a[y0:y1, x0:x1])
    return d.mean(), d.max()

print(f"{'setting':28s} {'KB':>6s}  " + "  ".join(f"{k.split()[0]:>10s}" for k in REGIONS))
for label, kw in [
    ("q86 4:2:0 (current)", dict(quality=86, subsampling=2)),
    ("q92 4:2:0",           dict(quality=92, subsampling=2)),
    ("q92 4:4:4",           dict(quality=92, subsampling=0)),
    ("q96 4:4:4",           dict(quality=96, subsampling=0)),
    ("q98 4:4:4",           dict(quality=98, subsampling=0)),
]:
    buf = io.BytesIO()
    im.save(buf, format="JPEG", optimize=True, progressive=True, **kw)
    kb = len(buf.getvalue()) / 1024
    enc = Image.open(io.BytesIO(buf.getvalue())).convert("RGB")
    cells = "  ".join(f"{err(enc, b)[0]:10.2f}" for b in REGIONS.values())
    print(f"{label:28s} {kb:6.0f}  {cells}")

# PNG reference
buf = io.BytesIO(); im.save(buf, format="PNG", optimize=True)
print(f"{'PNG (lossless)':28s} {len(buf.getvalue())/1024:6.0f}  " + "  ".join(f"{0.0:10.2f}" for _ in REGIONS))
print("\n(values = mean abs pixel error per region; lower is better)")
print(f"source resolution: {im.size[0]}x{im.size[1]}")
print("README content column is ~890 CSS px; a 2x display needs ~1780px to stay sharp.")
