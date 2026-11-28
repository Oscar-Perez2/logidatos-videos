#!/usr/bin/env python3
"""LogiDatos Short #9 – Cleopatra vivió más cerca de ti que de las pirámides (mamuts, Oxford vs. aztecas, T. rex vs. estegosaurio). Motion graphics drawn in code (cairo).
python3 video_09_cleopatra_piramides.py [preview t1 t2 ...]
Render -> build/silent.mp4; luego: musica.py mix build/silent.mp4 dl/voz.mp3 build/musica.wav <FINAL> --total TOTAL"""
import json, math, os, random, subprocess, sys
import cairo

W, H, FPS = 1080, 1920, 30
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "build"); os.makedirs(OUT, exist_ok=True)
WORDS = [w for w in json.load(open(os.path.join(BASE, "dl/words.json")))["words"] if w.get("type", "word") == "word"]
TOTAL = 54.0

def hexc(h, a=1.0):
    h = h.lstrip("#"); return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)
ACCENT = hexc("FFD23F"); NAVY = hexc("0B1020"); WHITE = hexc("F5F3EA")
ORANGE = hexc("FF6A13"); ORANGE_L = hexc("FF9A4D"); ORANGE_D = hexc("B8420A")
BLUE = hexc("3DA9FC"); RED = hexc("E0393E"); GREEN = hexc("37E08F"); GREY = hexc("8A93A6"); SEA = hexc("0B4F7A")
FONT = "Montserrat"

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def back(x):
    x = clamp(x); c = 1.70158; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, u): return a + (b - a) * u
def mixc(c1, c2, u): return tuple(lerp(c1[i], c2[i], u) for i in range(4))

# ---------------- primitives ----------------
def rgba(ctx, c, a=None): ctx.set_source_rgba(c[0], c[1], c[2], c[3] if a is None else a)

def text(ctx, s, x, y, size, color=WHITE, stroke=0, align="center", bold=True, alpha=1.0):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    w = ctx.text_extents(s).x_advance
    x0 = x - w / 2 if align == "center" else (x - w if align == "right" else x)
    y0 = y + size * 0.36
    ctx.new_path(); ctx.move_to(x0, y0); ctx.text_path(s)
    if stroke:
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_width(stroke)
        ctx.set_source_rgba(0, 0, 0, alpha); ctx.stroke_preserve()
    rgba(ctx, color, color[3] * alpha); ctx.fill()
    return w

def text_w(ctx, s, size):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(size)
    return ctx.text_extents(s).x_advance

def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path(); ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi); ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); ctx.close_path()

def glow(ctx, x, y, r, color, a):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, color[0], color[1], color[2], a); g.add_color_stop_rgba(1, color[0], color[1], color[2], 0)
    ctx.set_source(g); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.fill()

def logo_mark(ctx, x, y, s, alpha=1.0):
    rrect(ctx, x, y, s, s, s * 0.21); rgba(ctx, ACCENT, alpha); ctx.fill()
    k = s / 200 * 0.70; ox = x + s * 0.15 - 5 * k; oy = y + s * 0.15 + 3 * k
    rgba(ctx, NAVY, alpha)
    for (a, b, c, d) in [(38, 28, 34, 144), (38, 138, 134, 34), (88, 98, 34, 56), (138, 66, 34, 88)]:
        rrect(ctx, ox + a * k, oy + b * k, c * k, d * k, 8 * k); ctx.fill()
    ctx.arc(ox + 155 * k, oy + 38 * k, 15 * k, 0, 2 * math.pi); ctx.fill()

def label(ctx, s, x, y, size=44, color=WHITE, alpha=1.0, bg=True):
    if alpha <= 0: return
    w = text_w(ctx, s, size)
    if bg:
        rrect(ctx, x - w / 2 - 26, y - size * 0.75, w + 52, size * 1.5, size * 0.5); ctx.set_source_rgba(0.03, 0.03, 0.09, 0.78 * alpha); ctx.fill()
    text(ctx, s, x, y, size, color, alpha=alpha)

def header(ctx, s1, s2, t, t0, y=300, size=66, alpha=1.0, c2=ACCENT):
    a = (ease((t - t0) / 0.35) if t0 is not None else 1.0) * alpha
    if a <= 0: return
    dy = (1 - ease((t - t0) / 0.35)) * 30 if t0 is not None else 0
    ctx.save(); ctx.translate(0, dy)
    w1 = text_w(ctx, s1 + " ", size) if s1 else 0; w2 = text_w(ctx, s2, size)
    if w1 + w2 > 960:
        size *= 960 / (w1 + w2); w1 = text_w(ctx, s1 + " ", size) if s1 else 0; w2 = text_w(ctx, s2, size)
    x0 = (W - w1 - w2) / 2
    if s1: text(ctx, s1, x0, y, size, WHITE, stroke=10, align="left", alpha=a)
    text(ctx, s2, x0 + w1, y, size, c2, stroke=10, align="left", alpha=a)
    ctx.restore()

def pop_text(ctx, s, x, y, size, color, t, t0, stroke=14):
    k = back((t - t0) / 0.35)
    if k <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(k, k); text(ctx, s, 0, 0, size, color, stroke=stroke); ctx.restore()

def check(ctx, x, y, s, alpha=1.0, color=GREEN):
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.arc(0, 0, 1, 0, 2 * math.pi); rgba(ctx, color, alpha); ctx.fill()
    ctx.set_line_width(0.22); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(-0.45, 0.02); ctx.line_to(-0.12, 0.36); ctx.line_to(0.5, -0.32); ctx.set_source_rgba(1, 1, 1, alpha); ctx.stroke()
    ctx.restore()

def cross(ctx, x, y, s, alpha=1.0, color=RED):
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.arc(0, 0, 1, 0, 2 * math.pi); rgba(ctx, color, alpha); ctx.fill()
    ctx.set_line_width(0.24); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(-0.42, -0.42); ctx.line_to(0.42, 0.42); ctx.move_to(0.42, -0.42); ctx.line_to(-0.42, 0.42)
    ctx.set_source_rgba(1, 1, 1, alpha); ctx.stroke(); ctx.restore()

def counter_box(ctx, x, y, n, unit, alpha=1.0, color=ACCENT, size=140, sub=46):
    if alpha <= 0: return
    s = str(n); wn = text_w(ctx, s, size); wu = text_w(ctx, " " + unit, sub) if unit else 0; tot = wn + wu
    rrect(ctx, x - tot / 2 - 40, y - size * 0.62, tot + 80, size * 1.24, 36); ctx.set_source_rgba(0.03, 0.03, 0.09, 0.8 * alpha); ctx.fill()
    text(ctx, s, x - tot / 2, y, size, color, align="left", alpha=alpha)
    if unit: text(ctx, " " + unit, x - tot / 2 + wn, y + size * 0.18, sub, WHITE, align="left", alpha=alpha)

def stamp(ctx, s, x, y, size, color, t, t0, rot=-0.18):
    if t < t0: return
    u = clamp((t - t0) / 0.22); k = lerp(2.2, 1.0, ease(u)); a = ease(u)
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(k, k)
    w = text_w(ctx, s, size)
    rrect(ctx, -w / 2 - 34, -size * 0.85, w + 68, size * 1.7, 18); ctx.set_source_rgba(0.03, 0.03, 0.09, 0.75 * a); ctx.fill_preserve()
    ctx.set_line_width(10); rgba(ctx, color, a); ctx.stroke()
    text(ctx, s, 0, 0, size, color, alpha=a); ctx.restore()


def burst(ctx, x, y, r, n, color, alpha, rot=0.0):
    ctx.new_path()
    for i in range(2 * n):
        a = rot + i * math.pi / n; rr = r if i % 2 == 0 else r * 0.55
        (ctx.move_to if i == 0 else ctx.line_to)(x + rr * math.cos(a), y + rr * math.sin(a))
    ctx.close_path(); rgba(ctx, color, alpha); ctx.fill()

def flame(ctx, x, y, s, t, ph, alpha=1.0):
    if s <= 0: return
    f = 1 + 0.18 * math.sin(t * 13 + ph * 7) + 0.1 * math.sin(t * 7.3 + ph * 3)
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s * f)
    sway = 0.15 * math.sin(t * 5 + ph * 4)
    ctx.new_path(); ctx.move_to(0, 0); ctx.curve_to(-0.55, -0.1, -0.45, -0.75, sway, -1.35); ctx.curve_to(0.45, -0.75, 0.55, -0.1, 0, 0); ctx.close_path()
    g = cairo.LinearGradient(0, 0, 0, -1.35)
    g.add_color_stop_rgba(0, 1, 0.95, 0.55, alpha); g.add_color_stop_rgba(0.45, 1, 0.55, 0.05, 0.95 * alpha); g.add_color_stop_rgba(1, 0.85, 0.1, 0.05, 0.0)
    ctx.set_source(g); ctx.fill(); ctx.restore()

