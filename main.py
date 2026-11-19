#!/usr/bin/env python3
"""
make.fun bounty: news-image-20261118
Renders a 1024x1024 PNG summarizing world news of 18 November 2026.

Standard library only (zlib + struct for a hand-rolled PNG encoder,
plus a hand-rolled 5x7 bitmap font). No network access at runtime —
all captions below were researched ahead of time and are hardcoded.

Deterministic: given the same inputs, byte-identical output every run.
"""

import os
import struct
import zlib

# Note: PNG bytes are built manually via zlib/struct and glyphs come from a
# hand-rolled 5x7 bitmap font, avoiding any third-party imaging dependency.

WIDTH = 1024
HEIGHT = 1024

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
BG = (8, 12, 30)            # page background, dark navy
TITLE_BG = (14, 19, 46)     # title bar background
CARD_BG = (19, 25, 54)      # card background, slightly lighter navy
CARD_BORDER = (40, 50, 86)  # subtle card border
WHITE = (240, 243, 250)
SUBTLE = (158, 173, 206)    # caption text color
GOLD = (245, 197, 66)       # title bar rule / date text

ACCENT_RED = (231, 76, 60)
ACCENT_GOLD = (241, 196, 15)
ACCENT_ORANGE = (230, 126, 34)
ACCENT_TEAL = (26, 188, 156)
ACCENT_PURPLE = (155, 89, 182)
ACCENT_BLUE = (52, 152, 219)

# ---------------------------------------------------------------------------
# 5-wide x 7-tall bitmap font. Each glyph is 7 rows of a 5-char '0'/'1' string.
# Covers A-Z, 0-9, space, and punctuation: . , ' - : $ % /
# ---------------------------------------------------------------------------
FONT = {
    'A': ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    'B': ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    'C': ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    'D': ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    'E': ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    'F': ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    'G': ["01111", "10000", "10000", "10011", "10001", "10001", "01111"],
    'H': ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    'I': ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    'J': ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    'K': ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    'L': ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    'M': ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    'N': ["10001", "11001", "10101", "10101", "10011", "10001", "10001"],
    'O': ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    'P': ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    'Q': ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    'R': ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    'S': ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    'T': ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    'U': ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    'V': ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    'W': ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    'X': ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    'Y': ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    'Z': ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    '0': ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    '1': ["00100", "01100", "10100", "00100", "00100", "00100", "01110"],
    '2': ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    '3': ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    '4': ["10001", "10001", "10001", "11111", "00001", "00001", "00001"],
    '5': ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    '6': ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    '7': ["11111", "00001", "00010", "00100", "01000", "10000", "10000"],
    '8': ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    '9': ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    ' ': ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    '.': ["00000", "00000", "00000", "00000", "00000", "00110", "00110"],
    ',': ["00000", "00000", "00000", "00000", "00000", "00100", "01000"],
    "'": ["01000", "01000", "00000", "00000", "00000", "00000", "00000"],
    '-': ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    ':': ["00000", "00110", "00110", "00000", "00110", "00110", "00000"],
    '$': ["00100", "01111", "10100", "01110", "00101", "11110", "00100"],
    '%': ["11001", "11010", "00100", "00100", "00100", "01011", "10011"],
    '/': ["00001", "00001", "00010", "00100", "01000", "10000", "10000"],
}
GLYPH_W = 5
GLYPH_H = 7


# ---------------------------------------------------------------------------
# Pixel buffer helpers (flat bytearray, row-major RGB)
# ---------------------------------------------------------------------------
def new_canvas(w, h, bg):
    buf = bytearray(w * h * 3)
    r, g, b = bg
    row = bytes((r, g, b)) * w
    for y in range(h):
        buf[y * w * 3:(y + 1) * w * 3] = row
    return buf


def set_px(buf, x, y, color):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        i = (y * WIDTH + x) * 3
        buf[i] = color[0]
        buf[i + 1] = color[1]
        buf[i + 2] = color[2]


def fill_rect(buf, x, y, w, h, color):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(WIDTH, x + w)
    y1 = min(HEIGHT, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    r, g, b = color
    row = bytes((r, g, b)) * (x1 - x0)
    for yy in range(y0, y1):
        i = (yy * WIDTH + x0) * 3
        buf[i:i + len(row)] = row


def draw_rect_outline(buf, x, y, w, h, color, thickness=2):
    fill_rect(buf, x, y, w, thickness, color)
    fill_rect(buf, x, y + h - thickness, w, thickness, color)
    fill_rect(buf, x, y, thickness, h, color)
    fill_rect(buf, x + w - thickness, y, thickness, h, color)


def draw_circle(buf, cx, cy, r, color, filled=True, thickness=2):
    r2 = r * r
    ir2 = (r - thickness) * (r - thickness) if not filled else -1
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            dx = xx - cx
            dy = yy - cy
            d2 = dx * dx + dy * dy
            if d2 <= r2 and (filled or d2 >= ir2):
                set_px(buf, xx, yy, color)


def draw_triangle(buf, p1, p2, p3, color):
    xs = [p1[0], p2[0], p3[0]]
    ys = [p1[1], p2[1], p3[1]]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)

    def sign(ax, ay, bx, by, cx, cy):
        return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)

    for yy in range(y0, y1 + 1):
        for xx in range(x0, x1 + 1):
            d1 = sign(p1[0], p1[1], p2[0], p2[1], xx, yy)
            d2 = sign(p2[0], p2[1], p3[0], p3[1], xx, yy)
            d3 = sign(p3[0], p3[1], p1[0], p1[1], xx, yy)
            has_neg = d1 < 0 or d2 < 0 or d3 < 0
            has_pos = d1 > 0 or d2 > 0 or d3 > 0
            if not (has_neg and has_pos):
                set_px(buf, xx, yy, color)


