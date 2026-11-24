#!/usr/bin/env python3
"""LogiDatos Short #5 – La banana es una baya (y la fresa no). Motion graphics drawn in code (cairo).
python3 video_05_banana_fresa.py [preview t1 t2 ...]
Render -> build/silent.mp4; luego: musica.py mix build/silent.mp4 dl/voz.mp3 build/musica.wav <FINAL> --total TOTAL"""
import json, math, os, random, subprocess, sys
import cairo

W, H, FPS = 1080, 1920, 30
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "build"); os.makedirs(OUT, exist_ok=True)
WORDS = [w for w in json.load(open(os.path.join(BASE, "dl/words.json")))["words"] if w.get("type", "word") == "word"]
TOTAL = 54.5

def hexc(h, a=1.0):
    h = h.lstrip("#"); return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)
ACCENT = hexc("FFD23F"); NAVY = hexc("0B1020"); WHITE = hexc("F5F3EA")
BAN = hexc("FFE066"); BAN_D = hexc("E0A21C"); BAN_L = hexc("FFF4B8"); BROWN = hexc("5A3A1A")
STR = hexc("E8253A"); STR_D = hexc("9E1224"); STR_L = hexc("FF6B7A"); LEAF = hexc("3FB54A"); LEAF_D = hexc("1F7A30")
BLUE = hexc("3DA9FC"); RED = hexc("E0393E"); GREEN = hexc("37E08F"); PURPLE = hexc("7B3FA8")
FONT = "Montserrat"

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def back(x):
    x = clamp(x); c = 1.70158; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, u): return a + (b - a) * u

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
    w1 = text_w(ctx, s1 + " ", size) if s1 else 0; w2 = text_w(ctx, s2, size); x0 = (W - w1 - w2) / 2
    if s1: text(ctx, s1, x0, y, size, WHITE, stroke=10, align="left", alpha=a)
    text(ctx, s2, x0 + w1, y, size, c2, stroke=10, align="left", alpha=a)
    ctx.restore()

def check(ctx, x, y, s, alpha=1.0, color=GREEN):
    if alpha <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.arc(0, 0, 1, 0, 2 * math.pi); rgba(ctx, color, alpha); ctx.fill()
    ctx.set_line_width(0.22); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(-0.45, 0.02); ctx.line_to(-0.12, 0.36); ctx.line_to(0.5, -0.32); ctx.set_source_rgba(1, 1, 1, alpha); ctx.stroke()
    ctx.restore()

def cross(ctx, x, y, s, alpha=1.0, color=RED, disc=True):
    if alpha <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    if disc: ctx.arc(0, 0, 1, 0, 2 * math.pi); rgba(ctx, color, alpha); ctx.fill()
    ctx.set_line_width(0.24 if disc else 0.3); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    k = 0.42 if disc else 1.0
    ctx.move_to(-k, -k); ctx.line_to(k, k); ctx.move_to(k, -k); ctx.line_to(-k, k)
    if disc: ctx.set_source_rgba(1, 1, 1, alpha)
    else: rgba(ctx, color, alpha)
    ctx.stroke(); ctx.restore()

def counter_box(ctx, x, y, n, unit, alpha=1.0, color=ACCENT, size=140, sub=46):
    if alpha <= 0: return
    s = str(n); wn = text_w(ctx, s, size); wu = text_w(ctx, " " + unit, sub); tot = wn + wu
    rrect(ctx, x - tot / 2 - 40, y - size * 0.62, tot + 80, size * 1.24, 36); ctx.set_source_rgba(0.03, 0.03, 0.09, 0.8 * alpha); ctx.fill()
    text(ctx, s, x - tot / 2, y, size, color, align="left", alpha=alpha)
    text(ctx, " " + unit, x - tot / 2 + wn, y + size * 0.18, sub, WHITE, align="left", alpha=alpha)

# ---------------- background ----------------
random.seed(5)
BUBBLES = [(random.random(), random.random(), random.uniform(30, 120), random.random()) for _ in range(26)]

def bg(ctx, t, tint=None):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, 0.10, 0.06, 0.16); g.add_color_stop_rgb(0.5, 0.06, 0.05, 0.12); g.add_color_stop_rgb(1, 0.02, 0.02, 0.06)
    ctx.set_source(g); ctx.paint()
    glow(ctx, 200 + 50 * math.sin(t * 0.3), 560, 650, hexc("FFB020"), 0.13)
    glow(ctx, 900, 1150 + 40 * math.sin(t * 0.2), 700, hexc("E8253A"), 0.12)
    for (x, y, r, ph) in BUBBLES:
        yy = (y * H - t * (8 + 14 * ph)) % H; a = 0.035 + 0.03 * math.sin(t + ph * 9)
        ctx.set_source_rgba(1, 0.95, 0.8, a); ctx.arc(x * W, yy, r, 0, 2 * math.pi); ctx.fill()
    if tint: ctx.set_source_rgba(tint[0], tint[1], tint[2], tint[3]); ctx.paint()