def clock(ctx, x, y, r, t, alpha=1.0):
    ctx.arc(x, y, r, 0, 2 * math.pi); ctx.set_source_rgba(0.03, 0.05, 0.1, 0.9 * alpha); ctx.fill_preserve()
    ctx.set_line_width(8); rgba(ctx, WHITE, alpha); ctx.stroke()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_width(9)
    a = t * 6 - math.pi / 2; ctx.move_to(x, y); ctx.line_to(x + r * 0.7 * math.cos(a), y + r * 0.7 * math.sin(a)); rgba(ctx, ACCENT, alpha); ctx.stroke()
    a2 = t * 0.5 - math.pi / 2; ctx.move_to(x, y); ctx.line_to(x + r * 0.45 * math.cos(a2), y + r * 0.45 * math.sin(a2)); rgba(ctx, WHITE, alpha); ctx.stroke()

def arrow(ctx, x1, y1, x2, y2, color, alpha=1.0, w=10, head=30):
    a = math.atan2(y2 - y1, x2 - x1)
    ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND); rgba(ctx, color, alpha)
    ctx.move_to(x1, y1); ctx.line_to(x2 - head * 0.6 * math.cos(a), y2 - head * 0.6 * math.sin(a)); ctx.stroke()
    ctx.new_path(); ctx.move_to(x2, y2)
    ctx.line_to(x2 - head * math.cos(a - 0.45), y2 - head * math.sin(a - 0.45)); ctx.line_to(x2 - head * math.cos(a + 0.45), y2 - head * math.sin(a + 0.45))
    ctx.close_path(); ctx.fill()

def bubble_icon(ctx, x, y, s, alpha=1.0):
    if s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rrect(ctx, -1, -0.75, 2, 1.4, 0.4); ctx.move_to(-0.5, 0.6); ctx.line_to(-0.7, 1.0); ctx.line_to(-0.1, 0.6); ctx.close_path()
    rgba(ctx, ACCENT, alpha); ctx.fill()
    for i in (-0.45, 0, 0.45): ctx.arc(i, -0.05, 0.13, 0, 2 * math.pi); rgba(ctx, NAVY, alpha); ctx.fill()
    ctx.restore()


# ---------------- episode #9: Cleopatra vivió más cerca de ti que de las pirámides ----------------
SAND = hexc("E8B96A"); SAND_D = hexc("B98543"); SAND_DD = hexc("7E5A2C")
GOLD = hexc("F2B233"); LAPIS = hexc("2756C9"); SKIN2 = hexc("C98E5E"); DRESS = hexc("F4EFE2")
MAM = hexc("8B5A33"); MAM_D = hexc("5E3B20"); IVORY = hexc("F6EFD9")
STONE = hexc("D9C7A0"); STONE_D = hexc("A89670"); WIN = hexc("26324F")
AZT = hexc("B9A07A"); AZT_D = hexc("8C7655"); AZ_RED = hexc("C0392B"); AZ_BLUE = hexc("2E86C1")
REX = hexc("4E8F4A"); REX_D = hexc("2F5E2C"); STEG = hexc("6E8B3D"); STEG_D = hexc("4B6128"); PLATE = hexc("E07B39")
ICE = hexc("DDE7EE"); PERSON = hexc("FF8A3D"); PURPLE_C = hexc("A06CFF")

random.seed(9)
STARS = [(random.random() * W, random.random() * H * 0.7, random.uniform(1.2, 3.0), random.random()) for _ in range(120)]
DOTS = [(random.random(), random.random(), random.uniform(3, 7), random.random()) for _ in range(40)]
SNOW = [(random.random(), random.random(), random.uniform(3, 8), random.random()) for _ in range(90)]

def bg(ctx, t, warm=0.0, ice=0.0, jungle=0.0):
    top = hexc("16224A"); mid = hexc("0E1634"); bot = hexc("070B1C")
    for (amt, a, b, c) in ((warm, "2A1B4A", "4A2A3A", "1A0F14"), (ice, "0E2A4A", "123C5E", "06182A"), (jungle, "0F2A22", "0B1E18", "050F0B")):
        if amt > 0: top = mixc(top, hexc(a), amt); mid = mixc(mid, hexc(b), amt); bot = mixc(bot, hexc(c), amt)
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, top[0], top[1], top[2]); g.add_color_stop_rgb(0.55, mid[0], mid[1], mid[2]); g.add_color_stop_rgb(1, bot[0], bot[1], bot[2])
    ctx.set_source(g); ctx.paint()
    for (x, y, r, ph) in STARS:
        a = 0.25 + 0.35 * (0.5 + 0.5 * math.sin(t * 2.2 + ph * 20))
        ctx.arc(x, y, r, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, a * (1 - 0.6 * jungle)); ctx.fill()
    glow(ctx, 220 + 60 * math.sin(t * 0.3), 560, 640, mixc(BLUE, ORANGE, warm), 0.10)
    glow(ctx, 880, 1300 + 50 * math.sin(t * 0.2), 700, mixc(mixc(PURPLE_C, BLUE, ice), GREEN, jungle), 0.08)
    for (x, y, r, ph) in DOTS:
        yy = (y * H - t * (16 + 26 * ph)) % H; a = 0.08 + 0.06 * math.sin(t * 2 + ph * 9)
        ctx.new_path(); ctx.arc(x * W + 10 * math.sin(t + ph * 6), yy, r, 0, 2 * math.pi); ctx.set_source_rgba(1, 0.9, 0.75, a); ctx.fill()

def dunes(ctx, y0, t, color=SAND_D, alpha=1.0, amp=26):
    ctx.new_path(); ctx.move_to(0, H)
    for x in range(0, W + 21, 20): ctx.line_to(x, y0 + amp * math.sin(x / 170 + 0.6) + amp * 0.5 * math.sin(x / 63 + 2))
    ctx.line_to(W, H); ctx.close_path(); rgba(ctx, color, alpha); ctx.fill()

def snow(ctx, t, alpha=1.0):
    for (x, y, r, ph) in SNOW:
        yy = (y * H + t * (60 + 80 * ph)) % H; xx = (x * W + 30 * math.sin(t * 1.3 + ph * 9)) % W
        ctx.arc(xx, yy, r, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, (0.35 + 0.4 * ph) * alpha); ctx.fill()

def sun(ctx, x, y, r, t, alpha=1.0):
    if alpha <= 0 or r <= 0: return
    glow(ctx, x, y, r * 2.6, ACCENT, 0.45 * alpha)
    ctx.arc(x, y, r, 0, 2 * math.pi); rgba(ctx, ACCENT, alpha); ctx.fill()

def pyramid(ctx, cx, base, w, built=1.0, alpha=1.0, cracks=0.0):
    """Pirámide vista desde una esquina (cara izquierda iluminada). built 0..1 la construye por hiladas."""
    if alpha <= 0 or w <= 0 or built <= 0: return
    h = w * 0.62; ax, ay = cx + w * 0.06, base - h
    ctx.save(); ctx.rectangle(0, base - h * built - 1, W, h * built + 2); ctx.clip()
    ctx.new_path(); ctx.move_to(ax, ay); ctx.line_to(cx - w / 2, base); ctx.line_to(cx + w * 0.12, base); ctx.close_path(); rgba(ctx, SAND, alpha); ctx.fill()
    ctx.new_path(); ctx.move_to(ax, ay); ctx.line_to(cx + w * 0.12, base); ctx.line_to(cx + w / 2, base); ctx.close_path(); rgba(ctx, SAND_D, alpha); ctx.fill()
    ctx.set_line_width(max(1.5, w / 260)); ctx.set_source_rgba(0.35, 0.22, 0.08, 0.35 * alpha)
    n = 11
    for i in range(1, n):
        y = base - h * i / n; u = i / n
        ctx.move_to(lerp(cx - w / 2, ax, u), y); ctx.line_to(lerp(cx + w * 0.12, ax, u), y); ctx.line_to(lerp(cx + w / 2, ax, u), y)
    ctx.stroke()
    if cracks > 0:
        ctx.set_line_width(max(2, w / 160)); ctx.set_source_rgba(0.25, 0.14, 0.05, 0.8 * alpha * cracks)
        for (u0, v0, sgn) in ((0.25, 0.25, 1), (0.72, 0.4, -1), (0.45, 0.62, 1)):
            x = lerp(lerp(cx - w / 2, cx + w / 2, u0), ax, v0); y = base - h * v0
            ctx.move_to(x, y)
            for k in range(4): x += sgn * w * 0.03 * (1 if k % 2 else -1); y += h * 0.05 * cracks; ctx.line_to(x, y)
        ctx.stroke()
    ctx.restore()
    if built < 1:  # bloque subiendo
        y = base - h * built
        rrect(ctx, lerp(cx - w / 2, ax, built) + 8, y - w * 0.05, w * 0.06, w * 0.045, 4); rgba(ctx, SAND, alpha); ctx.fill()