def draw_line(buf, x0, y0, x1, y1, color, thickness=2):
    dx = x1 - x0
    dy = y1 - y0
    steps = max(abs(dx), abs(dy), 1)
    for i in range(steps + 1):
        x = round(x0 + dx * i / steps)
        y = round(y0 + dy * i / steps)
        half = thickness // 2
        for ox in range(-half, thickness - half):
            for oy in range(-half, thickness - half):
                set_px(buf, x + ox, y + oy, color)


def text_width(s, scale):
    return len(s) * 6 * scale


def draw_text(buf, x, y, s, scale, color):
    cx = x
    for ch in s:
        glyph = FONT.get(ch.upper())
        if glyph is None:
            cx += 6 * scale
            continue
        for row in range(GLYPH_H):
            bits = glyph[row]
            for col in range(GLYPH_W):
                if bits[col] == '1':
                    fill_rect(buf, cx + col * scale, y + row * scale, scale, scale, color)
        cx += 6 * scale


# ---------------------------------------------------------------------------
# Story content (researched ahead of time; no runtime network access)
# ---------------------------------------------------------------------------
STORIES = [
    {
        "accent": ACCENT_RED,
        "title": "UKRAINE: ODESA HIT",
        "lines": [
            "RUSSIAN STRIKES KILL 4 IN",
            "ODESA'S UNESCO OLD TOWN",
            "DOUBLE-TAP HIT RESPONDERS",
        ],
        "icon": "triangle",
    },
    {
        "accent": ACCENT_GOLD,
        "title": "EU: UKRAINE LOAN",
        "lines": [
            "VON DER LEYEN BACKS",
            "EUR 45 BILLION LOAN",
            "FOR UKRAINE REBUILD",
        ],
        "icon": "coin",
    },
    {
        "accent": ACCENT_ORANGE,
        "title": "YEMEN CRISIS",
        "lines": [
            "UNICEF: DOZENS OF KIDS",
            "KILLED IN HOUTHI CLASHES",
            "HUNDREDS OF THOUSANDS FLEE",
        ],
        "icon": "tent",
    },
    {
        "accent": ACCENT_TEAL,
        "title": "WHO HEALTH ALERT",
        "lines": [
            "DRUG RESISTANCE WORSE",
            "THAN 2019, WHO WARNS",
            "INFECTIONS RISING FAST",
        ],
        "icon": "cross",
    },
    {
        "accent": ACCENT_PURPLE,
        "title": "US TECH OUTAGES",
        "lines": [
            "AIR TRAVEL, MS EMAIL HIT",
            "NSA NETWORK DISRUPTED",
            "NOT A COORDINATED ATTACK",
        ],
        "icon": "glitch",
    },
    {
        "accent": ACCENT_BLUE,
        "title": "DC SECURITY ALERT",
        "lines": [
            "ALLEGED IRAN PLOT TIED",
            "TO WASHINGTON TARGETS",
            "RUBIO: NO IMMINENT THREAT",
        ],
        "icon": "shield",
    },
]

assert len(STORIES) == 6


