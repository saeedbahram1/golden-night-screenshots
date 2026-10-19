#!/usr/bin/env python3
"""Build polished 1280x800 Chrome Web Store screenshots, preserving the real popup."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import zipfile
import math

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "store-ready"
OUT.mkdir(exist_ok=True)

SOURCES = [
    ("Screenshot (13).png", "01-Golden-Night-Enabled.png"),
    ("Screenshot (14).png", "02-Golden-Night-Settings.png"),
    ("Screenshot (12).png", "03-Chrome-Dark-Mode-Guide.png"),
    ("Screenshot (15).png", "04-Golden-Night-Disabled.png"),
    ("Screenshot (11).png", "05-Golden-Night-Help-Tip.png"),
]
CANVAS_W, CANVAS_H = 1280, 800
FRAME_X, FRAME_Y = 30, 53
FRAME_W, FRAME_H = 1220, 694
TOOLBAR_H = 77
VIEWPORT_W, VIEWPORT_H = 1220, 616
SOURCE_CROP = (0, 105, 1810, 1018)  # Excludes old Windows frame/taskbar; popup stays in source pixels.

def font(size):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()

FONT_SMALL = font(12)
FONT_TAB = font(12)
FONT_URL = font(12)

def draw_icon(draw, kind, cx, cy, color=(190, 192, 201, 255), scale=1.0):
    s = scale
    if kind == "back":
        draw.line((cx+4*s, cy-6*s, cx-3*s, cy, cx+4*s, cy+6*s), fill=color, width=max(1, int(2*s)), joint="curve")
        draw.line((cx-3*s, cy, cx+7*s, cy), fill=color, width=max(1, int(2*s)))
    elif kind == "forward":
        draw.line((cx-4*s, cy-6*s, cx+3*s, cy, cx-4*s, cy+6*s), fill=color, width=max(1, int(2*s)), joint="curve")
        draw.line((cx+3*s, cy, cx-7*s, cy), fill=color, width=max(1, int(2*s)))
    elif kind == "reload":
        draw.arc((cx-7*s, cy-7*s, cx+7*s, cy+7*s), 35, 315, fill=color, width=max(1, int(2*s)))
        draw.polygon([(cx+6*s,cy-7*s),(cx+7*s,cy+1*s),(cx+1*s,cy-2*s)], fill=color)
    elif kind == "puzzle":
        # A restrained puzzle-piece glyph.
        draw.rounded_rectangle((cx-6*s,cy-5*s,cx+6*s,cy+6*s), radius=2*s, outline=color, width=max(1,int(1.5*s)))
        draw.arc((cx-2*s,cy-8*s,cx+4*s,cy-2*s), 180, 360, fill=color, width=max(1,int(1.5*s)))
    elif kind == "menu":
        for dy in (-4,0,4):
            draw.ellipse((cx-1.3*s, cy+(dy-1.3)*s, cx+1.3*s, cy+(dy+1.3)*s), fill=color)
    elif kind == "moon":
        draw.ellipse((cx-6*s,cy-6*s,cx+6*s,cy+6*s), fill=(255,207,34,255))
        draw.ellipse((cx-2*s,cy-8*s,cx+8*s,cy+2*s), fill=(39,39,46,255))

def make_background():
    image = Image.new("RGB", (CANVAS_W, CANVAS_H))
    pix = image.load()
    for y in range(CANVAS_H):
        t = y / max(1, CANVAS_H-1)
        base = tuple(round(a*(1-t)+b*t) for a,b in zip((15,16,21),(23,23,30)))
        for x in range(CANVAS_W):
            # A very subtle warm glow behind the browser, kept low-contrast.
            dx = (x - 1000) / 520
            dy = (y - 250) / 470
            glow = max(0.0, 1.0 - math.sqrt(dx*dx + dy*dy)) * 4
            pix[x,y] = (min(255, int(base[0]+glow)), min(255,int(base[1]+glow*0.78)), min(255,int(base[2]+glow*0.16)))
    return image

def process(source_path: Path, output_name: str):
    src = Image.open(source_path).convert("RGB")
    if src.size != (1920, 1080):
        raise ValueError(f"{source_path.name} expected 1920x1080, got {src.size}")
    # Keep the website view and extension popup from the original screenshot. Only the
    # surrounding Windows browser UI/taskbar is replaced with a macOS-style dark frame.
    viewport = src.crop(SOURCE_CROP).resize((VIEWPORT_W, VIEWPORT_H), Image.Resampling.LANCZOS)

    window = Image.new("RGBA", (FRAME_W, FRAME_H), (24,25,31,255))
    # The source browser viewport remains unpainted, other than uniform scaling to target dimensions.
    window.paste(viewport, (0, TOOLBAR_H))

    d = ImageDraw.Draw(window, "RGBA")
    # macOS-style dark tab strip and address bar.
    d.rectangle((0,0,FRAME_W,35), fill=(31,32,39,255))
    d.rectangle((0,35,FRAME_W,TOOLBAR_H), fill=(37,38,45,255))
    d.line((0,TOOLBAR_H-1,FRAME_W,TOOLBAR_H-1), fill=(10,11,14,255), width=1)
    # Window traffic lights.
    for cx, col in ((24,(255,95,86,255)),(43,(255,189,46,255)),(62,(39,201,63,255))):
        d.ellipse((cx-5.5,14-5.5,cx+5.5,14+5.5), fill=col, outline=(0,0,0,40), width=1)
    # Active tab.
    d.rounded_rectangle((93,4,365,34), radius=8, fill=(49,50,58,255))
    d.ellipse((105,11,118,24), fill=(228,230,235,255))
    d.text((110,10), "G", font=font(10), fill=(66,133,244,255))
    d.text((126,10), "translate - Google Search", font=FONT_TAB, fill=(231,232,237,255))
    d.line((350,14,357,21), fill=(155,157,165,255), width=1)
    d.line((357,14,350,21), fill=(155,157,165,255), width=1)
    d.line((386,15,398,15), fill=(167,169,177,255), width=1)
    d.line((392,9,392,21), fill=(167,169,177,255), width=1)

    # Navigation controls.
    draw_icon(d, "back", 24, 56)
    draw_icon(d, "forward", 54, 56, (119,121,130,255))
    draw_icon(d, "reload", 84, 56)
    # URL bar.
    d.rounded_rectangle((112,42,720,69), radius=13, fill=(24,25,31,255), outline=(57,58,67,255), width=1)
    d.ellipse((124,49,136,61), outline=(153,157,166,255), width=1)
    d.line((133,59,138,64), fill=(153,157,166,255), width=1)
    d.text((147,49), "google.com/search?q=translate", font=FONT_URL, fill=(193,195,204,255))
    # Extension area; Golden Night icon is centered above the untouched popup.
    d.rounded_rectangle((746,40,797,71), radius=8, fill=(51,48,31,255), outline=(128,102,22,255), width=1)
    draw_icon(d, "moon", 772, 55, scale=1.0)
    draw_icon(d, "puzzle", 829, 56, (190,192,201,255), 1.0)
    d.line((851,45,851,66), fill=(67,68,77,255), width=1)
    # Other neutral browser controls.
    d.ellipse((872,49,886,63), outline=(174,176,184,255), width=1)
    d.arc((873,50,885,62), 0, 180, fill=(174,176,184,255), width=1)
    draw_icon(d, "menu", 1194, 56, (190,192,201,255), 1.0)

    # Add a subtle, native-feeling scrollbar on the right edge of the content viewport.
    d.rounded_rectangle((1211,TOOLBAR_H+10,1216,TOOLBAR_H+602), radius=2, fill=(47,48,55,180))
    d.rounded_rectangle((1211,TOOLBAR_H+24,1216,TOOLBAR_H+136), radius=2, fill=(101,103,113,205))

    # Fine border plus rounded window corners.
    d.rounded_rectangle((0,0,FRAME_W-1,FRAME_H-1), radius=15, outline=(65,66,75,255), width=1)
    mask = Image.new("L", (FRAME_W, FRAME_H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0,0,FRAME_W-1,FRAME_H-1), radius=15, fill=255)
    window.putalpha(mask)

    # Shadow and background canvas.
    canvas = make_background().convert("RGBA")
    shadow = Image.new("RGBA", (CANVAS_W,CANVAS_H), (0,0,0,0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((FRAME_X-1,FRAME_Y+5,FRAME_X+FRAME_W+1,FRAME_Y+FRAME_H+7), radius=19, fill=(0,0,0,160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas = Image.alpha_composite(canvas, shadow)
    canvas.alpha_composite(window, (FRAME_X, FRAME_Y))

    # Export an optimized true-color PNG at Chrome Web Store's recommended screenshot size.
    destination = OUT / output_name
    canvas.convert("RGB").save(destination, format="PNG", optimize=True)
    with Image.open(destination) as check:
        if check.size != (1280,800):
            raise RuntimeError(f"Wrong output dimensions: {check.size}")
    return destination

def main():
    made = []
    for source, out_name in SOURCES:
        src_path = ROOT / source
        if not src_path.exists():
            raise FileNotFoundError(f"Missing source screenshot: {src_path}")
        made.append(process(src_path, out_name))

    readme = OUT / "README.txt"
    readme.write_text(
        "Golden Night — Chrome Web Store screenshots\n"
        "All 5 images are PNG, 1280 x 800 pixels (16:10).\n"
        "The original webpage and Golden Night popup are preserved from the submitted screenshots; "
        "the Windows browser frame/taskbar was replaced by a macOS-inspired dark browser frame.\n\n"
        "Suggested upload order:\n"
        "1. 01-Golden-Night-Enabled.png\n"
        "2. 02-Golden-Night-Settings.png\n"
        "3. 03-Chrome-Dark-Mode-Guide.png\n"
        "4. 04-Golden-Night-Disabled.png\n"
        "5. 05-Golden-Night-Help-Tip.png\n",
        encoding="utf-8"
    )
    archive = ROOT / "Golden-Night-Chrome-Web-Store-Screenshots.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=8) as z:
        for p in made:
            z.write(p, arcname=p.name)
        z.write(readme, arcname=readme.name)
    print(f"Created {len(made)} screenshots and {archive.name}")
    for p in made:
        with Image.open(p) as im:
            print(f"{p.name}: {im.size}, {p.stat().st_size} bytes")
    print(f"ZIP: {archive.stat().st_size} bytes")

if __name__ == "__main__":
    main()