# ---------------- fruits ----------------
def banana_path(ctx):
    ctx.new_path(); ctx.move_to(-1.0, -0.12)
    ctx.curve_to(-0.6, 0.78, 0.62, 0.78, 1.0, -0.12)
    ctx.curve_to(0.9, -0.02, 0.8, 0.05, 0.72, 0.06)
    ctx.curve_to(0.4, 0.42, -0.4, 0.42, -0.72, 0.06)
    ctx.curve_to(-0.8, 0.05, -0.9, -0.02, -1.0, -0.12); ctx.close_path()

def banana(ctx, x, y, s, rot=0.0, alpha=1.0, spots=0.0, rot_brown=0.0, seed=1):
    """Banana centred at x,y, width 2s. spots 0..1 = fungus blotches, rot_brown 0..1 = turns brown."""
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s * 1.35); ctx.translate(0, -0.3)
    # stem
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_width(0.09)
    c0 = (lerp(0.45, 0.30, rot_brown), lerp(0.55, 0.22, rot_brown), lerp(0.2, 0.1, rot_brown))
    ctx.set_source_rgba(c0[0], c0[1], c0[2], alpha); ctx.move_to(0.93, -0.06); ctx.curve_to(1.02, -0.2, 1.08, -0.3, 1.14, -0.34); ctx.stroke()
    banana_path(ctx)
    g = cairo.LinearGradient(0, -0.1, 0, 0.6)
    top = [lerp(BAN_L[i], 0.55, rot_brown) for i in range(3)]; mid = [lerp(BAN[i], (0.42, 0.28, 0.12)[i], rot_brown) for i in range(3)]
    bot = [lerp(BAN_D[i], (0.25, 0.15, 0.06)[i], rot_brown) for i in range(3)]
    g.add_color_stop_rgba(0, top[0], top[1], top[2], alpha); g.add_color_stop_rgba(0.45, mid[0], mid[1], mid[2], alpha)
    g.add_color_stop_rgba(1, bot[0], bot[1], bot[2], alpha)
    ctx.set_source(g); ctx.fill_preserve()
    ctx.save(); ctx.clip()
    ctx.set_source_rgba(1, 1, 1, 0.25 * alpha); ctx.set_line_width(0.05)
    ctx.move_to(-0.75, 0.14); ctx.curve_to(-0.35, 0.56, 0.35, 0.56, 0.75, 0.14); ctx.stroke()
    if spots > 0:
        rnd = random.Random(seed)
        for k in range(16):
            px = rnd.uniform(-0.8, 0.8); py = 0.32 * (1 - (px / 0.95) ** 2) + rnd.uniform(-0.06, 0.12)
            rr = rnd.uniform(0.04, 0.11) * clamp(spots * 1.6 - k / 16)
            if rr > 0:
                ctx.set_source_rgba(0.28, 0.17, 0.06, 0.9 * alpha); ctx.arc(px, py, rr, 0, 2 * math.pi); ctx.fill()
    ctx.restore()
    banana_path(ctx); ctx.set_source_rgba(0.35, 0.22, 0.05, 0.55 * alpha); ctx.set_line_width(0.035); ctx.stroke()
    ctx.set_source_rgba(0.22, 0.14, 0.05, alpha); ctx.arc(-0.99, -0.11, 0.05, 0, 2 * math.pi); ctx.fill()
    ctx.restore()

def straw_path(ctx):
    ctx.new_path(); ctx.move_to(0, 1.0)
    ctx.curve_to(-0.95, 0.5, -1.05, -0.62, -0.45, -0.78)
    ctx.curve_to(-0.2, -0.86, 0.2, -0.86, 0.45, -0.78)
    ctx.curve_to(1.05, -0.62, 0.95, 0.5, 0, 1.0); ctx.close_path()

# achene positions in unit coords (hex grid inside the strawberry)
_tmp = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4)); straw_path(_tmp)
ACH = []
_r = 0
yy = -0.6
while yy < 0.92:
    xx = -1.0 + (0.065 if _r % 2 else 0)
    while xx < 1.0:
        if _tmp.in_fill(xx, yy) and _tmp.in_fill(xx * 1.12, yy * 1.06 + 0.02): ACH.append((xx, yy))
        xx += 0.13
    yy += 0.112; _r += 1
random.seed(9); ACH_ORDER = ACH[:]; random.shuffle(ACH_ORDER)