# ---------------------------------------------------------------------------
# Icon drawing (built only from circles, rects and triangles)
# ---------------------------------------------------------------------------
def draw_icon(buf, kind, x, y, size, color):
    cx = x + size // 2
    cy = y + size // 2

    if kind == "triangle":
        draw_triangle(buf, (cx, y), (x, y + size), (x + size, y + size), color)
        fill_rect(buf, cx - 2, y + size // 3, 4, size // 3, BG)
        fill_rect(buf, cx - 2, y + size - size // 6, 4, 4, BG)

    elif kind == "coin":
        draw_circle(buf, cx, cy, size // 2, color, filled=True)
        draw_circle(buf, cx, cy, size // 2 - 6, BG, filled=True)
        draw_circle(buf, cx, cy, size // 2 - 10, color, filled=True)

    elif kind == "tent":
        draw_triangle(buf, (cx, y), (x, y + size), (x + size, y + size), color)
        draw_triangle(buf, (cx, y + size // 2), (x + size * 2 // 5, y + size),
                      (x + size * 3 // 5, y + size), BG)
        fill_rect(buf, x, y + size - 4, size, 4, color)

    elif kind == "cross":
        bar = size // 3
        fill_rect(buf, cx - bar // 2, y, bar, size, color)
        fill_rect(buf, x, cy - bar // 2, size, bar, color)

    elif kind == "glitch":
        draw_rect_outline(buf, x, y, size, size, color, thickness=3)
        draw_line(buf, x + 4, y + 6, x + size - 10, y + size // 2, color, thickness=3)
        draw_line(buf, x + size - 10, y + size // 2, x + 10, y + size - 6, color, thickness=3)
        draw_line(buf, x + 10, y + size - 6, x + size - 4, y + size - 4, color, thickness=3)

    elif kind == "shield":
        fill_rect(buf, x, cy - 2, size, size // 2, color)
        draw_circle(buf, cx, y + size // 4, size // 4, color, filled=True)
        draw_triangle(buf, (x, cy + size // 4), (x + size, cy + size // 4),
                      (cx, y + size), color)


# ---------------------------------------------------------------------------
# Layout + composition
# ---------------------------------------------------------------------------
def compose():
    buf = new_canvas(WIDTH, HEIGHT, BG)

    # --- Title bar -----------------------------------------------------
    TITLE_H = 118
    fill_rect(buf, 0, 0, WIDTH, TITLE_H, TITLE_BG)
    fill_rect(buf, 0, TITLE_H - 4, WIDTH, 4, GOLD)

    title_text = "WORLD NEWS"
    title_scale = 6
    tw = text_width(title_text, title_scale)
    draw_text(buf, (WIDTH - tw) // 2, 22, title_text, title_scale, WHITE)

    date_text = "NOVEMBER 18, 2026"
    date_scale = 3
    dw = text_width(date_text, date_scale)
    draw_text(buf, (WIDTH - dw) // 2, 80, date_text, date_scale, GOLD)

    # --- Story grid: 3 rows x 2 cols of cards --------------------------
    OUTER_MARGIN = 30
    GRID_TOP = TITLE_H + 26
    GRID_BOTTOM = HEIGHT - OUTER_MARGIN
    COLS, ROWS = 2, 3
    COL_GAP = 24
    ROW_GAP = 24

    grid_w = WIDTH - 2 * OUTER_MARGIN
    grid_h = GRID_BOTTOM - GRID_TOP
    card_w = (grid_w - (COLS - 1) * COL_GAP) // COLS
    card_h = (grid_h - (ROWS - 1) * ROW_GAP) // ROWS

    PAD = 18
    ICON_SIZE = 52
    title_scale_card = 3
    cap_scale = 2

    # Pre-flight text-width check, computed from the real layout numbers
    # (not assumed): every caption/title line must fit inside the card's
    # inner text column.
    inner_w = card_w - 2 * PAD
    max_cap_chars = inner_w // (6 * cap_scale)
    max_title_chars = inner_w // (6 * title_scale_card)

    for story in STORIES:
        assert len(story["title"]) <= max_title_chars, (
            f"title too long: {story['title']!r} "
            f"({len(story['title'])} > {max_title_chars})"
        )
        for line in story["lines"]:
            assert len(line) <= max_cap_chars, (
                f"caption too long: {line!r} ({len(line)} > {max_cap_chars})"
            )

    for idx, story in enumerate(STORIES):
        row = idx // COLS
        col = idx % COLS
        x = OUTER_MARGIN + col * (card_w + COL_GAP)
        y = GRID_TOP + row * (card_h + ROW_GAP)

        fill_rect(buf, x, y, card_w, card_h, CARD_BG)
        draw_rect_outline(buf, x, y, card_w, card_h, CARD_BORDER, thickness=2)

        accent = story["accent"]
        fill_rect(buf, x, y, card_w, 8, accent)

        content_x = x + PAD
        content_y = y + 8 + PAD

        draw_icon(buf, story["icon"], content_x, content_y, ICON_SIZE, accent)

        title_y = content_y + ICON_SIZE + 12
        draw_text(buf, content_x, title_y, story["title"], title_scale_card, WHITE)

        cap_y = title_y + GLYPH_H * title_scale_card + 16
        line_pitch = GLYPH_H * cap_scale + 10
        for i, line in enumerate(story["lines"]):
            draw_text(buf, content_x, cap_y + i * line_pitch, line, cap_scale, SUBTLE)

    return buf


# ---------------------------------------------------------------------------
# Minimal PNG encoder (zlib + struct only)
# ---------------------------------------------------------------------------
def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def encode_png(pixels: bytearray, width: int, height: int) -> bytes:
    sig = b"\x89PNG\r\n\x1a\n"

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_chunk = png_chunk(b"IHDR", ihdr)

    stride = width * 3
    raw = bytearray()
    for row in range(height):
        raw.append(0)  # filter type 0: None
        start = row * stride
        raw.extend(pixels[start:start + stride])

    compressed = zlib.compress(bytes(raw), 9)
    idat_chunk = png_chunk(b"IDAT", compressed)

    iend_chunk = png_chunk(b"IEND", b"")

    return sig + ihdr_chunk + idat_chunk + iend_chunk


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")

    pixels = compose()
    png_bytes = encode_png(pixels, WIDTH, HEIGHT)

    with open(out_path, "wb") as f:
        f.write(png_bytes)


if __name__ == "__main__":
    main()