def person(ctx, x, foot, h, color=PERSON, alpha=1.0):
    if alpha <= 0 or h <= 0: return
    rgba(ctx, color, alpha)
    ctx.arc(x, foot - 0.915 * h, 0.075 * h, 0, 2 * math.pi); ctx.fill()
    rrect(ctx, x - 0.13 * h, foot - 0.82 * h, 0.26 * h, 0.40 * h, 0.07 * h); ctx.fill()
    for s in (-1, 1):
        rrect(ctx, x + s * 0.165 * h - 0.035 * h, foot - 0.80 * h, 0.07 * h, 0.36 * h, 0.035 * h); ctx.fill()
        rrect(ctx, x + s * 0.06 * h - 0.05 * h, foot - 0.47 * h, 0.10 * h, 0.47 * h, 0.05 * h); ctx.fill()

def phone(ctx, x, y, s, alpha=1.0):
    if alpha <= 0 or s <= 0: return
    rrect(ctx, x - 0.5 * s, y - s, s, 2 * s, 0.18 * s); ctx.set_source_rgba(0.1, 0.1, 0.14, alpha); ctx.fill()
    rrect(ctx, x - 0.42 * s, y - 0.88 * s, 0.84 * s, 1.7 * s, 0.1 * s); rgba(ctx, BLUE, alpha); ctx.fill()

def cleo(ctx, x, y, s, alpha=1.0, blink=0.0):
    """Pictograma de reina egipcia: (x, y) = centro de la cara, s = radio de la cara."""
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    # tocado (atrás), a rayas
    ctx.new_path(); ctx.move_to(-1.15, -0.55); ctx.line_to(1.15, -0.55); ctx.line_to(1.45, 1.7); ctx.line_to(-1.45, 1.7); ctx.close_path()
    ctx.save(); ctx.clip_preserve(); rgba(ctx, LAPIS, alpha); ctx.fill()
    for k in range(8): ctx.rectangle(-2, -0.5 + k * 0.3, 4, 0.13); rgba(ctx, GOLD, alpha); ctx.fill()
    ctx.restore(); ctx.new_path()
    # vestido y collar
    ctx.move_to(-0.9, 1.3); ctx.line_to(0.9, 1.3); ctx.line_to(1.5, 4.2); ctx.line_to(-1.5, 4.2); ctx.close_path(); rgba(ctx, DRESS, alpha); ctx.fill()
    rrect(ctx, -0.32, 0.7, 0.64, 0.75, 0.2); rgba(ctx, SKIN2, alpha); ctx.fill()
    for k, c in enumerate((GOLD, LAPIS, GOLD, hexc("C0392B"))):
        ctx.new_path(); ctx.arc(0, 1.15, 1.25 - k * 0.16, 0.12 * math.pi, 0.88 * math.pi); ctx.arc_negative(0, 1.15, 1.09 - k * 0.16, 0.88 * math.pi, 0.12 * math.pi); ctx.close_path()
        rgba(ctx, c, alpha); ctx.fill()
    # cara
    ctx.arc(0, 0, 1, 0, 2 * math.pi); rgba(ctx, SKIN2, alpha); ctx.fill()
    # cabello lateral
    for sg in (-1, 1): rrect(ctx, sg * 1.0 - 0.18, -0.4, 0.36, 1.5, 0.15); ctx.set_source_rgba(0.08, 0.06, 0.08, alpha); ctx.fill()
    # diadema + cobra
    rrect(ctx, -1.08, -0.78, 2.16, 0.24, 0.1); rgba(ctx, GOLD, alpha); ctx.fill()
    ctx.arc(0, -0.95, 0.16, 0, 2 * math.pi); rgba(ctx, GOLD, alpha); ctx.fill()
    ctx.set_line_width(0.1); ctx.set_line_cap(cairo.LINE_CAP_ROUND); rgba(ctx, GOLD, alpha)
    ctx.move_to(0, -1.05); ctx.curve_to(0.1, -1.35, -0.1, -1.4, 0.05, -1.55); ctx.stroke()
    # ojos con delineado
    eh = 0.13 * (1 - blink)
    for sg in (-1, 1):
        ctx.save(); ctx.translate(sg * 0.38, -0.05); ctx.scale(0.2, max(0.01, eh)); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
        ctx.set_source_rgba(1, 1, 1, alpha); ctx.fill()
        ctx.arc(sg * 0.38, -0.05, 0.08 * (1 - blink) + 0.001, 0, 2 * math.pi); ctx.set_source_rgba(0.08, 0.06, 0.08, alpha); ctx.fill()
        ctx.set_line_width(0.06); ctx.set_source_rgba(0.08, 0.06, 0.08, alpha)
        ctx.move_to(sg * 0.17, -0.12); ctx.line_to(sg * 0.66, -0.12); ctx.line_to(sg * 0.74, -0.2); ctx.stroke()
        ctx.move_to(sg * 0.18, -0.3); ctx.curve_to(sg * 0.35, -0.4, sg * 0.55, -0.38, sg * 0.66, -0.3); ctx.stroke()
    ctx.save(); ctx.translate(0, 0.48); ctx.scale(0.22, 0.09); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); ctx.set_source_rgba(0.72, 0.2, 0.22, alpha); ctx.fill()
    ctx.restore()

def mammoth(ctx, x, y, s, t, alpha=1.0, walk=1.0, flip=False):
    """Mamut lanudo de perfil mirando a la derecha; (x, y) = centro del cuerpo."""
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(-s if flip else s, s)
    def leg(lx, ph, c):
        ctx.save(); ctx.translate(lx, 0.25); ctx.rotate(0.22 * walk * math.sin(t * 6 + ph)); rrect(ctx, -0.12, -0.1, 0.24, 0.85, 0.1); rgba(ctx, c, alpha); ctx.fill(); ctx.restore()
    leg(-0.42, math.pi, MAM_D); leg(0.42, 0, MAM_D)
    ctx.set_line_width(0.07); ctx.set_line_cap(cairo.LINE_CAP_ROUND); rgba(ctx, MAM_D, alpha)
    ctx.move_to(-0.85, -0.1); ctx.curve_to(-1.0, 0.0, -1.0, 0.2, -1.05, 0.35); ctx.stroke()
    ctx.save(); ctx.scale(0.88, 0.58); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); rgba(ctx, MAM, alpha); ctx.fill()
    ctx.arc(0.72, -0.32, 0.45, 0, 2 * math.pi); rgba(ctx, MAM, alpha); ctx.fill()
    ctx.arc(0.78, -0.68, 0.27, 0, 2 * math.pi); rgba(ctx, MAM, alpha); ctx.fill()
    # pelaje
    ctx.set_line_width(0.05); rgba(ctx, MAM_D, alpha)
    for k in range(12):
        xx = -0.75 + k * 0.13; ctx.move_to(xx, 0.35 + 0.1 * math.sin(k)); ctx.line_to(xx - 0.03, 0.62 + 0.06 * math.sin(k * 2.3 + t * 3))
    ctx.stroke()
    leg(-0.2, 0, MAM); leg(0.62, math.pi, MAM)
    sw = 0.08 * math.sin(t * 2.5)
    ctx.set_line_width(0.18); rgba(ctx, MAM, alpha)
    ctx.move_to(1.05, -0.25); ctx.curve_to(1.3, 0.15 + sw, 1.25, 0.6, 1.08 + sw, 0.8); ctx.stroke()
    ctx.set_line_width(0.1); rgba(ctx, IVORY, alpha)
    ctx.move_to(0.98, -0.05); ctx.curve_to(1.3, 0.4, 1.65, 0.25, 1.6, -0.08); ctx.stroke()
    ctx.save(); ctx.translate(0.55, -0.3); ctx.scale(0.16, 0.24); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); rgba(ctx, MAM_D, alpha); ctx.fill()
    ctx.arc(0.9, -0.42, 0.05, 0, 2 * math.pi); ctx.set_source_rgba(0.05, 0.03, 0.02, alpha); ctx.fill()
    ctx.restore()

