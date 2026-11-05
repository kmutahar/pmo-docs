"""Draw the plugin icon (a clipboard with a checklist) with Pillow. Maintainer tool, not shipped, not needed to use the skill.
Run once: python3 dev/make_icon.py   (writes skills/pmo-docs/.claude-plugin/icon.png, 512x512)"""
from pathlib import Path
from PIL import Image, ImageDraw

S, K = 512, 4  # final size, supersampling factor for smooth edges
im = Image.new("RGBA", (S * K, S * K), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
u = lambda v: int(v * K)
d.rounded_rectangle([0, 0, u(S) - 1, u(S) - 1], radius=u(96), fill="#1f4e79")  # background
d.rounded_rectangle([u(132), u(104), u(380), u(424)], radius=u(24), fill="#ffffff")  # board
d.rounded_rectangle([u(194), u(80), u(318), u(136)], radius=u(18), fill="#9fc5e8")  # clip
d.rounded_rectangle([u(222), u(92), u(290), u(122)], radius=u(10), fill="#1f4e79")
for i, y in enumerate((190, 270, 350)):  # three rows: box with a tick, then a line
    d.rounded_rectangle([u(164), u(y), u(204), u(y + 40)], radius=u(8), outline="#1f4e79", width=u(6))
    if i < 2:
        d.line([(u(172), u(y + 21)), (u(182), u(y + 31)), (u(198), u(y + 8))], fill="#2e8b57", width=u(7), joint="curve")
    d.rounded_rectangle([u(224), u(y + 12), u(348), u(y + 28)], radius=u(8), fill="#b7c4d1")
out = Path(__file__).resolve().parents[1] / "skills/pmo-docs/.claude-plugin/icon.png"
im.resize((S, S), Image.LANCZOS).save(out, optimize=True)
print(out, out.stat().st_size, "bytes")
