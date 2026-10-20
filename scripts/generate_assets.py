#!/usr/bin/env python3
"""
Generates the animated SVG assets used by the profile README.

Run it from anywhere; it always writes into ../assets relative to this file.

    python scripts/generate_assets.py                   # rebuild everything
    python scripts/generate_assets.py --photo me.jpg    # put YOUR photo inside the animated avatar ring
    python scripts/generate_assets.py --logos           # try to embed real brand logos in the tech ticker
                                                        # (needs internet; any logo that fails falls back to a dot)

Why generate SVGs instead of using GIFs?
  * They stay razor sharp on every screen (retina, mobile, zoomed).
  * They are tiny (a few KB) compared with a GIF.
  * GitHub plays SMIL animations inside <img src="...svg"> tags, so nothing extra is needed.
"""
from __future__ import annotations

import argparse
import base64
import io
import math
import sys
import urllib.request
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
FONT = "'JetBrains Mono','SF Mono',Consolas,'Liberation Mono',monospace"


def write(name: str, svg: str) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    path = ASSETS / name
    path.write_text(svg.strip() + "\n", encoding="utf-8")
    print(f"  wrote assets/{name:<22} {path.stat().st_size / 1024:6.1f} KB")


# --------------------------------------------------------------------------- #
# 1. Divider: a thin gradient line with a glowing light that sweeps across it  #
# --------------------------------------------------------------------------- #
def divider() -> str:
    return """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 14" width="1000" height="14" role="img" aria-label="Section divider">
  <defs>
    <linearGradient id="line" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0"  stop-color="#06B6D4" stop-opacity="0"/>
      <stop offset=".2" stop-color="#06B6D4"/>
      <stop offset=".5" stop-color="#6D28D9"/>
      <stop offset=".8" stop-color="#06B6D4"/>
      <stop offset="1"  stop-color="#06B6D4" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="glow">
      <stop offset="0" stop-color="#67E8F9"/>
      <stop offset="1" stop-color="#67E8F9" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect x="0" y="6" width="1000" height="2" rx="1" fill="url(#line)"/>
  <circle cy="7" r="7" fill="url(#glow)">
    <animate attributeName="cx" values="0;1000;0" keyTimes="0;.5;1" dur="7s" repeatCount="indefinite"
             calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/>
  </circle>
</svg>
"""


# --------------------------------------------------------------------------- #
# 2. Avatar: spinning gradient ring + pulsing aura around your photo (or logo) #
# --------------------------------------------------------------------------- #
def _mime(data: bytes) -> str:
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def load_photo(path: Path) -> tuple[str, str]:
    """Return (mime, base64) of a square, web-sized version of the photo."""
    data = path.read_bytes()
    try:
        from PIL import Image, ImageOps  # type: ignore

        img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        side = min(img.size)
        left = (img.width - side) // 2
        top = int((img.height - side) * 0.2)  # bias upward so faces are not cropped
        img = img.crop((left, top, left + side, top + side)).resize((360, 360), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=84, optimize=True)
        data = buf.getvalue()
    except ImportError:
        print("  ! Pillow not installed, embedding the photo as-is (pip install pillow to auto-crop/resize)")
    if len(data) > 250_000:
        print(f"  ! photo is {len(data) // 1024} KB, consider a smaller one so the README loads fast")
    return _mime(data), base64.b64encode(data).decode()