def island(ctx, cx, cy, r, t, alpha=1.0):
    if alpha <= 0 or r <= 0: return
    ctx.new_path()
    for i in range(61):
        a = i / 60 * 2 * math.pi; rr = r * (1 + 0.16 * math.sin(3 * a + 0.5) + 0.08 * math.sin(7 * a + 1) + 0.04 * math.sin(13 * a))
        (ctx.move_to if i == 0 else ctx.line_to)(cx + rr * math.cos(a) * 1.25, cy + rr * math.sin(a) * 0.6)
    ctx.close_path(); ctx.set_line_width(14); ctx.set_source_rgba(0.6, 0.85, 1, 0.35 * alpha); ctx.stroke_preserve(); rgba(ctx, ICE, alpha); ctx.fill()
    ctx.save(); ctx.translate(cx - r * 0.1, cy + r * 0.05); ctx.scale(r * 0.7, r * 0.3); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
    ctx.set_source_rgba(0.55, 0.62, 0.55, 0.6 * alpha); ctx.fill()

def floes(ctx, t, alpha=1.0):
    random.seed(91)
    for i in range(14):
        x = (random.random() * W + t * 12 * (0.5 + random.random())) % (W + 200) - 100; y = random.uniform(500, 1300); r = random.uniform(18, 46)
        ctx.save(); ctx.translate(x, y); ctx.scale(r, r * 0.45); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); ctx.set_source_rgba(0.9, 0.95, 1, 0.45 * alpha); ctx.fill()

def oxford(ctx, cx, base, s, built=1.0, alpha=1.0):
    """Edificio universitario gótico genérico; ancho ≈ 360·s."""
    if alpha <= 0 or built <= 0: return
    ctx.save(); ctx.rectangle(0, base - 520 * s * built, W, 520 * s * built + 1); ctx.clip()
    ctx.translate(cx, base); ctx.scale(s, s)
    rgba(ctx, STONE, alpha); ctx.rectangle(-150, -230, 300, 230); ctx.fill()
    for k in range(7): ctx.rectangle(-150 + k * 46, -255, 26, 26); ctx.fill()
    for sg in (-1, 1):
        rgba(ctx, STONE_D, alpha); ctx.rectangle(sg * 165 - 32, -380, 64, 380); ctx.fill()
        ctx.new_path(); ctx.move_to(sg * 165 - 38, -380); ctx.line_to(sg * 165, -500); ctx.line_to(sg * 165 + 38, -380); ctx.close_path(); ctx.fill()
        for k in range(3):
            yy = -330 + k * 100; ctx.new_path(); ctx.move_to(sg * 165 - 12, yy + 50); ctx.line_to(sg * 165 - 12, yy + 14); ctx.line_to(sg * 165, yy); ctx.line_to(sg * 165 + 12, yy + 14); ctx.line_to(sg * 165 + 12, yy + 50); ctx.close_path()
            rgba(ctx, WIN, alpha); ctx.fill()
    for row in range(2):
        for k in range(5):
            xx = -110 + k * 55; yy = -200 + row * 90
            if row == 1 and k == 2: continue
            ctx.new_path(); ctx.move_to(xx - 14, yy + 60); ctx.line_to(xx - 14, yy + 18); ctx.line_to(xx, yy); ctx.line_to(xx + 14, yy + 18); ctx.line_to(xx + 14, yy + 60); ctx.close_path()
            ctx.set_source_rgba(0.98, 0.82, 0.4, 0.85 * alpha); ctx.fill()
    ctx.new_path(); ctx.move_to(-38, 0); ctx.line_to(-38, -70); ctx.curve_to(-38, -110, 0, -130, 0, -130); ctx.curve_to(0, -130, 38, -110, 38, -70); ctx.line_to(38, 0); ctx.close_path(); rgba(ctx, WIN, alpha); ctx.fill()
    ctx.restore()

def temple(ctx, cx, base, s, built=1.0, alpha=1.0):
    """Templo escalonado mexica genérico con dos santuarios arriba; ancho ≈ 400·s."""
    if alpha <= 0 or built <= 0: return
    ctx.save(); ctx.rectangle(0, base - 400 * s * built, W, 400 * s * built + 1); ctx.clip()
    ctx.translate(cx, base); ctx.scale(s, s)
    y = 0
    for k, w in enumerate((400, 330, 260, 190)):
        rgba(ctx, AZT if k % 2 == 0 else AZT_D, alpha); ctx.rectangle(-w / 2, y - 62, w, 62); ctx.fill()
        ctx.set_source_rgba(0, 0, 0, 0.15 * alpha); ctx.rectangle(-w / 2, y - 8, w, 8); ctx.fill()
        y -= 62
    ctx.new_path(); ctx.move_to(-55, 0); ctx.line_to(-38, y); ctx.line_to(38, y); ctx.line_to(55, 0); ctx.close_path(); ctx.set_source_rgba(0.45, 0.36, 0.25, alpha); ctx.fill()
    ctx.set_line_width(3); ctx.set_source_rgba(0.75, 0.65, 0.5, alpha)
    for k in range(1, 16): yy = y * k / 16; ctx.move_to(-50 + 15 * k / 16, yy); ctx.line_to(50 - 15 * k / 16, yy)
    ctx.stroke()
    for sg, c in ((-1, AZ_RED), (1, AZ_BLUE)):
        rgba(ctx, c, alpha); ctx.rectangle(sg * 52 - 36, y - 70, 72, 70); ctx.fill()
        ctx.new_path(); ctx.move_to(sg * 52 - 44, y - 70); ctx.line_to(sg * 52, y - 108); ctx.line_to(sg * 52 + 44, y - 70); ctx.close_path(); ctx.fill()
        ctx.set_source_rgba(0.1, 0.06, 0.05, alpha); ctx.rectangle(sg * 52 - 14, y - 40, 28, 40); ctx.fill()
    ctx.restore()

def trex(ctx, x, y, s, t, alpha=1.0, walk=1.0, jaw=0.0, color=REX, dark=REX_D):
    """T. rex de perfil mirando a la derecha; (x, y) = centro del cuerpo."""
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    def leg(lx, ph, c):
        ctx.save(); ctx.translate(lx, 0.15); ctx.rotate(0.25 * walk * math.sin(t * 5 + ph))
        ctx.save(); ctx.scale(0.24, 0.34); ctx.arc(0, 0.2, 1, 0, 2 * math.pi); ctx.restore(); rgba(ctx, c, alpha); ctx.fill()
        rrect(ctx, -0.07, 0.3, 0.14, 0.62, 0.06); ctx.fill(); rrect(ctx, -0.05, 0.86, 0.3, 0.1, 0.04); ctx.fill(); ctx.restore()
    leg(-0.15, math.pi, dark)
    rgba(ctx, color, alpha)
    ctx.new_path(); ctx.move_to(-0.35, -0.3); ctx.curve_to(-0.9, -0.3, -1.4, -0.15, -1.85, 0.0); ctx.curve_to(-1.4, 0.05, -0.9, 0.2, -0.35, 0.28); ctx.close_path(); ctx.fill()
    ctx.save(); ctx.rotate(-0.18); ctx.scale(0.62, 0.38); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); ctx.fill()
    ctx.new_path(); ctx.move_to(0.3, -0.25); ctx.line_to(0.62, -0.7); ctx.line_to(0.86, -0.5); ctx.line_to(0.55, 0.05); ctx.close_path(); ctx.fill()
    ctx.save(); ctx.translate(0.75, -0.6); ctx.rotate(0.25 * jaw); rrect(ctx, 0.0, 0.0, 0.62, 0.13, 0.05); rgba(ctx, dark, alpha); ctx.fill(); ctx.restore()
    rrect(ctx, 0.55, -0.92, 0.85, 0.34, 0.12); rgba(ctx, color, alpha); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, alpha)
    for k in range(5):
        xx = 0.85 + k * 0.11; ctx.new_path(); ctx.move_to(xx, -0.58); ctx.line_to(xx + 0.04, -0.5); ctx.line_to(xx + 0.08, -0.58); ctx.close_path(); ctx.fill()
    ctx.arc(0.85, -0.8, 0.06, 0, 2 * math.pi); ctx.set_source_rgba(1, 0.85, 0.2, alpha); ctx.fill()
    ctx.arc(0.86, -0.8, 0.028, 0, 2 * math.pi); ctx.set_source_rgba(0, 0, 0, alpha); ctx.fill()
    ctx.set_line_width(0.07); ctx.set_line_cap(cairo.LINE_CAP_ROUND); rgba(ctx, dark, alpha)
    ctx.move_to(0.45, -0.05); ctx.line_to(0.62, 0.08); ctx.line_to(0.66, 0.18); ctx.stroke()
    leg(0.1, 0, color)
    ctx.restore()

