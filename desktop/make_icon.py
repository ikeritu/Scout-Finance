"""Draws desktop/scout_finance.ico (a rounded teal square with the letters SF and a small amber spark). Run it only to redraw the icon:
    .venv\\Scripts\\python.exe desktop\\make_icon.py
Needs Pillow (already installed with Streamlit) and the Segoe UI Bold font that ships with Windows."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 512
OUT = Path(__file__).with_name("scout_finance.ico")
FONT = Path(r"C:\Windows\Fonts\segoeuib.ttf")


def gradient(size: int) -> Image.Image:
    top, bottom = (17, 94, 89), (8, 38, 52)  # deep teal to ink blue
    image = Image.new("RGB", (size, size))
    pixels = image.load()
    for y in range(size):
        mix = y / (size - 1)
        row = tuple(round(top[i] + (bottom[i] - top[i]) * mix) for i in range(3))
        for x in range(size):
            pixels[x, y] = row
    return image


def build() -> Image.Image:
    base = gradient(SIZE).convert("RGBA")
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), radius=112, fill=255)
    base.putalpha(mask)
    draw = ImageDraw.Draw(base)
    font = ImageFont.truetype(str(FONT), 270)
    left, top, right, bottom = draw.textbbox((0, 0), "SF", font=font)
    draw.text(((SIZE - (right - left)) / 2 - left, (SIZE - (bottom - top)) / 2 - top + 8), "SF", font=font, fill=(244, 248, 247, 255))
    draw.ellipse((372, 82, 432, 142), fill=(245, 176, 65, 255))  # the spark: an explosive move
    return base


if __name__ == "__main__":
    build().save(OUT, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"wrote {OUT.name}")