def avatar(photo: tuple[str, str] | None) -> str:
    if photo:
        mime, b64 = photo
        center = f'<image href="data:{mime};base64,{b64}" x="28" y="28" width="184" height="184" preserveAspectRatio="xMidYMid slice" clip-path="url(#face)"/>'
    else:
        # Placeholder: an "M" monogram that draws itself, pauses, then redraws.
        center = """
  <path d="M80 162 V82 L120 130 L160 82 V162" fill="none" stroke="url(#ink)" stroke-width="12"
        stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="300" stroke-dashoffset="300">
    <animate attributeName="stroke-dashoffset" values="300;0;0;300" keyTimes="0;.35;.85;1" dur="7s" repeatCount="indefinite"/>
  </path>"""
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="240" height="240" role="img" aria-label="Mahesh profile avatar">
  <defs>
    <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0"   stop-color="#06B6D4"/>
      <stop offset=".55" stop-color="#6D28D9"/>
      <stop offset="1"   stop-color="#DB2777"/>
    </linearGradient>
    <linearGradient id="ink" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#67E8F9"/>
      <stop offset="1" stop-color="#A78BFA"/>
    </linearGradient>
    <radialGradient id="aura">
      <stop offset=".6" stop-color="#6D28D9" stop-opacity=".35"/>
      <stop offset="1"  stop-color="#6D28D9" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="face"><circle cx="120" cy="120" r="92"/></clipPath>
  </defs>

  <!-- breathing aura -->
  <circle cx="120" cy="120" r="118" fill="url(#aura)">
    <animate attributeName="r" values="108;118;108" dur="4s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values=".6;1;.6" dur="4s" repeatCount="indefinite"/>
  </circle>

  <!-- fast gradient ring (circumference of r=106 is about 666) -->
  <g>
    <animateTransform attributeName="transform" type="rotate" from="0 120 120" to="360 120 120" dur="7s" repeatCount="indefinite"/>
    <circle cx="120" cy="120" r="106" fill="none" stroke="url(#ring)" stroke-width="5" stroke-linecap="round" stroke-dasharray="470 196"/>
  </g>

  <!-- slow dotted ring spinning the other way -->
  <g>
    <animateTransform attributeName="transform" type="rotate" from="360 120 120" to="0 120 120" dur="22s" repeatCount="indefinite"/>
    <circle cx="120" cy="120" r="98" fill="none" stroke="#67E8F9" stroke-opacity=".55" stroke-width="1.5" stroke-linecap="round" stroke-dasharray="2 9"/>
  </g>

  <circle cx="120" cy="120" r="92" fill="#0D1117"/>
  {center}