def strawberry(ctx, x, y, s, alpha=1.0, n_ach=None, pulse=0.0, rot=0.0, bite=0.0):
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s)
    if bite > 0: ctx.push_group()
    straw_path(ctx)
    g = cairo.RadialGradient(-0.35, -0.35, 0.05, 0, 0.1, 1.2)
    g.add_color_stop_rgba(0, STR_L[0], STR_L[1], STR_L[2], alpha); g.add_color_stop_rgba(0.5, STR[0], STR[1], STR[2], alpha)
    g.add_color_stop_rgba(1, STR_D[0], STR_D[1], STR_D[2], alpha); ctx.set_source(g); ctx.fill()
    pts = ACH_ORDER if n_ach is None else ACH_ORDER[:max(0, int(n_ach))]
    k = 1 + 0.5 * pulse
    for (ax, ay) in pts:
        ctx.save(); ctx.translate(ax, ay); ctx.scale(0.028 * k, 0.042 * k)
        ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.set_source_rgba(1, 0.86, 0.35, alpha); ctx.fill(); ctx.restore()
        ctx.set_source_rgba(0.55, 0.05, 0.1, 0.35 * alpha); ctx.arc(ax + 0.015, ay + 0.03, 0.02, 0, math.pi); ctx.fill()
    # leaves
    for i in range(7):
        a = math.pi * (i / 6) + math.pi
        ctx.save(); ctx.translate(0, -0.78); ctx.rotate(a + math.pi / 2)
        ctx.new_path(); ctx.move_to(-0.09, 0); ctx.curve_to(-0.12, 0.25, -0.03, 0.42, 0, 0.48); ctx.curve_to(0.03, 0.42, 0.12, 0.25, 0.09, 0)
        ctx.close_path(); ctx.set_source_rgba(LEAF[0], LEAF[1], LEAF[2], alpha); ctx.fill_preserve()
        ctx.set_source_rgba(LEAF_D[0], LEAF_D[1], LEAF_D[2], alpha); ctx.set_line_width(0.02); ctx.stroke(); ctx.restore()
    ctx.set_source_rgba(LEAF_D[0], LEAF_D[1], LEAF_D[2], alpha); ctx.set_line_width(0.07); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(0, -0.85); ctx.curve_to(0.02, -1.0, 0.08, -1.08, 0.14, -1.12); ctx.stroke()
    if bite > 0:
        ctx.set_operator(cairo.OPERATOR_CLEAR)
        for (bx, by, br) in [(0.78, -0.35, 0.22), (0.86, -0.05, 0.22), (0.8, 0.25, 0.2), (0.7, -0.6, 0.18)]:
            ctx.arc(bx + (1 - bite) * 0.5, by, br * bite, 0, 2 * math.pi); ctx.fill()
        ctx.set_operator(cairo.OPERATOR_OVER); ctx.pop_group_to_source(); ctx.paint()
    ctx.restore()

def tomato(ctx, x, y, s, alpha=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s * 0.88)
    g = cairo.RadialGradient(-0.35, -0.35, 0.05, 0, 0, 1.05)
    g.add_color_stop_rgba(0, 1, 0.5, 0.4, alpha); g.add_color_stop_rgba(0.6, 0.9, 0.15, 0.1, alpha); g.add_color_stop_rgba(1, 0.6, 0.05, 0.05, alpha)
    ctx.set_source(g); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.fill(); ctx.restore()
    ctx.save(); ctx.translate(x, y - s * 0.82)
    for i in range(5):
        ctx.save(); ctx.rotate(i * 2 * math.pi / 5); ctx.new_path(); ctx.move_to(-s * 0.07, 0); ctx.line_to(0, s * 0.38); ctx.line_to(s * 0.07, 0); ctx.close_path()
        ctx.set_source_rgba(LEAF[0], LEAF[1], LEAF[2], alpha); ctx.fill(); ctx.restore()
    ctx.restore()

def grapes(ctx, x, y, s, alpha=1.0):
    pos = [(-0.5, -0.5), (0, -0.55), (0.5, -0.5), (-0.27, -0.05), (0.27, -0.05), (-0.5, 0.05), (0.5, 0.05), (0, 0.38), (-0.25, 0.75), (0.25, 0.4), (0.03, 0.85)]
    ctx.set_source_rgba(LEAF_D[0], LEAF_D[1], LEAF_D[2], alpha); ctx.set_line_width(s * 0.08); ctx.move_to(x, y - s * 0.75); ctx.line_to(x + s * 0.1, y - s * 1.05); ctx.stroke()
    for (px, py) in pos:
        cx, cy, r = x + px * s, y + py * s * 0.9, s * 0.3
        g = cairo.RadialGradient(cx - r * 0.35, cy - r * 0.35, r * 0.05, cx, cy, r)
        g.add_color_stop_rgba(0, 0.75, 0.55, 0.95, alpha); g.add_color_stop_rgba(1, 0.32, 0.12, 0.5, alpha)
        ctx.set_source(g); ctx.arc(cx, cy, r, 0, 2 * math.pi); ctx.fill()

