"""Recomposite plate + tiles at their SVG coords and diff against the original.

If the tiles are positioned correctly, the fully-faded-in frame of the SVG is
pixel-identical to the source banner (modulo JPEG loss on the plate).
"""
from PIL import Image, ImageChops
import numpy as np, re, base64, io

svg = open(r"C:\Users\andii\Documents\iashari-profile\banner.svg", encoding="utf-8").read()

plate_b64 = re.search(r'data:image/jpeg;base64,([^"]+)', svg).group(1)
plate = Image.open(io.BytesIO(base64.b64decode(plate_b64))).convert("RGB")
print("plate decoded:", plate.size)

comp = plate.copy()
tiles = re.findall(
    r'<image class="k\d+" x="(\d+)" y="(\d+)" width="(\d+)" height="(\d+)" '
    r'xlink:href="data:image/png;base64,([^"]+)"/>', svg)
print("tiles found:", len(tiles))
for x, y, w, h, b64 in tiles:
    t = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
    assert t.size == (int(w), int(h)), f"tile size mismatch {t.size} vs {w}x{h}"
    comp.paste(t, (int(x), int(y)))

orig = Image.open(r"C:\Users\andii\Documents\iashari-profile\banner.png").convert("RGB")
assert comp.size == orig.size, f"{comp.size} vs {orig.size}"

d = np.abs(np.asarray(comp).astype(int) - np.asarray(orig).astype(int))
print(f"composite vs original -> mean abs diff {d.mean():.2f}, max {d.max()}")

# Diff restricted to the label boxes: this is what proves placement.
# Boxes are authored at 1080px wide, so scale them to the actual export.
sc = comp.size[0] / 1080
for name, x0, y0, x1, y1 in [("ui/ux",389,150,437,176),("visual",190,478,243,503),
                             ("prototype",830,233,914,259),("code",576,547,629,573)]:
    sub = d[int(y0*sc):int(y1*sc), int(x0*sc):int(x1*sc)]
    print(f"  {name:10s} box mean {sub.mean():5.2f}  max {sub.max():3d}")

# Placement sanity: if a tile were misplaced, the label would be missing from
# its true location and duplicated elsewhere, spiking the error far above the
# plate's JPEG noise floor.
print(f"\nworst pixel error anywhere: {d.max()}  (JPEG noise floor, not misplacement, if < ~40)")

comp.save(r"C:\Users\andii\Documents\iashari-profile\_build\composite_check.png")