</svg>
"""


# --------------------------------------------------------------------------- #
# 3. Tech ticker: two rows of pills scrolling in opposite directions           #
# --------------------------------------------------------------------------- #
# (label, brand colour, simple-icons slug used only with --logos)
ROW_1 = [
    ("TypeScript", "3178C6", "typescript"), ("JavaScript", "F7DF1E", "javascript"),
    ("Python", "4B8BBE", "python"), ("Java", "ED8B00", "openjdk"),
    ("HTML5", "E34F26", "html5"), ("CSS3", "1572B6", "css3"),
    ("React", "61DAFB", "react"), ("Next.js", "FFFFFF", "nextdotjs"),
    ("Tailwind CSS", "06B6D4", "tailwindcss"), ("Vite", "646CFF", "vite"),
    ("Node.js", "339933", "nodedotjs"), ("NestJS", "E0234E", "nestjs"),
    ("Express", "9CA3AF", "express"), ("FastAPI", "009688", "fastapi"),
]
ROW_2 = [
    ("PostgreSQL", "4169E1", "postgresql"), ("MongoDB", "47A248", "mongodb"),
    ("MySQL", "4479A1", "mysql"), ("Redis", "DC382D", "redis"),
    ("Supabase", "3ECF8E", "supabase"), ("AWS", "FF9900", "amazonaws"),
    ("Docker", "2496ED", "docker"), ("Git", "F05032", "git"),
    ("GitHub", "C9D1D9", "github"), ("VS Code", "007ACC", "visualstudiocode"),
    ("Linux", "FCC624", "linux"), ("LLMs", "A78BFA", None),
    ("RAG", "14B8A6", None), ("Embeddings", "60A5FA", None),
    ("Agentic AI", "C084FC", None), ("Vector Search", "22D3EE", None),
    ("Tool Calling", "94A3B8", None),
]

CHAR_W = 7.9      # width of one character at 13px monospace
PILL_H = 34
GAP = 14


def fetch_logo(slug: str, color: str) -> str | None:
    url = f"https://cdn.simpleicons.org/{slug}/{color}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "profile-assets/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            svg = r.read()
        if b"<svg" not in svg:
            return None
        return base64.b64encode(svg).decode()
    except Exception as exc:  # noqa: BLE001 - any failure just means "use the dot"
        print(f"    logo for {slug} unavailable ({type(exc).__name__}); using a dot")
        return None


def _pill(x: float, label: str, color: str, logo_b64: str | None) -> tuple[str, float]:
    w = 40 + len(label) * CHAR_W + 16
    if logo_b64:
        icon = f'<image href="data:image/svg+xml;base64,{logo_b64}" x="14" y="8" width="18" height="18"/>'
    else:
        icon = f'<circle cx="23" cy="{PILL_H / 2}" r="5" fill="#{color}"/>'
    svg = (
        f'<g transform="translate({x:.1f} 0)">'
        f'<rect width="{w:.1f}" height="{PILL_H}" rx="{PILL_H / 2}" fill="#0D1117" stroke="#{color}" stroke-opacity=".55" stroke-width="1.2"/>'
        f"{icon}"
        f'<text x="40" y="{PILL_H / 2 + 4.5}" font-family="{FONT}" font-size="13" font-weight="600" fill="#E5E7EB">{label}</text>'
        f"</g>"
    )
    return svg, w


def _row(items, y: float, reverse: bool, logos: bool, speed: float = 38) -> str:
    x, parts = 0.0, []
    for label, color, slug in items:
        b64 = fetch_logo(slug, color) if (logos and slug) else None
        svg, w = _pill(x, label, color, b64)
        parts.append(svg)
        x += w + GAP
    total = x
    assert total >= 1000, "row too short for a seamless loop; add more items"
    one = "".join(parts)
    start, end = ("0 0", f"-{total:.1f} 0") if not reverse else (f"-{total:.1f} 0", "0 0")
    dur = total / speed
    return (
        f'<g transform="translate(0 {y})"><g>'
        f'<animateTransform attributeName="transform" type="translate" from="{start}" to="{end}" dur="{dur:.1f}s" repeatCount="indefinite"/>'
        f'{one}<g transform="translate({total:.1f} 0)">{one}</g>'
        f"</g></g>"
    )


def tech_marquee(logos: bool) -> str:
    row1 = _row(ROW_1, 4, reverse=False, logos=logos)
    row2 = _row(ROW_2, 54, reverse=True, logos=logos, speed=34)
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 92" width="1000" height="92" role="img"
     aria-label="Scrolling ticker of technologies: TypeScript, React, Next.js, Node.js, NestJS, PostgreSQL, MongoDB, Docker, LLMs, RAG and more">
  <defs>
    <linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0"   stop-color="#fff" stop-opacity="0"/>
      <stop offset=".08" stop-color="#fff"/>
      <stop offset=".92" stop-color="#fff"/>
      <stop offset="1"   stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <mask id="edges"><rect width="1000" height="92" fill="url(#fade)"/></mask>
  </defs>
  <g mask="url(#edges)">
    {row1}
    {row2}
  </g>
</svg>
"""


# --------------------------------------------------------------------------- #
# 4. Project thumbnails: animated icon + chasing-light border + drifting glow  #
# --------------------------------------------------------------------------- #
def _tag(cx: float, cy: float, text: str, color: str, delay: float) -> str:
    w = len(text) * 7.2 + 24
    return (
        f"<g transform=\"translate({cx} {cy})\"><g>"
        f'<animateTransform attributeName="transform" type="translate" values="0 0;0 -5;0 0" dur="4s" begin="{delay}s" repeatCount="indefinite"/>'
        f'<rect x="{-w / 2:.1f}" y="-12" width="{w:.1f}" height="24" rx="12" fill="#0B1020" fill-opacity=".7" stroke="#{color}" stroke-opacity=".6"/>'
        f'<text y="4" text-anchor="middle" font-family="{FONT}" font-size="10.5" letter-spacing="1.5" fill="#E5E7EB" fill-opacity=".9">{text}</text>'
        f"</g></g>"
    )