def stego(ctx, x, y, s, t, alpha=1.0, walk=1.0):
    """Estegosaurio de perfil mirando a la derecha; (x, y) = centro del cuerpo."""
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    def leg(lx, ln, ph, c):
        ctx.save(); ctx.translate(lx, 0.15); ctx.rotate(0.18 * walk * math.sin(t * 4 + ph)); rrect(ctx, -0.1, -0.05, 0.2, ln, 0.08); rgba(ctx, c, alpha); ctx.fill(); ctx.restore()
    leg(-0.45, 0.72, math.pi, STEG_D); leg(0.45, 0.58, 0, STEG_D)
    for k in range(9):
        a = math.pi * (1.1 + 0.8 * k / 8); px = 0.82 * math.cos(a); py = 0.42 * math.sin(a); sz = 0.16 + 0.14 * math.sin(math.pi * k / 8)
        nx, ny = math.cos(a), math.sin(a) * 1.6; L = math.hypot(nx, ny); nx /= L; ny /= L
        ctx.new_path(); ctx.move_to(px - ny * sz * 0.5, py + nx * sz * 0.5); ctx.line_to(px + nx * sz * 1.6, py + ny * sz * 1.6); ctx.line_to(px + ny * sz * 0.5, py - nx * sz * 0.5); ctx.close_path()
        rgba(ctx, PLATE, alpha); ctx.fill()
    rgba(ctx, STEG, alpha)
    ctx.new_path(); ctx.move_to(-0.6, -0.15); ctx.curve_to(-1.0, -0.05, -1.3, 0.1, -1.65, 0.2); ctx.curve_to(-1.3, 0.25, -1.0, 0.3, -0.6, 0.25); ctx.close_path(); ctx.fill()
    ctx.set_line_width(0.06); ctx.set_line_cap(cairo.LINE_CAP_ROUND); rgba(ctx, IVORY, alpha)
    for (sx, sy, ex, ey) in ((-1.4, 0.15, -1.55, -0.12), (-1.5, 0.17, -1.75, -0.05), (-1.45, 0.24, -1.6, 0.45), (-1.55, 0.24, -1.8, 0.4)):
        ctx.move_to(sx, sy); ctx.line_to(ex, ey)
    ctx.stroke()
    ctx.save(); ctx.scale(0.85, 0.42); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); rgba(ctx, STEG, alpha); ctx.fill()
    ctx.new_path(); ctx.move_to(0.6, -0.1); ctx.curve_to(0.9, 0.0, 1.0, 0.15, 1.1, 0.25); ctx.line_to(1.05, 0.38); ctx.curve_to(0.9, 0.3, 0.75, 0.3, 0.6, 0.25); ctx.close_path(); ctx.fill()
    ctx.save(); ctx.translate(1.17, 0.3); ctx.scale(0.2, 0.11); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); ctx.fill()
    ctx.arc(1.22, 0.27, 0.025, 0, 2 * math.pi); ctx.set_source_rgba(0, 0, 0, alpha); ctx.fill()
    leg(-0.25, 0.72, 0, STEG); leg(0.6, 0.58, math.pi, STEG)
    ctx.restore()

def bar(ctx, x0, x1, y, prog, color, alpha=1.0, th=26):
    if prog <= 0 or alpha <= 0: return
    xe = lerp(x0, x1, clamp(prog))
    rrect(ctx, min(x0, xe), y - th / 2, abs(xe - x0), th, th / 2); rgba(ctx, color, alpha); ctx.fill()

def track(ctx, x0, x1, y, alpha=1.0):
    if alpha <= 0: return
    rrect(ctx, x0 - 10, y - 6, x1 - x0 + 20, 12, 6); ctx.set_source_rgba(1, 1, 1, 0.22 * alpha); ctx.fill()

def dot(ctx, x, y, color, alpha=1.0, r=20):
    if alpha <= 0: return
    ctx.arc(x, y, r + 6, 0, 2 * math.pi); ctx.set_source_rgba(0.03, 0.03, 0.09, alpha); ctx.fill()
    ctx.arc(x, y, r, 0, 2 * math.pi); rgba(ctx, color, alpha); ctx.fill()

def tick_label(ctx, x, y, s1, s2=None, color=WHITE, alpha=1.0, size=40):
    if alpha <= 0: return
    text(ctx, s1, x, y, size, color, stroke=8, alpha=alpha)
    if s2: text(ctx, s2, x, y + size * 1.05, size * 0.72, hexc("C8CEE0"), stroke=6, alpha=alpha)

def qmarks(ctx, t, t0, pts, colors):
    for i, (qx, qy) in enumerate(pts):
        if t > t0 + i * 0.15:
            ctx.save(); ctx.translate(qx, qy + 10 * math.sin(t * 3 + i)); ctx.rotate(0.2 * math.sin(t * 2 + i))
            pop_text(ctx, "?", 0, 0, 120, colors[i % len(colors)], t, t0 + i * 0.15, stroke=10); ctx.restore()

# timeline Cleopatra: pirámide (2560 a. C.) — Cleopatra (69 a. C.) — hoy (2026)
TX0, TX1 = 130, 890
TXC = TX0 + (TX1 - TX0) * (2560 - 69) / (2560 + 2026)
# timeline dinosaurios: estegosaurio (~150 Ma) — T. rex (~67 Ma) — hoy
DX0, DX1 = 130, 890
DXR = DX0 + (DX1 - DX0) * (150 - 67) / 150

# ---------------- scenes ----------------
def s_hook(ctx, t):  # 0–3.2: gancho visible desde el cuadro 0
    bg(ctx, t, warm=0.8)
    dunes(ctx, 1290, t, SAND_DD, 0.9)
    text(ctx, "CLEOPATRA", W / 2, 320, 132, ACCENT, stroke=16)
    text(ctx, "MÁS CERCA DE TI", W / 2, 460, 98, WHITE, stroke=14)
    ty = 1130
    track(ctx, TX0, TX1, ty)
    cx = lerp(380, TXC, ease(t / 1.8))
    bar(ctx, TX0, cx, ty, 1, ACCENT); bar(ctx, cx, TX1, ty, 1, GREEN)
    pyramid(ctx, TX0 + 10, ty - 30, 230)
    person(ctx, TX1, ty - 30, 250, PERSON)
    phone(ctx, TX1 + 48, ty - 150, 20)
    cleo(ctx, cx, ty - 300 + 12 * math.sin(t * 3), 62)
    dot(ctx, TX0, ty, ACCENT); dot(ctx, cx, ty, WHITE); dot(ctx, TX1, ty, GREEN)
    if t > 2.0:
        a = ease((t - 2.0) / 0.3)
        tick_label(ctx, (TX0 + cx) / 2, ty + 70, "LEJOS", color=ACCENT, alpha=a)
        tick_label(ctx, (cx + TX1) / 2, ty + 70, "CERCA", color=GREEN, alpha=a)

def s_pyramid(ctx, t):  # 3.2–8.3
    bg(ctx, t, warm=1.0)
    if t < 5.7: header(ctx, "La Gran", "PIRÁMIDE", t, 3.25, size=104)
    else: header(ctx, "Se terminó hacia el", "AÑO…", t, 5.75, size=84)
    sun(ctx, 860, 640, 60, t, ease((t - 3.3) / 0.5))
    dunes(ctx, 1230, t, SAND_DD)
    b = ease((t - 3.35) / 2.0)
    pyramid(ctx, W / 2 - 30, 1250, 780, built=b)
    if t > 4.3: label(ctx, "GUIZA · EGIPTO", W / 2, 1310, 42, SAND, ease((t - 4.3) / 0.3))
    if t > 5.76:
        n = int(2560 * ease((t - 5.76) / 0.8))
        ctx.save(); ctx.translate(W / 2, 520); s = back((t - 5.76) / 0.3); ctx.scale(s, s)
        counter_box(ctx, 0, 0, n, "", size=150); ctx.restore()
    if t > 7.55:
        stamp(ctx, "ANTES DE CRISTO", W / 2, 690, 58, ORANGE_L, t, 7.55, rot=-0.06)

