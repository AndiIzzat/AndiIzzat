"""Montage the four inpainted regions at 1:1 with surrounding context,
so any unconverged blotch or seam is obvious."""
from PIL import Image

plate = Image.open(r"C:\Users\andii\Documents\iashari-profile\_build\plate_check.png")
W, _ = plate.size
sc = W / 1080
CTX = 60

BOXES = [("ui/ux", 394,155,431,170), ("visual",195,483,237,497),
         ("prototype",835,238,908,253), ("code",581,552,623,567)]

crops = []
for name, x0, y0, x1, y1 in BOXES:
    a = (int(x0*sc)-CTX, int(y0*sc)-CTX, int(x1*sc)+CTX, int(y1*sc)+CTX)
    crops.append(plate.crop(a))

pad = 12
w = max(c.width for c in crops)
h = sum(c.height for c in crops) + pad*(len(crops)+1)
out = Image.new("RGB", (w + pad*2, h), (255, 0, 255))  # magenta gutters
y = pad
for c in crops:
    out.paste(c, (pad, y))
    y += c.height + pad
out.save(r"C:\Users\andii\Documents\iashari-profile\_build\patch_montage.png")
print("montage:", out.size, "- regions top to bottom:", ", ".join(b[0] for b in BOXES))
