#!/usr/bin/env python3
"""Generate games/geometric-runes.polydicegame.

Draws six original geometric glyph PNGs (128x128, RGBA) with pure stdlib
and embeds them base64 in a game definition. Re-run to regenerate the
file deterministically.
"""

import base64
import json
import math
import struct
import zlib
from pathlib import Path

SIZE = 128
STROKE = 9
INK = (245, 242, 235, 255)  # warm ivory

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "games" / "geometric-runes.polydicegame"


# ---------------------------------------------------------------- PNG writer

def png(width: int, height: int, pixels: list[list[tuple[int, int, int, int]]]) -> bytes:
    raw = b"".join(
        b"\x00" + b"".join(bytes(px) for px in row) for row in pixels
    )

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


# ---------------------------------------------------------------- raster ops

def canvas() -> list[list[tuple[int, int, int, int]]]:
    return [[(0, 0, 0, 0)] * SIZE for _ in range(SIZE)]


def put(px: list[list[tuple[int, int, int, int]]], x: int, y: int) -> None:
    if 0 <= x < SIZE and 0 <= y < SIZE:
        px[y][x] = INK


def circle_outline(px, cx, cy, r):
    for a in range(0, 3600):
        t = math.radians(a / 10)
        for w in range(-(STROKE // 2), STROKE // 2 + 1):
            rr = r + w
            put(px, round(cx + rr * math.cos(t)), round(cy + rr * math.sin(t)))


def polygon_outline(px, points):
    def line(x0, y0, x1, y1):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            t = i / n
            for w in range(-(STROKE // 2), STROKE // 2 + 1):
                put(px, round(x0 + (x1 - x0) * t + w), round(y0 + (y1 - y0) * t))

    pts = points + [points[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        line(x0, y0, x1, y1)


def cross(px, cx, cy, r):
    for w in range(-(STROKE // 2), STROKE // 2 + 1):
        for d in range(-r, r + 1):
            put(px, cx + d, cy + d + w)
            put(px, cx + d, cy - d + w)


# ---------------------------------------------------------------- glyphs

C = SIZE // 2
GLYPHS = {
    "circle": lambda px: circle_outline(px, C, C, 40),
    "square": lambda px: polygon_outline(px, [(38, 38), (90, 38), (90, 90), (38, 90)]),
    "triangle": lambda px: polygon_outline(px, [(64, 30), (98, 92), (30, 92)]),
    "diamond": lambda px: polygon_outline(px, [(64, 26), (102, 64), (64, 102), (26, 64)]),
    "cross": lambda px: cross(px, C, C, 34),
    "rings": lambda px: (circle_outline(px, C, C, 40), circle_outline(px, C, C, 18)),
}

FACE_NAMES = {
    "circle": "Circle Rune",
    "square": "Square Rune",
    "triangle": "Triangle Rune",
    "diamond": "Diamond Rune",
    "cross": "Cross Rune",
    "rings": "Rings Rune",
}


def main() -> None:
    images = {}
    faces = []
    for name, draw in GLYPHS.items():
        px = canvas()
        draw(px)
        images[name] = base64.b64encode(png(SIZE, SIZE, px)).decode("ascii")
        faces.append({
            "id": name,
            "name": FACE_NAMES[name],
            "weight": 1,
            "symbol": {"type": "image", "name": name},
        })

    game = {
        "id": "geometric-runes",
        "name": "Geometric Runes",
        "shortName": "Runes",
        "author": "draugvar",
        "version": 1,
        "isGeneric": False,
        "diceType": "d6",
        "dieShape": {
            "type": "roundedPolygon",
            "sides": 6,
            "rotation": 0,
            "cornerRadius": 16,
        },
        "dieColor": {"r": 0.16, "g": 0.11, "b": 0.24},
        "accentColor": {"r": 0.96, "g": 0.80, "b": 0.36},
        "faces": faces,
        "images": images,
        "diceCount": 2,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(game, indent=2) + "\n")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()