def s_born(ctx, t):  # 8.3–11.7
    bg(ctx, t, warm=0.7)
    if t < 9.55: header(ctx, "Cleopatra", "NACIÓ", t, 8.35, size=104)
    else: header(ctx, "Casi", "2500 AÑOS DESPUÉS", t, 9.6, size=86)
    ty = 1130
    track(ctx, TX0, TX1, ty)
    pyramid(ctx, TX0 + 10, ty - 30, 230)
    dot(ctx, TX0, ty, ACCENT)
    tick_label(ctx, TX0 + 10, ty + 70, "2560", "a. C.", ACCENT)
    p = ease((t - 9.6) / 1.3)
    bar(ctx, TX0, TXC, ty, p, ACCENT)
    k = back((t - 8.45) / 0.45)
    cleo(ctx, TXC + 10, ty - 320 + 10 * math.sin(t * 2.5), 70 * k, blink=1.0 if 10.6 < t < 10.72 else 0.0)
    if p >= 1 or t > 9.0:
        dot(ctx, TXC, ty, WHITE, ease((t - 9.0) / 0.3))
        tick_label(ctx, TXC, ty + 70, "69", "a. C.", WHITE, ease((t - 9.0) / 0.3))
    if t > 9.6:
        n = int(2500 * ease((t - 9.6) / 1.0))
        ctx.save(); ctx.translate(265, 760); s = back((t - 9.6) / 0.3); ctx.scale(s, s)
        counter_box(ctx, 0, 0, f"+{n}", "", size=86); ctx.restore()

def s_you(ctx, t):  # 11.7–15.3
    bg(ctx, t, warm=0.5)
    if t < 13.9: header(ctx, "Entre Cleopatra y", "TÚ", t, 11.75, size=88, c2=GREEN)
    else: header(ctx, "Apenas", "2100 AÑOS", t, 13.95, size=100, c2=GREEN)
    ty = 1130
    track(ctx, TX0, TX1, ty)
    bar(ctx, TX0, TXC, ty, 1, ACCENT)
    p = ease((t - 12.9) / 1.4)
    bar(ctx, TXC, TX1, ty, p, GREEN)
    pyramid(ctx, TX0 + 10, ty - 30, 230)
    cleo(ctx, TXC, ty - 290, 55)
    k = back((t - 12.75) / 0.4)
    person(ctx, TX1, ty - 30, 250 * k, PERSON); phone(ctx, TX1 + 48, ty - 150, 20 * k)
    dot(ctx, TX0, ty, ACCENT); dot(ctx, TXC, ty, WHITE); dot(ctx, TX1, ty, GREEN, ease((t - 12.8) / 0.3))
    tick_label(ctx, TX0 + 10, ty + 70, "2560", "a. C.", ACCENT)
    tick_label(ctx, TXC, ty + 70, "69", "a. C.", WHITE)
    if t > 12.8: tick_label(ctx, TX1, ty + 70, "HOY", None, GREEN, ease((t - 12.8) / 0.3))
    text(ctx, "2500", (TX0 + TXC) / 2, ty - 70, 56, ACCENT, stroke=10)
    if t > 13.92:
        n = int(2100 * ease((t - 13.92) / 0.8))
        ctx.save(); ctx.translate((TXC + TX1) / 2 + 10, ty - 70); s = back((t - 13.92) / 0.3); ctx.scale(s, s)
        text(ctx, str(n), 0, 0, 56, GREEN, stroke=10); ctx.restore()
    if t > 14.55: stamp(ctx, "¡MÁS CERCA!", W / 2, 560, 66, GREEN, t, 14.55, rot=-0.08)

def s_ruins(ctx, t):  # 15.3–18.5
    bg(ctx, t, warm=0.9)
    if t < 17.35: header(ctx, "Para ella, las", "PIRÁMIDES…", t, 15.35, size=88, c2=SAND)
    else: header(ctx, "ya eran", "ANTIQUÍSIMAS", t, 17.4, size=96)
    dunes(ctx, 1240, t, SAND_DD)
    cr = ease((t - 16.3) / 1.2)
    pyramid(ctx, 690, 1250, 620, cracks=cr)
    random.seed(15)
    for i in range(22):
        ph = random.random(); x0 = random.uniform(420, 980); y0 = random.uniform(700, 1240)
        u = ((t - 15.3) * 0.4 + ph) % 1
        ctx.arc(x0 + 40 * u, y0 - 80 * u, random.uniform(3, 7), 0, 2 * math.pi); ctx.set_source_rgba(0.95, 0.8, 0.55, 0.35 * (1 - u) * cr); ctx.fill()
    cleo(ctx, 210, 780 + 8 * math.sin(t * 2), 70 * back((t - 15.4) / 0.4))
    if t > 15.9:
        a = ease((t - 15.9) / 0.3); ctx.set_dash([14, 10]); ctx.set_line_width(5); ctx.set_source_rgba(1, 1, 1, 0.5 * a)
        ctx.move_to(300, 790); ctx.line_to(560, 900); ctx.stroke(); ctx.set_dash([])
    if t > 17.4: stamp(ctx, "+2500 AÑOS", 700, 640, 64, ORANGE_L, t, 17.4)

def s_twist(ctx, t):  # 18.5–20.1
    bg(ctx, t, warm=0.3)
    sh = 8 * math.sin(t * 50) * clamp((t - 19.5) / 0.1) * (1 - clamp((t - 19.9) / 0.15))
    pop_text(ctx, "PERO HAY", W / 2 + sh, 560, 132, WHITE, t, 18.55)
    pop_text(ctx, "ALGO", W / 2 + sh, 720, 150, WHITE, t, 19.0)
    pop_text(ctx, "MÁS RARO", W / 2 + sh, 890, 150, ACCENT, t, 19.5)
    qmarks(ctx, t, 18.7, [(170, 1120), (W / 2, 1180), (900, 1110)], [ACCENT, PURPLE_C, ORANGE_L])

def s_mammoth(ctx, t):  # 20.1–24.1
    bg(ctx, t, warm=0.7 * (1 - ease((t - 22.2) / 1.0)), ice=0.5 * ease((t - 22.2) / 1.0))
    if t < 22.1: header(ctx, "Mientras construían las", "PIRÁMIDES", t, 20.15, size=76, c2=SAND)
    else: header(ctx, "Había", "MAMUTS VIVOS", t, 22.15, size=98, c2=ORANGE_L)
    dunes(ctx, 1200, t, SAND_DD)
    pyramid(ctx, 280, 1215, 420, built=ease((t - 20.2) / 1.8))
    mx = lerp(1300, 770, ease((t - 22.4) / 1.4))
    mammoth(ctx, mx, 1010, 160, t, walk=1 - 0.7 * ease((t - 23.6) / 0.4))
    if t > 23.3:
        a = ease((t - 23.3) / 0.3)
        label(ctx, "AL MISMO TIEMPO", W / 2, 520, 50, WHITE, a)
        text(ctx, "=", 520, 1000, 120, ACCENT, stroke=12, alpha=a)

def s_wrangel(ctx, t):  # 24.1–28.7
    bg(ctx, t, ice=1.0)
    if t < 25.6: header(ctx, "Los", "ÚLTIMOS", t, 24.15, size=108, c2=ORANGE_L)
    else: header(ctx, "En una isla del", "ÁRTICO", t, 25.65, size=98, c2=BLUE)
    floes(ctx, t)
    k = back((t - 24.3) / 0.5)
    island(ctx, W / 2, 870, 290 * k, t)
    if t > 24.3:
        mammoth(ctx, W / 2 - 40, 830, 95 * back((t - 24.4) / 0.4), t, walk=0.6)
    if t > 26.1: label(ctx, "ISLA DE WRANGEL", W / 2, 1110, 46, ICE, ease((t - 26.1) / 0.3))
    snow(ctx, t, 0.9)
    if t > 27.36:
        n = int(4000 * ease((t - 27.36) / 0.7))
        ctx.save(); ctx.translate(W / 2, 520); s = back((t - 27.36) / 0.3); ctx.scale(s, s)
        counter_box(ctx, 0, 0, n, "AÑOS", size=120, sub=52); ctx.restore()
        label(ctx, "HASTA HACE", W / 2, 420, 40, WHITE, ease((t - 27.36) / 0.3), bg=False)

