#!/usr/bin/env python3
"""INKWITNESS graphics: avatar, banner, title card, end card, thumbnail, paper texture.

All type is typeset with Pillow in the brand fonts. Nothing on these assets comes
from an image model, which is why the letters are always crisp.
"""
from __future__ import annotations

import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "brand", "fonts")

INK = (16, 21, 20)
TEAL = (27, 52, 51)
SLATE = (62, 85, 83)
BONE = (237, 228, 211)
AMBER = (231, 163, 76)
RUST = (162, 69, 47)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def serif(size: int, weight: str = "SemiBold") -> ImageFont.FreeTypeFont:
    return font(f"Fraunces-{weight}.ttf", size)


def sans(size: int, weight: str = "Regular") -> ImageFont.FreeTypeFont:
    return font(f"InterTight-{weight}.ttf", size)


# ---------------------------------------------------------------- primitives

def letterspaced(draw, xy, text, fnt, fill, tracking=0.14, anchor_left=True):
    """Draw uppercase type with manual letterspacing. Returns (width, height)."""
    x, y = xy
    space = fnt.size * tracking
    widths = []
    for ch in text:
        bbox = draw.textbbox((0, 0), ch, font=fnt)
        widths.append(bbox[2] - bbox[0])
    total = sum(widths) + space * max(0, len(text) - 1)
    if not anchor_left:
        x -= total
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += w + space
    return total, fnt.size


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _fbm(size, octaves=5, seed=0, base=4):
    """Multi-octave value noise: the backbone of every organic texture here."""
    rng = np.random.default_rng(seed)
    w, h = size
    out = np.zeros((h, w), dtype=np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        gw = max(2, base * 2 ** o)
        gh = max(2, int(gw * h / w))
        grid = rng.normal(0, 1, (gh, gw)).astype(np.float32)
        layer = np.array(Image.fromarray(grid).resize((w, h), Image.BICUBIC))
        out += layer * amp
        total += amp
        amp *= 0.5
    out /= total
    out -= out.min()
    return out / max(1e-6, out.max())


def paper(size, base=BONE, grain=9, seed=7):
    """Warm paper: soft blotches, fine fibre grain, photographed vignette."""
    w, h = size
    rng = np.random.default_rng(seed)
    blotch = _fbm(size, octaves=5, seed=seed)
    arr = np.zeros((h, w, 3), dtype=np.float32)
    arr[..., 0], arr[..., 1], arr[..., 2] = base
    arr += (blotch[..., None] - 0.5) * 16.0
    arr += rng.normal(0, grain, (h, w, 1))
    # a few long paper fibres, very low amplitude
    for _ in range(70):
        y = int(rng.integers(0, h))
        th = int(rng.integers(1, 3))
        arr[y:y + th, :, :] += float(rng.uniform(-4, 5))
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.45))

    vig = Image.new("L", size, 0)
    ImageDraw.Draw(vig).ellipse([-w * 0.18, -h * 0.28, w * 1.18, h * 1.28], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(min(w, h) * 0.16))
    img = Image.composite(img, Image.blend(img, Image.new("RGB", size, (146, 133, 113)), 0.42), vig)
    return img