def kiwi(ctx, x, y, s, alpha=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.set_source_rgba(0.45, 0.32, 0.16, alpha); ctx.fill()
    g = cairo.RadialGradient(0, 0, 0.1, 0, 0, 0.9); g.add_color_stop_rgba(0, 0.85, 0.95, 0.6, alpha); g.add_color_stop_rgba(1, 0.38, 0.72, 0.2, alpha)
    ctx.set_source(g); ctx.arc(0, 0, 0.9, 0, 2 * math.pi); ctx.fill()
    ctx.set_source_rgba(0.98, 1, 0.9, alpha); ctx.save(); ctx.scale(1, 0.75); ctx.arc(0, 0, 0.25, 0, 2 * math.pi); ctx.restore(); ctx.fill()
    for i in range(22):
        a = i * 2 * math.pi / 22; r = 0.4 + 0.05 * (i % 2)
        ctx.save(); ctx.translate(r * math.cos(a), r * math.sin(a)); ctx.rotate(a); ctx.scale(0.07, 0.035)
        ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.set_source_rgba(0.08, 0.06, 0.04, alpha); ctx.fill(); ctx.restore()
    ctx.restore()

def eggplant(ctx, x, y, s, alpha=1.0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(-0.5); ctx.scale(s, s)
    ctx.new_path(); ctx.move_to(0, -0.75); ctx.curve_to(0.45, -0.7, 0.35, 0.0, 0.62, 0.55)
    ctx.curve_to(0.8, 1.05, -0.8, 1.05, -0.62, 0.55); ctx.curve_to(-0.35, 0.0, -0.45, -0.7, 0, -0.75); ctx.close_path()
    g = cairo.LinearGradient(-0.6, 0, 0.6, 0); g.add_color_stop_rgba(0, 0.5, 0.25, 0.7, alpha); g.add_color_stop_rgba(1, 0.22, 0.06, 0.32, alpha)
    ctx.set_source(g); ctx.fill()
    ctx.new_path(); ctx.move_to(-0.32, -0.55); ctx.curve_to(-0.2, -0.85, 0.2, -0.85, 0.32, -0.55); ctx.line_to(0.15, -0.62); ctx.line_to(0, -0.5); ctx.line_to(-0.15, -0.62); ctx.close_path()
    ctx.set_source_rgba(LEAF[0], LEAF[1], LEAF[2], alpha); ctx.fill()
    ctx.set_source_rgba(LEAF_D[0], LEAF_D[1], LEAF_D[2], alpha); ctx.set_line_width(0.1); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.move_to(0, -0.78); ctx.line_to(0.05, -1.05); ctx.stroke()
    ctx.restore()

def flower(ctx, x, y, s, t, many=False, alpha=1.0, ov=1.0, petal=(1, 0.97, 0.98)):
    """Top view flower; ov 0..1 highlights the ovary."""
    ctx.save(); ctx.translate(x, y); ctx.rotate(t * 0.15)
    for i in range(5):
        ctx.save(); ctx.rotate(i * 2 * math.pi / 5); ctx.translate(0, -s * 0.6); ctx.scale(s * 0.42, s * 0.55)
        ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.set_source_rgba(petal[0], petal[1], petal[2], alpha); ctx.fill_preserve()
        ctx.set_source_rgba(0.85, 0.75, 0.8, alpha); ctx.set_line_width(0.04); ctx.stroke(); ctx.restore()
    ctx.restore()
    glow(ctx, x, y, s * 0.6, ACCENT, 0.4 * alpha * ov)
    ctx.arc(x, y, s * 0.36, 0, 2 * math.pi); ctx.set_source_rgba(1, 0.82, 0.2, alpha); ctx.fill()
    for i in range(14):
        a = i * 2 * math.pi / 14; ctx.arc(x + s * 0.3 * math.cos(a), y + s * 0.3 * math.sin(a), s * 0.035, 0, 2 * math.pi)
        ctx.set_source_rgba(0.85, 0.55, 0.05, alpha); ctx.fill()
    if not many:
        ctx.arc(x, y, s * 0.16, 0, 2 * math.pi); ctx.set_source_rgba(0.35, 0.78, 0.3, alpha); ctx.fill()
    else:
        rnd = random.Random(3)
        for i in range(30):
            r = s * 0.2 * math.sqrt(rnd.random()); a = rnd.uniform(0, 2 * math.pi)
            ctx.arc(x + r * math.cos(a), y + r * math.sin(a), s * 0.035, 0, 2 * math.pi); ctx.set_source_rgba(0.35, 0.78, 0.3, alpha); ctx.fill()

def banana_slice(ctx, x, y, s, alpha=1.0, seeds=1.0):
    ctx.arc(x, y, s, 0, 2 * math.pi); ctx.set_source_rgba(0.95, 0.85, 0.3, alpha); ctx.fill()
    ctx.arc(x, y, s * 0.9, 0, 2 * math.pi); ctx.set_source_rgba(1, 0.96, 0.82, alpha); ctx.fill()
    ctx.save(); ctx.translate(x, y)
    for i in range(3):
        ctx.save(); ctx.rotate(i * 2 * math.pi / 3 - math.pi / 2); ctx.translate(0, -s * 0.2); ctx.scale(s * 0.1, s * 0.22)
        ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.set_source_rgba(0.95, 0.88, 0.62, alpha); ctx.fill(); ctx.restore()
    for i in range(9):
        a = i * 2 * math.pi / 9; r = s * 0.25 + s * 0.04 * (i % 2)
        ctx.arc(r * math.cos(a), r * math.sin(a), s * 0.045 * seeds, 0, 2 * math.pi); ctx.set_source_rgba(0.15, 0.1, 0.06, alpha); ctx.fill()
    ctx.restore()

def achene_big(ctx, x, y, s, alpha=1.0, seed_a=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.new_path(); ctx.move_to(0, -1); ctx.curve_to(0.75, -0.6, 0.7, 0.75, 0, 1); ctx.curve_to(-0.7, 0.75, -0.75, -0.6, 0, -1); ctx.close_path()
    g = cairo.RadialGradient(-0.25, -0.3, 0.05, 0, 0, 1.0); g.add_color_stop_rgba(0, 1, 0.95, 0.6, alpha); g.add_color_stop_rgba(1, 0.92, 0.7, 0.15, alpha)
    ctx.set_source(g); ctx.fill_preserve(); ctx.set_source_rgba(0.6, 0.4, 0.05, alpha); ctx.set_line_width(0.05); ctx.stroke()
    if seed_a > 0:
        ctx.save(); ctx.scale(0.28, 0.5); ctx.arc(0, 0.1, 1, 0, 2 * math.pi); ctx.restore()
        ctx.set_source_rgba(0.45, 0.25, 0.08, alpha * seed_a); ctx.fill()
    ctx.restore()

def dna(ctx, x, y, w, h, t, alpha=1.0, color=GREEN):
    ctx.set_line_width(4); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(9):
        yy = y - h / 2 + h * k / 8; ph = t * 3 + k * 0.8
        x1 = x + w / 2 * math.sin(ph); x2 = x - w / 2 * math.sin(ph)
        ctx.set_source_rgba(1, 1, 1, 0.5 * alpha); ctx.move_to(x1, yy); ctx.line_to(x2, yy); ctx.stroke()
        rgba(ctx, color, alpha); ctx.arc(x1, yy, 6, 0, 2 * math.pi); ctx.fill()
        ctx.set_source_rgba(1, 0.6, 0.3, alpha); ctx.arc(x2, yy, 6, 0, 2 * math.pi); ctx.fill()

def warning(ctx, x, y, s, alpha=1.0):
    if alpha <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.new_path(); ctx.move_to(0, -1); ctx.line_to(1.05, 0.8); ctx.line_to(-1.05, 0.8); ctx.close_path()
    ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_width(0.16); rgba(ctx, RED, alpha); ctx.stroke_preserve(); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, alpha); rrect(ctx, -0.08, -0.45, 0.16, 0.75, 0.08); ctx.fill(); ctx.arc(0, 0.52, 0.1, 0, 2 * math.pi); ctx.fill()
    ctx.restore()

def bubble(ctx, x, y, s, alpha=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rrect(ctx, -1, -0.75, 2, 1.4, 0.4); ctx.move_to(-0.5, 0.6); ctx.line_to(-0.7, 1.0); ctx.line_to(-0.1, 0.6); ctx.close_path()
    rgba(ctx, ACCENT, alpha); ctx.fill()
    for i in (-0.45, 0, 0.45): ctx.arc(i, -0.05, 0.13, 0, 2 * math.pi); rgba(ctx, NAVY, alpha); ctx.fill()
    ctx.restore()

# ---------------- scenes ----------------
def s_hook(ctx, t):  # 0–3.3  (text + motion visible from frame 0)
    bg(ctx, t)
    bob = math.sin(t * 4) * 14
    banana(ctx, 320, 800 + bob, 225, rot=-0.2 + 0.06 * math.sin(t * 3))
    strawberry(ctx, 780, 780 - bob, 195, rot=0.12 * math.sin(t * 2.5))
    # hook text (no fade-in)
    text(ctx, "La BANANA", W / 2, 330, 104, ACCENT, stroke=14)
    text(ctx, "es una BAYA", W / 2, 460, 104, WHITE, stroke=14)
    check(ctx, 320, 1060, 72 * back((t - 1.1) / 0.35))
    xa = back((t - 2.0) / 0.35)
    cross(ctx, 780, 1060, 72 * xa)
    if t > 1.85:
        a = ease((t - 1.85) / 0.25)
        label(ctx, "LA FRESA, NO", W / 2, 1200, 68, RED, a)

def s_def(ctx, t):  # 3.3–9.0
    bg(ctx, t)
    header(ctx, "¿Qué es una", "BAYA?", t, 3.35)
    fa = back((t - 4.9) / 0.4); fade = 1 - ease((t - 7.3) / 0.4)
    if fa > 0 and fade > 0:
        flower(ctx, W / 2, 760, 230 * fa, t, alpha=fade, ov=0.5 + 0.5 * math.sin(t * 5))
        if t > 6.2:
            la = ease((t - 6.2) / 0.3) * fade
            ctx.set_source_rgba(1, 1, 1, la); ctx.set_line_width(5); ctx.move_to(W / 2 + 40, 760); ctx.line_to(W / 2 + 250, 1000); ctx.stroke()
            label(ctx, "1 FLOR · 1 OVARIO", W / 2, 1060, 54, ACCENT, la)
    if t > 7.3:
        u = back((t - 7.3) / 0.45)
        banana_slice(ctx, W / 2, 760, 250 * u, seeds=ease((t - 7.8) / 0.4) * (1 + 0.3 * math.sin(t * 8)))
        label(ctx, "SEMILLAS ADENTRO", W / 2, 1100, 56, ACCENT, ease((t - 7.8) / 0.3))
    if t < 4.9:
        a = ease((t - 3.4) / 0.3)
        text(ctx, "Botánica", W / 2, 720, 90, WHITE, stroke=10, alpha=a)
        banana(ctx, W / 2, 900, 150, alpha=a, rot=0.1 * math.sin(t * 3))

def s_members(ctx, t):  # 9.0–13.9
    bg(ctx, t)
    ba = ease((t - 9.0) / 0.3)
    shrink = ease((t - 10.2) / 0.4)
    bx, by, bs = W / 2, lerp(760, 520, shrink), lerp(260, 150, shrink)
    banana(ctx, bx, by, bs, rot=-0.15 + 0.05 * math.sin(t * 3), alpha=ba)
    check(ctx, bx + bs * 0.95, by - bs * 0.55, 62 * back((t - 9.6) / 0.35))
    if t < 10.3: label(ctx, "LA BANANA CUMPLE", W / 2, 1050, 58, GREEN, ease((t - 9.6) / 0.3))
    items = [(10.8, tomato, 280, 780, 100, "TOMATE"), (11.68, grapes, 800, 790, 90, "UVA"),
             (12.32, kiwi, 280, 1070, 95, "KIWI"), (13.04, eggplant, 800, 1050, 120, "BERENJENA")]
    for (t0, fn, x, y, s, name) in items:
        a = back((t - t0) / 0.4)
        if a <= 0: continue
        fn(ctx, x, y, s * a)
        label(ctx, name, x, y + 150, 40, WHITE, clamp(a))
    header(ctx, "También son", "BAYAS", t, 10.3)

def s_strawflower(ctx, t):  # 13.9–16.8
    bg(ctx, t)
    header(ctx, "La fresa:", "MUCHOS ovarios", t, 13.95, size=62)
    a = back((t - 14.2) / 0.45)
    flower(ctx, W / 2, 740, 240 * a, t, many=True, ov=0.6 + 0.4 * math.sin(t * 6))
    if t > 15.5:
        la = ease((t - 15.5) / 0.3)
        label(ctx, "MUCHOS OVARIOS", W / 2, 1080, 56, ACCENT, la)
    if t > 16.2:
        cross(ctx, W / 2 + 330, 520, 60 * back((t - 16.2) / 0.3))

def s_dots(ctx, t):  # 16.8–22.7
    bg(ctx, t)
    zoom = ease((t - 16.8) / 0.5)
    sx, sy, ss = W / 2 - 60, 780, lerp(230, 300, zoom)
    pulse = (0.5 + 0.5 * math.sin(t * 10)) if 17.1 < t < 18.2 else 0
    strawberry(ctx, sx, sy, ss, pulse=pulse)
    if t < 19.35:
        header(ctx, "Esos puntitos NO son", "SEMILLAS", t, 16.85, size=58)
        if t > 18.6:
            label(ctx, "SEMILLA", W / 2, 1130, 56, WHITE, ease((t - 18.6) / 0.2))
            cross(ctx, W / 2 + 190, 1130, 40 * back((t - 18.8) / 0.3), disc=False)
    # magnifier on one achene
    if t > 19.4:
        m = back((t - 19.4) / 0.45)
        ax, ay = ACH[len(ACH) // 2 + 3]; px, py = sx + ax * ss, sy + ay * ss
        mx, my, mr = 790, 700, 210 * m
        ctx.set_source_rgba(1, 1, 1, 0.8); ctx.set_line_width(4); ctx.move_to(px, py); ctx.line_to(mx - mr * 0.7, my + mr * 0.7); ctx.stroke()
        ctx.arc(px, py, 16, 0, 2 * math.pi); ctx.stroke()
        ctx.arc(mx, my, mr, 0, 2 * math.pi); ctx.set_source_rgba(0.75, 0.08, 0.15, 1); ctx.fill_preserve()
        ctx.set_source_rgba(1, 1, 1, 0.95); ctx.set_line_width(12); ctx.stroke()
        achene_big(ctx, mx, my, 120 * m, seed_a=ease((t - 21.55) / 0.3))
        header(ctx, "Cada uno es un", "FRUTO", t, 19.4, size=64)
        if t > 20.2: label(ctx, "FRUTO", mx, my + mr + 60, 50, ACCENT, ease((t - 20.2) / 0.3))
        if t > 21.6:
            sa = ease((t - 21.6) / 0.3)
            label(ctx, "+ SU SEMILLA", mx, my + mr + 140, 46, WHITE, sa)

def s_count(ctx, t):  # 22.7–28.6
    bg(ctx, t)
    sx, sy, ss = W / 2, 760, 300
    p = ease((t - 23.3) / 1.9)
    bite = ease((t - 26.2) / 0.3)
    strawberry(ctx, sx, sy, ss, n_ach=len(ACH) * p, bite=bite)
    if t < 25.9:
        header(ctx, "Una fresa mediana:", "", t, 22.75, size=62)
        counter_box(ctx, W / 2, 1150, int(round(200 * p)), "frutos", ease((t - 23.0) / 0.3))
    else:
        header(ctx, "Cada mordida =", "CIENTOS de frutos", t, 25.9, size=58)
        if t > 27.4:
            k = back((t - 27.4) / 0.35)
            ctx.save(); ctx.translate(W / 2, 1150); ctx.scale(k, k); text(ctx, "200+", 0, 0, 150, ACCENT, stroke=14); ctx.restore()

CLONE_POS = [(W / 2 + (c - 1) * 315, 600 + r * 250) for r in range(3) for c in range(3)]
def s_clone(ctx, t):  # 28.6–33.4
    bg(ctx, t)
    if t < 32.45:
        a = ease((t - 28.7) / 0.3)
        banana(ctx, W / 2, 760, 260, rot=-0.15 + 0.05 * math.sin(t * 2), alpha=a)
        q = back((t - 29.9) / 0.4)
        if q > 0:
            ctx.save(); ctx.translate(W / 2 + 250, 520); ctx.scale(q, q); ctx.rotate(0.1 * math.sin(t * 3)); text(ctx, "?", 0, 0, 220, ACCENT, stroke=14); ctx.restore()
        header(ctx, "Algo más", "RARO...", t, 30.0)
        if t > 31.6: label(ctx, "LAS DEL SÚPER", W / 2, 1100, 56, WHITE, ease((t - 31.6) / 0.25))
    else:
        for i, (x, y) in enumerate(CLONE_POS):
            k = back((t - 32.5 - i * 0.07) / 0.35)
            banana(ctx, x, y, 120 * k, rot=-0.15 + 0.05 * math.sin(t * 2))
        k = back((t - 32.5) / 0.35)
        ctx.save(); ctx.translate(W / 2, 310); ctx.scale(k, k); text(ctx, "CLONES", 0, 0, 130, ACCENT, stroke=14); ctx.restore()

def s_dna(ctx, t):  # 33.4–38.2
    danger = ease((t - 37.4) / 0.3)
    bg(ctx, t, tint=(0.6, 0.0, 0.05, 0.22 * danger * (0.7 + 0.3 * math.sin(t * 12))))
    for i, (x, y) in enumerate(CLONE_POS):
        banana(ctx, x, y - 40, 120, rot=-0.15 + 0.05 * math.sin(t * 2))
        da = ease((t - 34.7 - i * 0.05) / 0.3)
        if da > 0: dna(ctx, x, y + 70, 60, 70, t, da)
    if t < 37.4:
        if t < 35.6: header(ctx, "Todas las", "CAVENDISH", t, 33.45)
        else:
            k = back((t - 35.6) / 0.35)
            ctx.save(); ctx.translate(W / 2, 300); ctx.scale(k, k); text(ctx, "100 % IDÉNTICAS", 0, 0, 84, GREEN, stroke=12); ctx.restore()
    else:
        k = back((t - 37.45) / 0.35)
        ctx.set_source_rgba(0.02, 0.0, 0.03, 0.55 * danger); ctx.paint()
        warning(ctx, W / 2, 870, 170 * k)
        header(ctx, "", "PELIGRO", t, 37.45, size=96, c2=RED)

def s_fungus(ctx, t):  # 38.2–45.2
    bg(ctx, t)
    if t < 40.3: header(ctx, "Años", "50", t, 38.25, size=84)
    else: header(ctx, "Un hongo:", "mal de Panamá", t, 40.3, size=62, c2=RED)
    xs = [230, 540, 850]; ys = [620, 900]
    spread = ease((t - 39.8) / 1.6); kill = ease((t - 41.6) / 1.4)
    i = 0
    for yy in ys:
        for x in xs:
            d = clamp(spread * 1.6 - i * 0.1); kk = clamp(kill * 1.5 - i * 0.08)
            drop = kk * kk * 120
            banana(ctx, x, yy + drop, 125, rot=-0.15 + kk * 0.5, alpha=1 - 0.45 * kk, spots=d, rot_brown=kk, seed=i + 3)
            i += 1
    if t > 39.8:
        # spores
        for k in range(18):
            ph = (t * 0.5 + k / 18) % 1; a = 0.6 * math.sin(ph * math.pi) * ease((t - 39.8) / 0.4)
            ctx.set_source_rgba(0.6, 0.85, 0.4, a); ctx.arc(120 + (k * 137) % 840, 1180 - ph * 700, 6 + 4 * (k % 3), 0, 2 * math.pi); ctx.fill()
    if t > 44.0:
        k = back((t - 44.0) / 0.35)
        ctx.save(); ctx.translate(W / 2, 1150); ctx.scale(k, k); label(ctx, "GROS MICHEL", 0, 0, 64, ACCENT); ctx.restore()
        cross(ctx, W / 2 + 290, 1150, 44 * k)
    elif t > 41.6:
        label(ctx, "CASI LA BORRÓ", W / 2, 1150, 58, RED, ease((t - 41.6) / 0.3))

def s_today(ctx, t):  # 45.2–48.37
    bg(ctx, t, tint=(0.5, 0.0, 0.05, 0.10 * (0.5 + 0.5 * math.sin(t * 6))))
    header(ctx, "", "HOY", t, 45.2, size=110)
    sp = 0.35 * ease((t - 46.1) / 1.6)
    banana(ctx, W / 2, 780, 270, rot=-0.15 + 0.04 * math.sin(t * 2), spots=sp, seed=11)
    if t > 46.1: label(ctx, "NUEVA CEPA", W / 2, 500, 56, RED, ease((t - 46.1) / 0.3))
    warning(ctx, W / 2 + 300, 1020, 70 * back((t - 46.6) / 0.35))
    if t > 47.3: label(ctx, "TU BANANA", W / 2, 1150, 62, ACCENT, ease((t - 47.3) / 0.25))

def s_ask(ctx, t):  # 48.37–49.9
    bg(ctx, t)
    k = back((t - 48.37) / 0.35)
    ctx.save(); ctx.translate(W / 2, 520); ctx.scale(k, k); text(ctx, "¿LO SABÍAS?", 0, 0, 120, ACCENT, stroke=14); ctx.restore()
    banana(ctx, 330, 860, 190 * k, rot=-0.2 + 0.08 * math.sin(t * 4))
    strawberry(ctx, 760, 860, 140 * k, rot=0.1 * math.sin(t * 4))
    bubble(ctx, W / 2, 1100, 80 * back((t - 49.2) / 0.35))

def s_end(ctx, t):  # 49.9–end
    bg(ctx, t)
    a = ease((t - 49.9) / 0.5)
    banana(ctx, 380, 1520, 170, rot=-0.2 + 0.05 * math.sin(t * 2), alpha=a)
    strawberry(ctx, 760, 1500, 130, alpha=a, rot=0.08 * math.sin(t * 2))
    sc = 0.85 + 0.15 * back((t - 49.9) / 0.5); s = 300 * sc
    logo_mark(ctx, (W - s) / 2, 470 + (300 - s) / 2, s, a)
    w1 = text_w(ctx, "Logi", 120); w2 = text_w(ctx, "Datos", 120); x0 = (W - w1 - w2) / 2
    text(ctx, "Logi", x0, 900, 120, WHITE, align="left", alpha=a); text(ctx, "Datos", x0 + w1, 900, 120, ACCENT, align="left", alpha=a)
    text(ctx, "Curiosidades con lógica y datos", W / 2, 1010, 48, hexc("C8CEE0"), bold=False, alpha=a)
    pa = back((t - 50.3) / 0.4)
    if pa > 0:
        ctx.save(); ctx.translate(W / 2, 1150); ctx.scale(pa, pa)
        pw = text_w(ctx, "SÍGUENOS", 54) + 100; rrect(ctx, -pw / 2, -52, pw, 104, 52); rgba(ctx, ACCENT); ctx.fill()
        text(ctx, "SÍGUENOS", 0, 0, 54, NAVY); ctx.restore()

SCENES = [(0.0, s_hook), (3.3, s_def), (9.0, s_members), (13.9, s_strawflower), (16.8, s_dots), (22.7, s_count),
          (28.6, s_clone), (33.4, s_dna), (38.2, s_fungus), (45.2, s_today), (48.37, s_ask), (49.9, s_end)]
END_START = 49.9

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
EMPH = {"BANANA", "BAYA", "FRESA", "NO", "OVARIO", "OVARIOS", "SEMILLAS", "FRUTO", "DOSCIENTOS", "CIENTOS", "FRUTOS",
        "CLONES", "IDÉNTICAS", "PELIGRO", "HONGO", "PANAMÁ", "BORRÓ", "CEPA", "TÚ", "CAVENDISH"}
def clean(s): return s.replace("…", "").replace("¿", "").rstrip(".,;:?!…").upper()

CAP_Y, CAP_SIZE = 1400, 86
def captions(ctx, t):
    if t < 3.3: return  # el gancho ya está escrito en pantalla
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