def s_oxford(ctx, t):  # 28.7–35.7
    bg(ctx, t, warm=0.2)
    if t < 29.85: header(ctx, "Y otro", "MÁS:", t, 28.75, size=110)
    elif t < 32.1: header(ctx, "Universidad de", "OXFORD", t, 29.9, size=96)
    elif t < 34.55: header(ctx, "Más de", "200 AÑOS ANTES", t, 32.15, size=86, c2=ORANGE_L)
    else: header(ctx, "de que existiera", "TENOCHTITLAN", t, 34.6, size=86, c2=GREEN)
    gy = 1200
    ctx.rectangle(0, gy, W, H - gy); ctx.set_source_rgba(0.12, 0.2, 0.16, 1); ctx.fill()
    oxford(ctx, 290, gy, 0.95, built=ease((t - 29.9) / 1.0))
    if t > 30.6:
        ctx.save(); ctx.translate(290, 610); s = back((t - 30.6) / 0.3); ctx.scale(s, s)
        counter_box(ctx, 0, 0, "1096", "", size=80); ctx.restore()
        label(ctx, "YA DABA CLASES", 290, 1260, 38, WHITE, ease((t - 31.2) / 0.3))
    if t < 33.7 and t > 29.0:
        # un "lote vacío": nada todavía
        a = ease((t - 30.2) / 0.3) * (1 - ease((t - 33.4) / 0.3))
        ctx.set_dash([16, 12]); ctx.set_line_width(5); ctx.set_source_rgba(1, 1, 1, 0.45 * a)
        rrect(ctx, 590, 860, 340, 330, 20); ctx.stroke(); ctx.set_dash([])
        text(ctx, "?", 760, 1020, 120, WHITE, stroke=10, alpha=0.6 * a)
    temple(ctx, 760, gy, 0.85, built=ease((t - 33.7) / 0.9))
    if t > 32.2:
        p = ease((t - 32.2) / 1.0)
        arrow(ctx, 380, 760, lerp(380, 690, p), 760, ORANGE_L, ease((t - 32.2) / 0.2), w=12, head=34)
        if t > 32.6: text(ctx, "+200", 535, 700, 60, ORANGE_L, stroke=10, alpha=ease((t - 32.6) / 0.3))
    if t > 34.7:
        ctx.save(); ctx.translate(760, 610); s = back((t - 34.7) / 0.3); ctx.scale(s, s)
        counter_box(ctx, 0, 0, "1325", "", size=80, color=GREEN); ctx.restore()
        label(ctx, "AZTECAS", 760, 1260, 38, GREEN, ease((t - 34.8) / 0.3))

def s_loco(ctx, t):  # 35.7–37.0
    bg(ctx, t, jungle=0.6)
    sh = 8 * math.sin(t * 50) * clamp((t - 36.3) / 0.1) * (1 - clamp((t - 36.8) / 0.15))
    pop_text(ctx, "¿Y EL", W / 2 + sh, 560, 140, WHITE, t, 35.72)
    pop_text(ctx, "MÁS LOCO?", W / 2 + sh, 730, 150, ACCENT, t, 36.0)
    rise = ease((t - 35.8) / 0.9)
    trex(ctx, 420, lerp(1600, 1280, rise), 260, t, walk=0, jaw=0.5 + 0.5 * math.sin(t * 6))

def s_dinos(ctx, t):  # 37.0–40.5
    bg(ctx, t, jungle=1.0)
    if t < 38.85: header(ctx, "El", "TIRANOSAURIO", t, 37.05, size=100, c2=GREEN)
    elif t < 39.4: header(ctx, "más cerca de", "TI", t, 38.9, size=104, c2=PERSON)
    else: header(ctx, "que del", "ESTEGOSAURIO", t, 39.45, size=94, c2=PLATE)
    gy = 1230
    ctx.rectangle(0, gy, W, H - gy); ctx.set_source_rgba(0.1, 0.22, 0.12, 1); ctx.fill()
    rx = lerp(1200, 600, ease((t - 37.05) / 1.2))
    trex(ctx, rx, 960, 150, t, walk=1 - ease((t - 38.2) / 0.4), jaw=0.3 + 0.3 * math.sin(t * 4))
    k = back((t - 38.9) / 0.4)
    person(ctx, 930, gy, 230 * k, PERSON)
    if t > 38.9: arrow(ctx, 790, 760, 880, 820, PERSON, ease((t - 38.9) / 0.2), w=10, head=30)
    sx = lerp(-250, 210, ease((t - 39.45) / 0.9))
    stego(ctx, sx, 1080, 120, t, walk=1 - ease((t - 40.2) / 0.3))

def dino_timeline(ctx, t, p1, p2, a_hoy):
    ty = 1130
    track(ctx, DX0, DX1, ty)
    bar(ctx, DX0, DXR, ty, p1, RED); bar(ctx, DXR, DX1, ty, p2, GREEN)
    stego(ctx, DX0 + 40, ty - 120, 62, t, walk=0)
    trex(ctx, DXR, ty - 140, 70, t, walk=0, jaw=0.2)
    person(ctx, DX1, ty - 30, 200 * a_hoy, PERSON)
    dot(ctx, DX0, ty, RED); dot(ctx, DXR, ty, WHITE); dot(ctx, DX1, ty, GREEN, a_hoy)
    tick_label(ctx, DX0 + 30, ty + 70, "JURÁSICO", "~150 M", PLATE, size=36)
    tick_label(ctx, DXR, ty + 70, "CRETÁCICO", "~66 M", WHITE, size=36)
    tick_label(ctx, DX1 - 20, ty + 70, "HOY", None, GREEN, a_hoy, size=36)

def s_gap1(ctx, t):  # 40.5–43.5
    bg(ctx, t, jungle=0.8)
    header(ctx, "Entre", "ELLOS", t, 40.55, size=110, c2=RED)
    dino_timeline(ctx, t, ease((t - 40.7) / 1.2), 0, ease((t - 40.6) / 0.3))
    if t > 41.6:
        n = int(80 * ease((t - 41.6) / 0.6))
        ctx.save(); ctx.translate(W / 2, 560); s = back((t - 41.6) / 0.3); ctx.scale(s, s)
        counter_box(ctx, 0, 0, f"+{n}", "MILLONES DE AÑOS", color=RED, size=120, sub=40); ctx.restore()
        ctx.set_dash([12, 10]); ctx.set_line_width(5); ctx.set_source_rgba(1, 0.4, 0.4, 0.6 * ease((t - 41.8) / 0.3))
        ctx.move_to(W / 2 - 80, 650); ctx.line_to((DX0 + DXR) / 2, 1090); ctx.stroke(); ctx.set_dash([])

def s_gap2(ctx, t):  # 43.5–47.2
    bg(ctx, t, jungle=0.8)
    if t < 45.4: header(ctx, "Entre el T. rex y", "TÚ", t, 43.55, size=90, c2=PERSON)
    else: header(ctx, "Solo", "66 MILLONES", t, 45.45, size=100, c2=GREEN)
    dino_timeline(ctx, t, 1, ease((t - 43.8) / 1.4), 1)
    text(ctx, "80", (DX0 + DXR) / 2, 1060, 60, RED, stroke=10)
    if t > 45.44:
        n = int(66 * ease((t - 45.44) / 0.6))
        ctx.save(); ctx.translate((DXR + DX1) / 2, 1060); s = back((t - 45.44) / 0.3); ctx.scale(s, s)
        text(ctx, str(n), 0, 0, 60, GREEN, stroke=10); ctx.restore()
    if t > 46.2: stamp(ctx, "¡MÁS CERCA DE TI!", W / 2, 600, 64, GREEN, t, 46.2, rot=-0.07)
    elif t > 44.0:
        a = ease((t - 44.0) / 0.3)
        trex(ctx, W / 2, 680, 120, t, walk=0, jaw=0.5 + 0.5 * math.sin(t * 7), alpha=a)