def icon_spark(c1: str, c2: str) -> str:
    ring = lambda color, begin: (  # noqa: E731
        f'<circle r="28" fill="none" stroke="#{color}" stroke-width="1.5">'
        f'<animate attributeName="r" values="28;54" dur="3s" begin="{begin}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values=".7;0" dur="3s" begin="{begin}s" repeatCount="indefinite"/></circle>'
    )
    return (
        ring(c1, 0) + ring(c2, 1.5)
        + f'<g><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="10s" repeatCount="indefinite"/>'
          f'<circle cx="46" r="3.2" fill="#{c2}"/><circle cx="-46" r="2.2" fill="#{c1}"/></g>'
        + '<g><animateTransform attributeName="transform" type="scale" values="1;1.14;1" dur="2.6s" repeatCount="indefinite"/>'
          '<path d="M0 -26 C3 -9 9 -3 26 0 C9 3 3 9 0 26 C-3 9 -9 3 -26 0 C-9 -3 -3 -9 0 -26Z" fill="url(#ico)"/></g>'
    )


def icon_play(c1: str, c2: str) -> str:
    strip = lambda y: (  # noqa: E731
        f'<line x1="-40" x2="40" y1="{y}" y2="{y}" stroke="#{c2}" stroke-opacity=".7" stroke-width="4" stroke-dasharray="7 7">'
        f'<animate attributeName="stroke-dashoffset" from="0" to="-14" dur="1s" repeatCount="indefinite"/></line>'
    )
    return (
        strip(-38) + strip(38)
        + '<rect x="-46" y="-30" width="92" height="60" rx="10" fill="#0B1020" fill-opacity=".6" stroke="url(#ico)" stroke-width="2.5"/>'
        + f'<circle r="16" fill="none" stroke="#{c1}" stroke-width="1.5">'
          '<animate attributeName="r" values="16;36" dur="2.2s" repeatCount="indefinite"/>'
          '<animate attributeName="opacity" values=".8;0" dur="2.2s" repeatCount="indefinite"/></circle>'
        + '<path d="M-7 -13 L16 0 L-7 13Z" fill="#fff"/>'
    )


def icon_pin(c1: str, c2: str) -> str:
    bits = "".join(
        f'<circle cx="{x}" cy="10" r="2.4" fill="#{c}">'
        f'<animate attributeName="cy" values="22;-34" dur="{d}s" begin="{b}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="0;.9;0" dur="{d}s" begin="{b}s" repeatCount="indefinite"/></circle>'
        for x, c, d, b in ((-44, c1, 3.2, 0), (46, c2, 2.8, .8), (58, c1, 3.6, 1.6))
    )
    return (
        f'<ellipse cy="44" rx="10" ry="3.5" fill="none" stroke="#{c2}" stroke-width="1.5">'
        '<animate attributeName="rx" values="10;42" dur="1.8s" repeatCount="indefinite"/>'
        '<animate attributeName="opacity" values=".8;0" dur="1.8s" repeatCount="indefinite"/></ellipse>'
        + bits
        + '<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -8;0 0" keyTimes="0;.5;1" dur="1.8s" '
          'calcMode="spline" keySplines=".4 0 .6 1;.4 0 .6 1" repeatCount="indefinite"/>'
          '<path d="M0 -32 C-18 -32 -27 -18 -27 -6 C-27 11 -8 25 0 36 C8 25 27 11 27 -6 C27 -18 18 -32 0 -32Z" fill="url(#ico)"/>'
          '<circle cy="-8" r="10" fill="#0B1020"/></g>'
    )