def ink_wash(size, seed=3):
    """Deep ink field: wash blotches generated small and upscaled, so no banding."""
    w, h = size
    sw, sh = max(64, w // 6), max(36, h // 6)
    a = _fbm((sw, sh), octaves=5, seed=seed)
    b = _fbm((sw, sh), octaves=4, seed=seed + 11)
    c = np.array(Image.fromarray(_fbm((sw // 2, sh // 2), octaves=3, seed=seed + 29)).resize((sw, sh), Image.LANCZOS))

    mix = np.clip(0.10 + 0.62 * a + 0.30 * c, 0, 1)[..., None]
    ink = np.array(INK, dtype=np.float32)
    teal = np.array(TEAL, dtype=np.float32)
    arr = ink * (1 - mix) + teal * mix
    arr *= (0.55 + 0.95 * b)[..., None]

    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).resize((w, h), Image.LANCZOS)

    full = np.array(img, dtype=np.float32)
    full += np.random.default_rng(seed).normal(0, 2.6, (h, w, 1))
    img = Image.fromarray(np.clip(full, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.5))

    vig = Image.new("L", size, 0)
    ImageDraw.Draw(vig).ellipse([-w * 0.22, -h * 0.30, w * 1.22, h * 1.30], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(min(w, h) * 0.22))
    img = Image.composite(img, Image.new("RGB", size, (5, 8, 8)), vig)
    return img


def lantern_glow(size, center, radius, strength=1.0):
    """RGBA radial amber glow for compositing over ink."""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - center[0]) ** 2 + (yy - center[1]) ** 2) / radius
    falloff = np.clip(1.0 - d, 0, 1) ** 2.4
    rgb = np.array(AMBER, dtype=np.float32)
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[..., 0] = rgb[0]
    arr[..., 1] = rgb[1]
    arr[..., 2] = rgb[2]
    arr[..., 3] = np.clip(falloff * 255 * strength, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def frame_rules(img, inset=46, color=INK, alpha=120, tick=26):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w, h = img.size
    c = color + (alpha,)
    d.rectangle([inset, inset, w - inset, h - inset], outline=c, width=2)
    for (x, y, dx, dy) in [(inset, inset, 1, 1), (w - inset, inset, -1, 1),
                           (inset, h - inset, 1, -1), (w - inset, h - inset, -1, -1)]:
        d.line([x, y, x + dx * tick, y], fill=c, width=4)
        d.line([x, y, x, y + dy * tick], fill=c, width=4)
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


# ---------------------------------------------------------------- assets

def build_profile():
    src = Image.open(os.path.join(ROOT, "brand/logo/profile-raw.png")).convert("RGB")
    side = min(src.size)
    src = src.crop(((src.width - side) // 2, (src.height - side) // 2,
                    (src.width + side) // 2, (src.height + side) // 2))
    # kill the scanned-paper margin so the ink fills the circular avatar
    m = int(side * 0.085)
    src = src.crop((m, m, side - m, side - m))
    src = src.resize((1024, 1024), Image.LANCZOS)
    out = os.path.join(ROOT, "brand/logo/profile-1024.png")
    src.save(out, quality=96)
    print("wrote", out)
    # circular-safe preview (YouTube crops to a circle)
    mask = Image.new("L", (1024, 1024), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 1023, 1023], fill=255)
    prev = Image.new("RGB", (1024, 1024), INK)
    prev.paste(src, (0, 0), mask)
    prev.save(os.path.join(ROOT, "brand/logo/profile-circle-preview.png"))


def build_banner():
    W, H = 2560, 1440
    img = ink_wash((W, H))
    img = Image.alpha_composite(img.convert("RGBA"), lantern_glow((W, H), (700, 760), 900, 0.16)).convert("RGB")

    logo = Image.open(os.path.join(ROOT, "brand/logo/profile-1024.png")).convert("RGB")
    logo = logo.resize((300, 300), Image.LANCZOS)
    mask = Image.new("L", (300, 300), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 299, 299], fill=255)
    ring = Image.new("RGBA", (316, 316), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([0, 0, 315, 315], outline=BONE + (140,), width=3)
    img = img.convert("RGBA")
    img.paste(logo, (600, 560), mask)
    img.alpha_composite(ring, (592, 552))

    d = ImageDraw.Draw(img)
    name_f = serif(132, "Black")
    letterspaced(d, (975, 596), "INKWITNESS", name_f, BONE, tracking=0.06)
    d.line([(978, 762), (1560, 762)], fill=AMBER, width=3)
    tag_f = serif(56, "Regular")
    d.text((980, 790), "True stories that almost disappeared.", font=tag_f, fill=(216, 205, 187))
    small = sans(30, "SemiBold")
    letterspaced(d, (980, 872), "HAND-INKED DOCUMENTARY  ·  NEW EPISODE WEEKLY", small, SLATE, tracking=0.18)

    out = os.path.join(ROOT, "brand/logo/banner-2560.png")
    img.convert("RGB").save(out, quality=95)
    print("wrote", out)

    # safe-area guide for the owner: 1546x423 centred
    safe = Image.new("RGB", (W, H), INK)
    safe.paste(img.convert("RGB"), (0, 0))
    ds = ImageDraw.Draw(safe)
    ds.rectangle([(W - 1546) // 2, (H - 423) // 2, (W + 1546) // 2, (H + 423) // 2],
                 outline=(255, 60, 60), width=4)
    safe.save(os.path.join(ROOT, "brand/logo/banner-safearea-guide.png"), quality=92)


def build_title_card():
    W, H = 1920, 1080
    img = paper((W, H), seed=11)
    img = Image.alpha_composite(img.convert("RGBA"), lantern_glow((W, H), (1560, 250), 620, 0.10)).convert("RGB")
    d = ImageDraw.Draw(img)

    letterspaced(d, (150, 150), "INKWITNESS", sans(34, "SemiBold"), (60, 74, 72), tracking=0.22)
    letterspaced(d, (150, 208), "EPISODE 01  ·  CELTIC SEA  ·  1973", sans(24, "SemiBold"), RUST, tracking=0.20)

    title_f = serif(168, "Black")
    lines = ["1,575 FEET", "DOWN."]
    y = 420
    for ln in lines:
        d.text((146, y), ln, font=title_f, fill=INK)
        y += 172

    d.line([(152, y + 34), (152 + 300, y + 34)], fill=AMBER, width=6)
    sub_f = serif(62, "Italic")
    d.text((152, y + 66), "The rescue of Pisces III", font=sub_f, fill=TEAL)

    letterspaced(d, (152, 940), "TWO MEN  ·  480 METRES  ·  76 HOURS  ·  12 MINUTES OF AIR", sans(22, "SemiBold"), (92, 106, 104), tracking=0.16)

    img = frame_rules(img, inset=60, alpha=130)
    out = os.path.join(ROOT, "episodes/ep01-pisces-iii/images/card-title.png")
    img.save(out)
    print("wrote", out)


def build_end_card():
    W, H = 1920, 1080
    img = ink_wash((W, H), seed=5)
    img = Image.alpha_composite(img.convert("RGBA"), lantern_glow((W, H), (960, 1180), 760, 0.30)).convert("RGBA")

    d = ImageDraw.Draw(img)
    name_f = serif(128, "Black")
    tw = d.textlength("INKWITNESS", font=name_f)
    letterspaced(d, ((W - tw) / 2, 330), "INKWITNESS", name_f, BONE, tracking=0.04)

    d.line([(W / 2 - 140, 500), (W / 2 + 140, 500)], fill=AMBER, width=3)

    tag_f = serif(52, "Italic")
    tag = "True stories that almost disappeared."
    d.text(((W - d.textlength(tag, font=tag_f)) / 2, 540), tag, font=tag_f, fill=(214, 203, 184))

    sub = sans(26, "SemiBold")
    txt = "ONE TRUE STORY  ·  HAND-INKED  ·  EVERY WEEK"
    tw = sum(d.textlength(c, font=sub) + 26 * 0.18 for c in txt) - 26 * 0.18
    letterspaced(d, ((W - tw) / 2, 640), txt, sub, SLATE, tracking=0.18)

    # subscribe chip
    chip_f = sans(30, "SemiBold")
    label = "SUBSCRIBE"
    lw = sum(d.textlength(c, font=chip_f) + 30 * 0.20 for c in label) - 30 * 0.20
    bw, bh = lw + 92, 96
    x0, y0 = (W - bw) / 2, 740
    d.rectangle([x0, y0, x0 + bw, y0 + bh], outline=BONE + (230,), width=3)
    letterspaced(d, (x0 + 46, y0 + 28), label, chip_f, BONE, tracking=0.20)

    nx = sans(24, "SemiBold")
    next_txt = "NEXT EPISODE  ·  THE BYFORD DOLPHIN"
    tw = sum(d.textlength(c, font=nx) + 24 * 0.16 for c in next_txt) - 24 * 0.16
    letterspaced(d, ((W - tw) / 2, 900), next_txt, nx, RUST, tracking=0.16)

    img = img.convert("RGB")
    img = frame_rules(img, inset=60, color=BONE, alpha=60)
    out = os.path.join(ROOT, "episodes/ep01-pisces-iii/images/card-end.png")
    img.save(out)
    print("wrote", out)


def build_paper_texture():
    W, H = 1920, 1080
    rng = np.random.default_rng(21)
    base = np.full((H, W, 3), 128, dtype=np.float32)
    noise = rng.normal(0, 26, (H, W, 1)).repeat(3, axis=2)
    # streaks
    for _ in range(90):
        y = rng.integers(0, H)
        th = int(rng.integers(1, 5))
        base[y:y + th, :, :] += float(rng.uniform(-16, 16))
    arr = np.clip(base + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr).filter(ImageFilter.GaussianBlur(0.8))
    os.makedirs(os.path.join(ROOT, "assets/textures"), exist_ok=True)
    out = os.path.join(ROOT, "assets/textures/paper-grain.png")
    img.save(out)
    print("wrote", out)


def build_thumbnail(slug="ep01-pisces-iii"):
    """1280x720 cover. Left: the number. Right: the ascent plate."""
    W, H = 1280, 720
    plate_path = os.path.join(ROOT, "episodes", slug, "images", "plate-09-the-lift.png")
    bg = ink_wash((W, H), seed=9)
    if os.path.exists(plate_path):
        plate = Image.open(plate_path).convert("RGB")
        # cover-crop to the right 58% of the canvas
        target_w = int(W * 0.62)
        scale = max(target_w / plate.width, H / plate.height)
        plate = plate.resize((int(plate.width * scale) + 1, int(plate.height * scale) + 1), Image.LANCZOS)
        top = (plate.height - H) // 2
        left = max(0, plate.width - target_w - int(target_w * 0.18))  # keep the sub and Wick in frame
        plate = plate.crop((left, top, left + target_w, top + H))
        # feather the left edge over 240 px so the plate melts into the ink field
        m = Image.new("L", (target_w, H), 255)
        md = ImageDraw.Draw(m)
        for x in range(240):
            md.line([(x, 0), (x, H)], fill=int(255 * (x / 240) ** 1.35))
        bg.paste(plate, (W - target_w, 0), m)

    # ink scrim on the left so type always reads
    scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for x in range(W):
        a = int(max(0, 1 - x / (W * 0.72)) ** 1.2 * 250)
        sd.line([(x, 0), (x, H)], fill=INK + (a,))
    img = Image.alpha_composite(bg.convert("RGBA"), scrim)

    d = ImageDraw.Draw(img)
    letterspaced(d, (58, 54), "INKWITNESS", sans(20, "SemiBold"), (226, 214, 194), tracking=0.26)

    big = serif(150, "Black")
    d.text((52, 122), "12", font=big, fill=BONE)
    d.text((52, 262), "MINUTES", font=serif(112, "Black"), fill=BONE)
    d.text((52, 372), "OF AIR LEFT", font=serif(86, "Black"), fill=AMBER)

    d.line([(56, 496), (300, 496)], fill=RUST, width=5)
    sub = sans(30, "SemiBold")
    letterspaced(d, (56, 520), "PISCES III  ·  1973", sub, (206, 194, 175), tracking=0.14)
    d.text((56, 566), "The deepest rescue ever completed.", font=serif(34, "Italic"), fill=(186, 176, 160))

    # depth stamp on the plate side
    stamp = sans(26, "SemiBold")
    st = "1,575 FT"
    sw = sum(d.textlength(c, font=stamp) + 26 * 0.14 for c in st) - 26 * 0.14
    x0, y0 = W - sw - 96, 54
    d.rectangle([x0 - 22, y0 - 14, x0 + sw + 22, y0 + 48], fill=INK + (185,))
    letterspaced(d, (x0, y0), st, stamp, AMBER, tracking=0.14)

    img = img.convert("RGB")
    img = frame_rules(img, inset=26, color=BONE, alpha=40, tick=18)
    out = os.path.join(ROOT, "episodes", slug, "seo", "thumbnail-1280.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)
    print("wrote", out)


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    slug = sys.argv[2] if len(sys.argv) > 2 else "ep01-pisces-iii"
    jobs = {
        "profile": build_profile,
        "banner": build_banner,
        "paper": build_paper_texture,
        "title": build_title_card,
        "end": build_end_card,
        "thumb": lambda: build_thumbnail(slug),
    }
    if what == "all":
        for fn in jobs.values():
            fn()
    else:
        jobs[what]()


if __name__ == "__main__":
    main()