def s_ask(ctx, t):  # 47.2–48.7
    bg(ctx, t, warm=0.4)
    pop_text(ctx, "¿CUÁL TE", W / 2, 420, 120, WHITE, t, 47.22)
    pop_text(ctx, "SORPRENDIÓ MÁS?", W / 2, 560, 96, ACCENT, t, 47.5)
    cells = [(300, 820), (780, 820), (300, 1170), (780, 1170)]
    for i, (cx, cy) in enumerate(cells):
        k = back((t - 47.4 - i * 0.12) / 0.35)
        if k <= 0: continue
        ctx.save(); ctx.translate(cx, cy); ctx.scale(k, k)
        rrect(ctx, -210, -150, 420, 300, 36); ctx.set_source_rgba(0.03, 0.03, 0.09, 0.75); ctx.fill()
        ctx.restore()
        if i == 0: cleo(ctx, cx - 70, cy - 30, 48 * k); pyramid(ctx, cx + 90, cy + 110, 180 * k)
        elif i == 1: mammoth(ctx, cx, cy, 95 * k, t, walk=0.5)
        elif i == 2: oxford(ctx, cx, cy + 130, 0.5 * k)
        else: trex(ctx, cx + 40, cy + 10, 68 * k, t, walk=0, jaw=0.3)
        pop_text(ctx, str(i + 1), cx - 170, cy - 110, 64, ACCENT, t, 47.6 + i * 0.12, stroke=10)

def s_end(ctx, t):  # 48.7–fin
    T0 = END_START
    bg(ctx, t, warm=0.3)
    a = ease((t - T0) / 0.5)
    mammoth(ctx, lerp(-200, 1280, ((t - T0) / 6.0) % 1), 1480, 70, t, alpha=a)
    sc = 0.85 + 0.15 * back((t - T0) / 0.5); s = 300 * sc
    logo_mark(ctx, (W - s) / 2, 470 + (300 - s) / 2, s, a)
    w1 = text_w(ctx, "Logi", 120); w2 = text_w(ctx, "Datos", 120); x0 = (W - w1 - w2) / 2
    text(ctx, "Logi", x0, 900, 120, WHITE, align="left", alpha=a); text(ctx, "Datos", x0 + w1, 900, 120, ACCENT, align="left", alpha=a)
    text(ctx, "Curiosidades con lógica y datos", W / 2, 1010, 48, hexc("C8CEE0"), bold=False, alpha=a)
    bubble_icon(ctx, W / 2 - 250, 1180, 50 * back((t - T0 - 0.1) / 0.35))
    pa = back((t - T0 - 0.8) / 0.4)
    if pa > 0:
        ctx.save(); ctx.translate(W / 2 + 60, 1175); ctx.scale(pa, pa)
        pw = text_w(ctx, "SÍGUENOS", 54) + 100; rrect(ctx, -pw / 2, -52, pw, 104, 52); rgba(ctx, ACCENT); ctx.fill()
        text(ctx, "SÍGUENOS", 0, 0, 54, NAVY); ctx.restore()

END_START = 48.7
SCENES = [(0.0, s_hook), (3.2, s_pyramid), (8.3, s_born), (11.7, s_you), (15.3, s_ruins), (18.5, s_twist), (20.1, s_mammoth),
          (24.1, s_wrangel), (28.7, s_oxford), (35.7, s_loco), (37.0, s_dinos), (40.5, s_gap1), (43.5, s_gap2), (47.2, s_ask), (END_START, s_end)]
HOOK_END = 3.2

# ---------------- captions ----------------
groups, cur = [], []
for i, w in enumerate(WORDS):
    cur.append(w); nxt = WORDS[i + 1] if i + 1 < len(WORDS) else None
    endp = w["text"][-1] in ".,;:?!…"; gap = (nxt["start"] - w["end"]) if nxt else 9
    if len(cur) >= 3 or endp or gap > 0.25 or len(" ".join(x["text"] for x in cur)) > 15:
        groups.append(cur); cur = []
if cur: groups.append(cur)
for gi, g in enumerate(groups):
    nxt0 = groups[gi + 1][0]["start"] if gi + 1 < len(groups) else TOTAL
    for w in g: w["gs"], w["ge"] = g[0]["start"], min(nxt0, g[-1]["end"] + 0.5)
EMPH = {"CLEOPATRA", "PIRÁMIDE", "GUIZA", "2560", "CRISTO", "2500", "2100", "ANTIQUÍSIMAS", "RARO", "MAMUTS", "VIVOS", "ÁRTICO", "4000",
        "OXFORD", "200", "AZTECAS", "TENOCHTITLAN", "LOCO", "TIRANOSAURIO", "ESTEGOSAURIO", "80", "66", "SORPRENDIÓ", "TI", "TÚ"}
def clean(s): return s.replace("…", "").replace("¿", "").rstrip(".,;:?!…").upper()

CAP_Y, CAP_SIZE = 1400, 86
def captions(ctx, t):
    if t < HOOK_END: return  # el gancho ya está escrito en pantalla
    g = next((g for g in groups if g[0]["gs"] <= t < g[0]["ge"]), None)
    if not g: return
    toks = [clean(w["text"]) for w in g]; sp = text_w(ctx, " ", CAP_SIZE); ws = [text_w(ctx, s, CAP_SIZE) for s in toks]
    lines, ln, lw = [], [], 0
    for i, w in enumerate(ws):
        if ln and lw + sp + w > 920: lines.append(ln); ln, lw = [], 0
        lw += (sp if ln else 0) + w; ln.append(i)
    lines.append(ln)
    age = t - g[0]["gs"]; pop = 0.82 + 0.18 * back(age / 0.16)
    ctx.save(); ctx.translate(W / 2, CAP_Y); ctx.scale(pop, pop); ctx.translate(-W / 2, -CAP_Y)
    y = CAP_Y - (len(lines) - 1) * 52
    for ln in lines:
        tot = sum(ws[i] for i in ln) + sp * (len(ln) - 1); x = (W - tot) / 2
        for i in ln:
            w = g[i]; end_i = g[i + 1]["start"] if i + 1 < len(g) else w["ge"]
            active = w["start"] <= t < end_i
            col = ACCENT if (active or (toks[i] in EMPH and t >= w["start"])) else WHITE
            text(ctx, toks[i], x, y, CAP_SIZE, col, stroke=14, align="left")
            x += ws[i] + sp
        y += 104
    ctx.restore()

def tag(ctx):
    s = 58; w1 = text_w(ctx, "Logi", 38); w2 = text_w(ctx, "Datos", 38); tot = s + 14 + w1 + w2; x0 = (W - tot) / 2
    logo_mark(ctx, x0, 96, s)
    text(ctx, "Logi", x0 + s + 14, 125, 38, WHITE, stroke=6, align="left"); text(ctx, "Datos", x0 + s + 14 + w1, 125, 38, ACCENT, stroke=6, align="left")

# ---------------- frame ----------------
XF = 0.3
def draw_scene(idx, t):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); ctx = cairo.Context(surf); SCENES[idx][1](ctx, t); return surf

def frame(t):
    idx = max(i for i, (s0, _) in enumerate(SCENES) if s0 <= t)
    surf = draw_scene(idx, t); ctx = cairo.Context(surf)
    if idx > 0 and t - SCENES[idx][0] < XF:
        prev = draw_scene(idx - 1, t); a = 1 - (t - SCENES[idx][0]) / XF
        ctx.set_source_surface(prev); ctx.paint_with_alpha(ease(a))
    if t < END_START:
        sh = cairo.LinearGradient(0, 1250, 0, 1600); sh.add_color_stop_rgba(0, 0, 0, 0, 0); sh.add_color_stop_rgba(0.5, 0, 0, 0, 0.35); sh.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(sh); ctx.rectangle(0, 1250, W, 350); ctx.fill()
        tag(ctx); captions(ctx, t)
    return surf

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        for tt in map(float, sys.argv[2:]):
            frame(tt).write_to_png(os.path.join(OUT, f"p_{tt:05.2f}.png"))
        sys.exit(0)
    bounds = [s0 for s0, _ in SCENES] + [TOTAL]; parts = []
    for k in range(len(SCENES)):
        f0, f1 = round(bounds[k] * FPS), round(bounds[k + 1] * FPS)
        tmp = os.path.join(OUT, f"sc{k:02d}.tmp.mp4"); fin = os.path.join(OUT, f"sc{k:02d}.mp4")
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        for f in range(f0, f1):
            s = frame(f / FPS); s.flush(); p.stdin.write(bytes(s.get_data()))
        p.stdin.close()
        if p.wait() != 0: sys.exit("ffmpeg failed")
        os.replace(tmp, fin); parts.append(fin)
    lst = os.path.join(OUT, "list.txt"); open(lst, "w").write("".join(f"file '{x}'\n" for x in parts))
    silent = os.path.join(OUT, "silent.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    print("OK", silent)