def project_card(label: str, c1: str, c2: str, icon: str, w: int, tags: str = "", h: int = 150) -> str:
    r = 16
    iw, ih = w - 2, h - 2
    perim = 2 * (iw + ih) - 8 * r + 2 * math.pi * r
    dash = perim * 0.16
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{label.title()} project thumbnail">
  <defs>
    <linearGradient id="ico" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#{c1}"/><stop offset="1" stop-color="#{c2}"/></linearGradient>
    <linearGradient id="tint" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#{c1}" stop-opacity=".28"/><stop offset="1" stop-color="#{c2}" stop-opacity=".10"/>
    </linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#{c1}"/><stop offset="1" stop-color="#{c2}"/></linearGradient>
    <pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1" fill="#fff" fill-opacity=".14"/></pattern>
    <filter id="blur" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="26"/></filter>
    <clipPath id="card"><rect x="1" y="1" width="{iw}" height="{ih}" rx="{r}"/></clipPath>
  </defs>

  <g clip-path="url(#card)">
    <rect width="{w}" height="{h}" fill="#0B1020"/>
    <rect width="{w}" height="{h}" fill="url(#tint)"/>
    <circle cx="{w * 0.2:.0f}" cy="30" r="52" fill="#{c1}" opacity=".5" filter="url(#blur)">
      <animate attributeName="cx" values="{w * 0.2:.0f};{w * 0.42:.0f};{w * 0.2:.0f}" dur="9s" repeatCount="indefinite"/>
    </circle>
    <circle cx="{w * 0.82:.0f}" cy="{h - 20}" r="56" fill="#{c2}" opacity=".45" filter="url(#blur)">
      <animate attributeName="cx" values="{w * 0.82:.0f};{w * 0.6:.0f};{w * 0.82:.0f}" dur="11s" repeatCount="indefinite"/>
    </circle>
    <rect width="{w}" height="{h}" fill="url(#dots)"/>
    {tags}
    <g transform="translate({w / 2:.0f} {h / 2 - 12:.0f})">{icon}</g>
    <text x="{w / 2:.0f}" y="{h - 16}" text-anchor="middle" font-family="{FONT}" font-size="12" font-weight="600" letter-spacing="3" fill="#E5E7EB" fill-opacity=".85">{label}</text>
  </g>

  <rect x="1" y="1" width="{iw}" height="{ih}" rx="{r}" fill="none" stroke="#fff" stroke-opacity=".10"/>
  <rect x="1" y="1" width="{iw}" height="{ih}" rx="{r}" fill="none" stroke="url(#edge)" stroke-width="2.5" stroke-linecap="round"
        stroke-dasharray="{dash:.1f} {perim - dash:.1f}">
    <animate attributeName="stroke-dashoffset" from="0" to="-{perim:.1f}" dur="5s" repeatCount="indefinite"/>
  </rect>
</svg>
"""


def project_cards() -> dict[str, str]:
    wide_tags = "".join(
        _tag(x, y, t, col, d)
        for x, y, t, col, d in (
            (150, 48, "LOCATION-AWARE", "F59E0B", 0),
            (810, 48, "BUDGET-BASED", "DB2777", 1),
            (190, 100, "WEBSOCKETS", "DB2777", 2),
            (770, 100, "RAG ASSISTANT", "F59E0B", 3),
        )
    )
    return {
        "project-vizuna.svg": project_card("AI  ·  SELF-IMPROVEMENT", "7C3AED", "06B6D4", icon_spark("7C3AED", "06B6D4"), 480),
        "project-thirai.svg": project_card("OTT  ·  MULTILINGUAL STREAMING", "0891B2", "6366F1", icon_play("0891B2", "6366F1"), 480),
        "project-food.svg": project_card("FOOD  ·  CONVERSATIONAL AI", "DB2777", "F59E0B", icon_pin("DB2777", "F59E0B"), 960, tags=wide_tags),
    }


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--photo", type=Path, help="path to your photo (jpg/png/webp) for the avatar ring")
    ap.add_argument("--logos", action="store_true", help="embed real brand logos in the tech ticker (needs internet)")
    args = ap.parse_args()

    print("Generating assets...")
    photo = load_photo(args.photo) if args.photo else None
    write("divider.svg", divider())
    write("avatar.svg", avatar(photo))
    write("tech-marquee.svg", tech_marquee(args.logos))
    for name, svg in project_cards().items():
        write(name, svg)
    print("Done. Commit the assets/ folder together with README.md.")


if __name__ == "__main__":
    sys.exit(main())
