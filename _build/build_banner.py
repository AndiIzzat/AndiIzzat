"""Build an animated SVG banner: static photo plate + keyword tiles that fade in.

The keywords are baked into the source PNG, so we rebuild a clean plate by
patching each label box with pixels copied from the same rows further along
the image (the photo is horizontally uniform banding, so this is seamless),
then re-composite the original label crops on top as separately animated
layers. This keeps the exact original typography instead of re-typesetting it.
"""
from PIL import Image
import base64, io, os

SRC = r"C:\Users\andii\Documents\iashari-profile\banner.png"
OUT = r"C:\Users\andii\Documents\iashari-profile\banner.svg"

im = Image.open(SRC).convert("RGB")
W, H = im.size

PAD = 5
# Label boxes are authored against a 1080px-wide export and scaled to whatever
# resolution the source actually is, so a 2x/3x re-export needs no re-measuring.
REF_W = 1080
SCALE = W / REF_W
# (name, x0, y0, x1, y1, patch_source_dx, fade_in_start_seconds)
LABELS = [
    ("ui/ux",     394, 155, 431, 170,  140, 0.4),
    ("visual",    195, 483, 237, 497,  140, 0.9),
    ("prototype", 835, 238, 908, 253, -150, 1.4),
    ("code",      581, 552, 623, 567,  150, 1.9),
]
if SCALE != 1:
    print(f"source is {SCALE:g}x the {REF_W}px reference - scaling label boxes")

def s(v):
    return int(round(v * SCALE))

boxes = []
for name, x0, y0, x1, y1, dx, t in LABELS:
    boxes.append((name, s(x0) - PAD, s(y0) - PAD, s(x1) + PAD + 1,
                  s(y1) + PAD + 1, s(dx), t))

# 1. Original label tiles (before we damage the plate).
tiles = []
for name, x0, y0, x1, y1, dx, t in boxes:
    tiles.append((name, x0, y0, x1 - x0, y1 - y0, im.crop((x0, y0, x1, y1)).copy(), t))

# 2. Clean plate: Laplace-diffuse each label box inward from its own borders.
#    Copying pixels from elsewhere leaves visible rectangles because the photo
#    has a horizontal falloff as well as horizontal banding; solving Laplace's
#    equation with the surrounding ring as a fixed boundary matches all four
#    edges exactly, so smooth gradients reconstruct seamlessly.
import numpy as np

arr = np.asarray(im).astype(np.float64)
for name, x0, y0, x1, y1, dx, t in boxes:
    r = 2  # boundary ring thickness
    sy0, sy1 = y0 - r, y1 + r
    sx0, sx1 = x0 - r, x1 + r
    region = arr[sy0:sy1, sx0:sx1].copy()
    hh, ww, _ = region.shape
    hole = np.zeros((hh, ww), dtype=bool)
    hole[r:hh - r, r:ww - r] = True

    for c in range(3):
        ch = region[:, :, c]
        # seed the hole with the mean of its boundary ring
        ring = ch[~hole]
        ch[hole] = ring.mean()
        for _ in range(1500):
            nb = np.zeros_like(ch)
            nb[1:-1, 1:-1] = (
                ch[:-2, 1:-1] + ch[2:, 1:-1] + ch[1:-1, :-2] + ch[1:-1, 2:]
            ) / 4.0
            ch[hole] = nb[hole]
        region[:, :, c] = ch
    arr[sy0:sy1, sx0:sx1] = region

plate = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

plate.save(r"C:\Users\andii\Documents\iashari-profile\_build\plate_check.png")

# 3. Encode plate as JPEG (smooth gradient photo -> JPEG beats PNG hugely).
buf = io.BytesIO()
# 4:4:4 (subsampling=0) matters here: the wordmark is thin light strokes on a
# dark gradient, and default 4:2:0 chroma halving fringes exactly that.
plate.save(buf, format="JPEG", quality=96, subsampling=0, optimize=True,
           progressive=True)
plate_b64 = base64.b64encode(buf.getvalue()).decode()
print(f"plate jpeg: {len(buf.getvalue())/1024:.0f} KB")

TOTAL = 6.0
FADE = 0.6
HOLD_END = 5.0
OUT_END = 5.6

def pct(t):
    return round(t / TOTAL * 100, 2)

css, layers = [], []
for i, (name, x, y, w, h, tile, t) in enumerate(tiles):
    tb = io.BytesIO()
    tile.save(tb, format="PNG", optimize=True)
    b64 = base64.b64encode(tb.getvalue()).decode()
    cls = f"k{i}"
    css.append(f"""
.{cls} {{ animation: f{i} {TOTAL}s ease-in-out infinite; opacity: 0; }}
@keyframes f{i} {{
  0%, {pct(t)}% {{ opacity: 0; }}
  {pct(t + FADE)}%, {pct(HOLD_END)}% {{ opacity: 1; }}
  {pct(OUT_END)}%, 100% {{ opacity: 0; }}
}}""")
    layers.append(
        f'<image class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" '
        f'xlink:href="data:image/png;base64,{b64}"/>'
    )
    print(f"tile {name:10s} {w}x{h} at ({x},{y})  {len(tb.getvalue())/1024:.1f} KB  in@{t}s")

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<style>
{"".join(css)}
@media (prefers-reduced-motion: reduce) {{
  .k0, .k1, .k2, .k3 {{ animation: none; opacity: 1; }}
}}
</style>
<image x="0" y="0" width="{W}" height="{H}" xlink:href="data:image/jpeg;base64,{plate_b64}"/>
{chr(10).join(layers)}
</svg>'''

with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"\nbanner.svg: {os.path.getsize(OUT)/1024:.0f} KB")
