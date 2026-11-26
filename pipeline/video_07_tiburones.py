#!/usr/bin/env python3
"""LogiDatos Short #7 – Los tiburones son más viejos que los árboles. Motion graphics drawn in code (cairo).
python3 video_07_tiburones.py [preview t1 t2 ...]
Render -> build/silent.mp4; luego: musica.py mix build/silent.mp4 dl/voz.mp3 build/musica.wav <FINAL> --total TOTAL"""
import json, math, os, random, subprocess, sys
import cairo

W, H, FPS = 1080, 1920, 30
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "build"); os.makedirs(OUT, exist_ok=True)
WORDS = [w for w in json.load(open(os.path.join(BASE, "dl/words.json")))["words"] if w.get("type", "word") == "word"]
TOTAL = 60.0

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


# ---------------- background (océano) ----------------
random.seed(7)
DOTS = [(random.random(), random.random(), random.uniform(3, 7), random.random()) for _ in range(46)]
TEAL = hexc("2EC4B6"); LEAF = hexc("5CC85A"); LEAF_D = hexc("2E8B3E"); BROWN = hexc("7A4E2D"); SAND = hexc("D9B779")
CART = hexc("7FD8FF"); SKIN = hexc("F2C9A5"); PURPLE = hexc("A06CFF")

def bg(ctx, t, deep=0.0, ice=0.0):
    g = cairo.LinearGradient(0, 0, 0, H)
    c0 = mixc(hexc("0F5A8A"), hexc("06192C"), deep); c1 = mixc(hexc("093553"), hexc("030C18"), deep); c2 = mixc(hexc("04172A"), hexc("01040A"), deep)
    g.add_color_stop_rgb(0, c0[0], c0[1], c0[2]); g.add_color_stop_rgb(0.5, c1[0], c1[1], c1[2]); g.add_color_stop_rgb(1, c2[0], c2[1], c2[2])
    ctx.set_source(g); ctx.paint()
    for k in range(6):
        x0 = 40 + k * 190 + 50 * math.sin(t * 0.35 + k * 1.3)
        ctx.new_path(); ctx.move_to(x0, 0); ctx.line_to(x0 + 70, 0); ctx.line_to(x0 + 240, H); ctx.line_to(x0 + 90, H); ctx.close_path()
        ctx.set_source_rgba(0.6, 0.9, 1, 0.04 * (1 - 0.7 * deep)); ctx.fill()
    glow(ctx, 230 + 60 * math.sin(t * 0.3), 520, 620, TEAL, 0.10 * (1 - 0.5 * deep))
    glow(ctx, 860, 1280 + 50 * math.sin(t * 0.2), 700, BLUE, 0.09)
    ctx.set_line_width(2)
    for (x, y, r, ph) in DOTS:
        yy = (y * H - t * (18 + 30 * ph)) % H; a = 0.10 + 0.08 * math.sin(t * 2 + ph * 9)
        ctx.new_path(); ctx.arc(x * W + 10 * math.sin(t + ph * 6), yy, r, 0, 2 * math.pi); ctx.set_source_rgba(0.8, 0.95, 1, a); ctx.stroke()
    if ice > 0:
        ctx.new_path(); ctx.move_to(0, 0); ctx.line_to(W, 0)
        for i in range(13, -1, -1):
            x = i * W / 13; ctx.line_to(x, ice * (60 + 28 * math.sin(i * 2.7) + 18 * math.sin(i * 5.1)))
        ctx.close_path()
        g2 = cairo.LinearGradient(0, 0, 0, 230); g2.add_color_stop_rgba(0, 0.9, 0.97, 1, 0.95); g2.add_color_stop_rgba(1, 0.55, 0.8, 0.95, 0.85)
        ctx.set_source(g2); ctx.fill()

def sea_floor(ctx, y, t, alpha=1.0):
    ctx.new_path(); ctx.move_to(0, H)
    for x in range(0, W + 30, 30): ctx.line_to(x, y + 18 * math.sin(x / 140) + 8 * math.sin(x / 47))
    ctx.line_to(W, H); ctx.close_path(); ctx.set_source_rgba(0.55, 0.45, 0.28, 0.55 * alpha); ctx.fill()

# ---------------- objects ----------------
def shark(ctx, x, y, s, t, alpha=1.0, flip=False, body=(0.47, 0.58, 0.70), belly=(0.93, 0.95, 0.97), xray=0.0, wag=1.0, sy=1.0, ph=0.0):
    """Tiburón de perfil mirando a la derecha (flip = izquierda). Largo total ≈ 2.1·s."""
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(-s if flip else s, s * sy)
    w = 0.16 * wag * math.sin(t * 6 + ph)
    dk = (body[0] * 0.75, body[1] * 0.75, body[2] * 0.8)
    # cola
    ctx.save(); ctx.translate(-0.72, 0); ctx.rotate(w)
    ctx.new_path(); ctx.move_to(0.06, -0.075); ctx.curve_to(-0.1, -0.2, -0.24, -0.38, -0.38, -0.54); ctx.curve_to(-0.32, -0.3, -0.24, -0.1, -0.15, 0.0)
    ctx.curve_to(-0.23, 0.1, -0.29, 0.22, -0.32, 0.34); ctx.curve_to(-0.16, 0.22, -0.05, 0.12, 0.06, 0.075); ctx.close_path()
    ctx.set_source_rgba(dk[0], dk[1], dk[2], alpha); ctx.fill(); ctx.restore()
    # cuerpo
    ctx.new_path(); ctx.move_to(1.0, 0.03)
    ctx.curve_to(0.92, -0.13, 0.62, -0.2, 0.26, -0.21); ctx.line_to(0.12, -0.2)
    ctx.curve_to(0.05, -0.34, -0.02, -0.48, -0.09, -0.56); ctx.curve_to(-0.11, -0.4, -0.15, -0.27, -0.22, -0.17)
    ctx.curve_to(-0.45, -0.13, -0.64, -0.09, -0.75, -0.075); ctx.line_to(-0.75, 0.075)
    ctx.curve_to(-0.6, 0.1, -0.46, 0.14, -0.36, 0.16); ctx.line_to(-0.43, 0.27); ctx.line_to(-0.26, 0.18)
    ctx.curve_to(0.0, 0.215, 0.2, 0.215, 0.32, 0.2); ctx.curve_to(0.62, 0.18, 0.86, 0.15, 1.0, 0.03); ctx.close_path()
    g = cairo.LinearGradient(0, -0.22, 0, 0.22)
    g.add_color_stop_rgba(0, dk[0], dk[1], dk[2], alpha); g.add_color_stop_rgba(0.45, body[0], body[1], body[2], alpha)
    g.add_color_stop_rgba(0.62, belly[0], belly[1], belly[2], alpha); g.add_color_stop_rgba(1, belly[0], belly[1], belly[2], alpha)
    ctx.set_source(g); ctx.fill()
    # aleta pectoral
    fw = 0.05 * math.sin(t * 3 + ph)
    ctx.new_path(); ctx.move_to(0.4, 0.12); ctx.curve_to(0.32, 0.3, 0.2, 0.42 + fw, 0.08, 0.5 + fw); ctx.curve_to(0.15, 0.33, 0.21, 0.2, 0.23, 0.15); ctx.close_path()
    ctx.set_source_rgba(dk[0], dk[1], dk[2], alpha); ctx.fill()
    # branquias, ojo, boca
    ctx.set_line_width(0.012); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for gx in (0.47, 0.52, 0.57):
        ctx.move_to(gx, -0.07); ctx.curve_to(gx - 0.02, -0.02, gx - 0.02, 0.04, gx - 0.01, 0.09)
    ctx.set_source_rgba(0.1, 0.15, 0.22, 0.6 * alpha); ctx.stroke()
    ctx.arc(0.77, -0.045, 0.03, 0, 2 * math.pi); ctx.set_source_rgba(0.02, 0.03, 0.05, alpha); ctx.fill()
    ctx.arc(0.78, -0.055, 0.009, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, 0.9 * alpha); ctx.fill()
    ctx.move_to(0.88, 0.1); ctx.curve_to(0.8, 0.13, 0.72, 0.13, 0.66, 0.12); ctx.set_line_width(0.014); ctx.set_source_rgba(0.15, 0.1, 0.12, 0.7 * alpha); ctx.stroke()
    if xray > 0:
        # rayos X: oscurece y dibuja el esqueleto de cartílago
        ctx.new_path(); ctx.move_to(1.0, 0.03)
        ctx.curve_to(0.92, -0.13, 0.62, -0.2, 0.26, -0.21); ctx.line_to(0.12, -0.2)
        ctx.curve_to(0.05, -0.34, -0.02, -0.48, -0.09, -0.56); ctx.curve_to(-0.11, -0.4, -0.15, -0.27, -0.22, -0.17)
        ctx.curve_to(-0.45, -0.13, -0.64, -0.09, -0.75, -0.075); ctx.line_to(-0.75, 0.075)
        ctx.curve_to(-0.6, 0.1, -0.46, 0.14, -0.36, 0.16); ctx.curve_to(0.0, 0.215, 0.2, 0.215, 0.32, 0.2); ctx.curve_to(0.62, 0.18, 0.86, 0.15, 1.0, 0.03); ctx.close_path()
        ctx.set_source_rgba(0.02, 0.08, 0.16, 0.85 * xray * alpha); ctx.fill()
        a = xray * alpha; ctx.set_line_width(0.022); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(0.62, -0.03); ctx.curve_to(0.3, -0.04, -0.3, -0.02, -0.74, 0.0); rgba(ctx, CART, a); ctx.stroke()
        for k in range(22):
            vx = 0.58 - k * 0.063; ctx.move_to(vx, -0.07); ctx.line_to(vx, 0.035)
        ctx.set_line_width(0.014); rgba(ctx, CART, 0.8 * a); ctx.stroke()
        ctx.save(); ctx.translate(0.78, 0.0); ctx.scale(0.22, 0.11); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
        ctx.set_line_width(0.02); rgba(ctx, CART, a); ctx.stroke()
        ctx.move_to(0.88, 0.09); ctx.curve_to(0.78, 0.15, 0.66, 0.14, 0.58, 0.08); ctx.stroke()
        for (a0, b0, a1, b1) in [(0.0, -0.08, -0.08, -0.48), (0.35, 0.1, 0.12, 0.44), (-0.32, 0.06, -0.4, 0.22)]:
            for j in range(4):
                ctx.move_to(a0 - j * 0.03, b0); ctx.line_to(a1 - j * 0.03, b1 * (1 - j * 0.12))
        ctx.set_line_width(0.01); rgba(ctx, CART, 0.7 * a); ctx.stroke()
    ctx.restore()

def tree(ctx, x, y, s, grow=1.0, alpha=1.0, t=0.0, ghost=False):
    if grow <= 0 or alpha <= 0: return
    h = s * grow; sw = 0.03 * math.sin(t * 1.5)
    ctx.save(); ctx.translate(x, y)
    tc = (0.55, 0.6, 0.68) if ghost else BROWN[:3]
    ctx.new_path(); ctx.move_to(-0.08 * s, 0); ctx.line_to(-0.05 * s, -0.62 * h); ctx.line_to(0.05 * s, -0.62 * h); ctx.line_to(0.08 * s, 0); ctx.close_path()
    ctx.set_source_rgba(tc[0], tc[1], tc[2], alpha); ctx.fill()
    for (cx, cy, r, c) in [(-0.2, -0.62, 0.26, LEAF_D), (0.2, -0.64, 0.26, LEAF_D), (0.0, -0.85, 0.32, LEAF), (-0.12, -0.6, 0.22, LEAF), (0.14, -0.58, 0.2, LEAF)]:
        cc = (0.6, 0.66, 0.75) if ghost else c[:3]
        ctx.arc(cx * s * grow + sw * s, cy * h, r * s * grow, 0, 2 * math.pi); ctx.set_source_rgba(cc[0], cc[1], cc[2], alpha); ctx.fill()
    ctx.restore()

def moss(ctx, x0, x1, y, s, alpha=1.0, t=0.0):
    if alpha <= 0 or s <= 0: return
    n = int((x1 - x0) / (28 * max(s, 0.3)))
    for i in range(n):
        xx = x0 + i * (x1 - x0) / max(n - 1, 1); hh = s * (14 + 10 * math.sin(i * 2.3)) * (1 + 0.08 * math.sin(t * 3 + i))
        ctx.arc(xx, y, hh, math.pi, 2 * math.pi); ctx.set_source_rgba(0.35 + 0.1 * math.sin(i), 0.7, 0.3, alpha); ctx.fill()

def island(ctx, x, y, w, alpha=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(w / 2, 40)
    ctx.arc(0, 0, 1, math.pi, 2 * math.pi); ctx.restore(); rgba(ctx, SAND, alpha); ctx.fill()

def dino(ctx, x, y, s, alpha=1.0, rot=0.0, color=(0.5, 0.72, 0.38), t=0.0):
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s)
    c = color; ctx.set_source_rgba(c[0], c[1], c[2], alpha)
    nk = 0.05 * math.sin(t * 2)
    for lx in (-0.3, -0.12, 0.12, 0.3):
        rrect(ctx, lx - 0.06, 0.05, 0.12, 0.5, 0.05); ctx.fill()
    ctx.save(); ctx.scale(0.55, 0.3); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); ctx.fill()
    ctx.new_path(); ctx.move_to(0.3, -0.18); ctx.curve_to(0.55, -0.35, 0.6, -0.7 + nk, 0.72, -0.9 + nk); ctx.line_to(0.82, -0.85 + nk)
    ctx.curve_to(0.7, -0.6, 0.62, -0.2, 0.45, 0.05); ctx.close_path(); ctx.fill()
    ctx.save(); ctx.translate(0.8, -0.92 + nk); ctx.scale(0.16, 0.09); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); ctx.fill()
    ctx.new_path(); ctx.move_to(-0.45, -0.12); ctx.curve_to(-0.8, -0.05, -1.0, 0.05, -1.2, 0.18); ctx.curve_to(-0.95, 0.12, -0.7, 0.12, -0.45, 0.12); ctx.close_path(); ctx.fill()
    ctx.arc(0.85, -0.95 + nk, 0.025, 0, 2 * math.pi); ctx.set_source_rgba(0, 0, 0, alpha); ctx.fill()
    ctx.restore()

def meteor(ctx, x, y, r, ang, alpha=1.0):
    if alpha <= 0: return
    for k in range(12):
        d = k * r * 0.55; ctx.arc(x - d * math.cos(ang), y - d * math.sin(ang), r * (1 - k / 13), 0, 2 * math.pi)
        ctx.set_source_rgba(1, 0.55 + 0.03 * k, 0.15, alpha * (0.6 - k * 0.045)); ctx.fill()
    glow(ctx, x, y, r * 2.6, ORANGE, 0.7 * alpha)
    ctx.arc(x, y, r, 0, 2 * math.pi); ctx.set_source_rgba(0.45, 0.32, 0.25, alpha); ctx.fill()

def bone(ctx, x, y, s, rot=0.0, alpha=1.0):
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s); ctx.set_source_rgba(0.96, 0.94, 0.88, alpha)
    rrect(ctx, -0.8, -0.16, 1.6, 0.32, 0.1); ctx.fill()
    for (bx, by) in [(-0.85, -0.18), (-0.85, 0.18), (0.85, -0.18), (0.85, 0.18)]:
        ctx.arc(bx, by, 0.24, 0, 2 * math.pi); ctx.fill()
    ctx.restore()

def head_profile(ctx, x, y, s, alpha=1.0, nose=0.0, ear=0.0, t=0.0):
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rgba(ctx, SKIN, alpha)
    ctx.new_path(); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.fill()
    rrect(ctx, -0.35, 0.7, 0.7, 0.7, 0.2); ctx.fill()
    ctx.set_source_rgba(0.35, 0.22, 0.14, alpha); ctx.new_path(); ctx.arc(-0.05, -0.15, 1.02, math.pi * 0.95, math.pi * 1.95); ctx.close_path(); ctx.fill()
    ctx.arc(0.5, -0.1, 0.07, 0, 2 * math.pi); ctx.set_source_rgba(0.1, 0.1, 0.1, alpha); ctx.fill()
    nc = mixc(SKIN, CART, nose)
    ctx.new_path(); ctx.move_to(0.9, -0.05); ctx.curve_to(1.25, 0.25, 1.25, 0.32, 0.95, 0.38); ctx.close_path(); rgba(ctx, nc, alpha); ctx.fill()
    if nose > 0: glow(ctx, 1.05, 0.2, 0.45, CART, 0.6 * nose * alpha)
    ec = mixc(mixc(SKIN, (0.9, 0.7, 0.6, 1), 0.4), CART, ear)
    ctx.save(); ctx.translate(-0.25, 0.05); ctx.scale(0.22, 0.32); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); rgba(ctx, ec, alpha); ctx.fill()
    if ear > 0: glow(ctx, -0.25, 0.05, 0.5, CART, 0.6 * ear * alpha)
    ctx.move_to(0.7, 0.55); ctx.curve_to(0.8, 0.6, 0.85, 0.58, 0.9, 0.52); ctx.set_line_width(0.05); ctx.set_source_rgba(0.6, 0.3, 0.3, alpha); ctx.stroke()
    ctx.restore()

def feather(ctx, x, y, s, rot=0.0, alpha=1.0):
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s)
    ctx.new_path(); ctx.move_to(0, -1); ctx.curve_to(0.55, -0.6, 0.5, 0.3, 0.05, 0.75); ctx.curve_to(-0.45, 0.3, -0.5, -0.6, 0, -1); ctx.close_path()
    ctx.set_source_rgba(0.95, 0.97, 1, alpha); ctx.fill()
    ctx.move_to(0, -0.9); ctx.line_to(0.02, 1.1); ctx.set_line_width(0.06); ctx.set_source_rgba(0.6, 0.65, 0.75, alpha); ctx.stroke()
    for k in range(5):
        yy = -0.6 + k * 0.28; ctx.move_to(0.01, yy); ctx.line_to(0.3, yy - 0.18); ctx.move_to(0.01, yy); ctx.line_to(-0.28, yy - 0.18)
    ctx.set_line_width(0.025); ctx.stroke(); ctx.restore()

def battery(ctx, x, y, s, level, alpha=1.0):
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rrect(ctx, -1, -0.5, 1.9, 1.0, 0.18); ctx.set_line_width(0.12); rgba(ctx, WHITE, alpha); ctx.stroke()
    rrect(ctx, 0.95, -0.2, 0.15, 0.4, 0.05); ctx.fill()
    c = GREEN if level > 0.4 else ACCENT
    rrect(ctx, -0.88, -0.38, 1.66 * clamp(level), 0.76, 0.1); rgba(ctx, c, alpha); ctx.fill()
    ctx.restore()

def tooth(ctx, x, y, s, alpha=1.0, shade=0.0, rot=0.0):
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s)
    ctx.new_path(); ctx.move_to(-0.5, 0); ctx.curve_to(-0.35, -0.3, -0.12, -0.7, 0, -1.05); ctx.curve_to(0.12, -0.7, 0.35, -0.3, 0.5, 0); ctx.close_path()
    v = 0.97 - 0.35 * shade; ctx.set_source_rgba(v, v, v * 0.95, alpha); ctx.fill_preserve()
    ctx.set_line_width(0.04); ctx.set_source_rgba(0.5, 0.5, 0.55, alpha); ctx.stroke()
    for k in range(5):
        ex = -0.45 + k * 0.1; ctx.move_to(ex, -0.05 - k * 0.2); ctx.line_to(ex + 0.06, -0.12 - k * 0.2)
    ctx.set_line_width(0.03); ctx.stroke(); ctx.restore()

def jaw(ctx, cx, cy, t, t_drop, t_new, alpha=1.0):
    """Mandíbula en corte: filas de dientes de reserva que avanzan como una cinta."""
    rrect(ctx, cx - 430, cy - 330, 860, 400, 60); ctx.set_source_rgba(0.85, 0.42, 0.5, alpha); ctx.fill()
    rrect(ctx, cx - 430, cy - 330, 860, 400, 60); ctx.set_line_width(6); ctx.set_source_rgba(0.6, 0.25, 0.32, alpha); ctx.stroke()
    p = ease((t - t_new) / 0.7); fall = clamp((t - t_drop) / 0.9)
    for col in range(5):
        x = cx - 320 + col * 160
        for r in range(4):
            rr = r - (p if col == 2 else 0.0)
            if col == 2 and r == 0:
                if fall > 0:
                    tooth(ctx, x + 60 * fall, cy + 40 + 520 * fall * fall, 95, alpha * (1 - fall), 0, rot=fall * 2.2)
                    continue
            if rr < 0: continue
            k = 1 - 0.18 * rr
            tooth(ctx, x, cy + 40 - rr * 105, 95 * k, alpha, shade=rr / 3)
    if t > t_new - 0.1 and p < 1:
        arrow(ctx, cx + 470, cy - 260, cx + 470, cy + 10, ACCENT, alpha * (1 - p) * clamp((t - t_new + 0.1) / 0.2), 12, 36)

def crown(ctx, x, y, s, alpha=1.0):
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.new_path(); ctx.move_to(-1, 0.5); ctx.line_to(-1, -0.4); ctx.line_to(-0.5, 0.05); ctx.line_to(0, -0.6); ctx.line_to(0.5, 0.05); ctx.line_to(1, -0.4); ctx.line_to(1, 0.5); ctx.close_path()
    rgba(ctx, ACCENT, alpha); ctx.fill()
    for (gx, gy) in [(-1, -0.45), (0, -0.66), (1, -0.45)]:
        ctx.arc(gx, gy, 0.12, 0, 2 * math.pi); rgba(ctx, RED, alpha); ctx.fill()
    ctx.restore()

def timeline(ctx, t, x0, x1, y, alpha=1.0):
    ctx.set_line_width(10); ctx.set_line_cap(cairo.LINE_CAP_ROUND); rgba(ctx, WHITE, 0.85 * alpha)
    ctx.move_to(x0, y); ctx.line_to(x1, y); ctx.stroke()
    for ma in (450, 300, 150, 0):
        xx = x0 + (450 - ma) / 450 * (x1 - x0)
        ctx.move_to(xx, y - 18); ctx.line_to(xx, y + 18); ctx.set_line_width(6); ctx.stroke()
        label(ctx, "HOY" if ma == 0 else f"{ma} M", xx, y + 70, 36, hexc("C8CEE0"), alpha, bg=False)

def tx(ma, x0=110, x1=930): return x0 + (450 - ma) / 450 * (x1 - x0)

# ---------------- scenes ----------------
def s_hook(ctx, t):  # 0–2.96 (texto + movimiento desde el cuadro 0)
    bg(ctx, t)
    shark(ctx, lerp(580, 420, t / 3), 900 + 15 * math.sin(t * 2.2), 260, t, wag=1.3)
    text(ctx, "TIBURONES", W / 2, 300, 138, ACCENT, stroke=16)
    text(ctx, "más viejos que", W / 2, 440, 84, WHITE, stroke=12)
    text(ctx, "los ÁRBOLES", W / 2, 560, 104, LEAF, stroke=14)
    if t > 2.1:
        k = back((t - 2.1) / 0.35)
        island(ctx, 790, 1260, 320 * k); tree(ctx, 790, 1250, 250, k, t=t)
        pop_text(ctx, "MÁS VIEJO", 330, 1190, 64, ACCENT, t, 2.3, stroke=10)

def s_450(ctx, t):  # 2.96–8.3
    bg(ctx, t)
    header(ctx, "Escamas de", "TIBURÓN", t, 3.0, size=78)
    # piel de tiburón con dentículos (escamas en forma de diente)
    z = 1 + 0.08 * ease((t - 3.0) / 5)
    ctx.save(); ctx.translate(W / 2, 760); ctx.scale(z, z)
    rrect(ctx, -360, -260, 720, 520, 60); ctx.set_source_rgba(0.3, 0.4, 0.5, ease((t - 3.0) / 0.4)); ctx.fill()
    for i in range(7):
        for j in range(5):
            k = back((t - 3.2 - (i + j) * 0.05) / 0.35)
            if k <= 0: continue
            sx = -300 + i * 100 + (50 if j % 2 else 0); sy = -200 + j * 100
            if sx > 330: continue
            ctx.save(); ctx.translate(sx, sy); ctx.scale(k, k); ctx.rotate(-0.5)
            ctx.new_path(); ctx.move_to(-38, 18); ctx.curve_to(-20, -30, 10, -40, 45, -8); ctx.curve_to(20, 0, 0, 20, -38, 18); ctx.close_path()
            ctx.set_source_rgba(0.75, 0.82, 0.9, 1); ctx.fill(); ctx.restore()
    ctx.restore()
    if t > 4.4: label(ctx, "LAS MÁS ANTIGUAS", W / 2, 1080, 50, WHITE, ease((t - 4.4) / 0.3))
    if t > 5.6:
        n = int(450 * ease((t - 5.6) / 1.3))
        ctx.save(); ctx.translate(W / 2, 1215); s = back((t - 5.6) / 0.3); ctx.scale(s, s)
        counter_box(ctx, 0, 0, n, "MILLONES DE AÑOS", size=120, sub=40); ctx.restore()

def s_385(ctx, t):  # 8.3–12.7
    bg(ctx, t)
    header(ctx, "Primeros", "ÁRBOLES", t, 8.35, size=86, c2=LEAF)
    g = ease((t - 8.7) / 1.4)
    island(ctx, W / 2, 1110, 700, ease((t - 8.4) / 0.4)); tree(ctx, W / 2, 1100, 560, g, t=t)
    if t > 10.4:
        n = int(385 * ease((t - 10.4) / 1.3))
        ctx.save(); ctx.translate(W / 2, 1235); s = back((t - 10.4) / 0.3); ctx.scale(s, s)
        counter_box(ctx, 0, 0, n, "MILLONES", color=LEAF, size=120, sub=44); ctx.restore()

def s_moss(ctx, t):  # 12.7–18.2
    bg(ctx, t)
    # tierra arriba (solo musgo), mar abajo (tiburones)
    a = ease((t - 12.7) / 0.4)
    ctx.rectangle(0, 440, W, 280); ctx.set_source_rgba(0.45, 0.35, 0.2, 0.9 * a); ctx.fill()
    ctx.rectangle(0, 440, W, 26); ctx.set_source_rgba(0.3, 0.55, 0.25, 0.9 * a); ctx.fill()
    if t < 14.8:
        header(ctx, "Hace", "450 MILLONES", t, 12.75, size=76)
    else:
        header(ctx, "En tierra:", "SOLO MUSGO", t, 14.85, size=76, c2=LEAF)
    for i, (sx, sy, ss, fl) in enumerate([(320, 880, 150, False), (760, 1060, 120, True), (380, 1180, 95, False)]):
        k = ease((t - 13.0 - i * 0.25) / 0.5)
        shark(ctx, sx + (60 if not fl else -60) * math.sin(t * 0.6 + i) , sy, ss * k, t, alpha=k, flip=fl, ph=i * 2)
    mk = back((t - 15.84) / 0.5)
    moss(ctx, 60, 1020, 442, 1.3 * mk, 1.0, t)
    if t > 16.4:
        u = ease((t - 16.4) / 0.4)
        tree(ctx, 820, 705, 210, 1, u * 0.45, t, ghost=True); cross(ctx, 820, 600, 60 * back((t - 16.5) / 0.35))
        label(ctx, "SIN ÁRBOLES", 330, 600, 50, WHITE, u)
    if t > 17.0: label(ctx, "+65 MILLONES DE AÑOS DE VENTAJA", W / 2, 790, 44, ACCENT, ease((t - 17.0) / 0.3))

def s_twist(ctx, t):  # 18.2–20.0
    bg(ctx, t)
    sh = 8 * math.sin(t * 50) * clamp((t - 19.44) / 0.1) * (1 - clamp((t - 19.8) / 0.2))
    pop_text(ctx, "PERO ESO", W / 2 + sh, 560, 130, WHITE, t, 18.24)
    pop_text(ctx, "NO ES LO", W / 2 + sh, 720, 130, WHITE, t, 18.8)
    pop_text(ctx, "MÁS LOCO", W / 2 + sh, 900, 150, ACCENT, t, 19.2)
    shark(ctx, lerp(-300, 1400, (t - 18.2) / 1.8), 1180, 160, t, wag=1.6)

def s_dino(ctx, t):  # 20.0–24.0
    bg(ctx, t)
    header(ctx, "", "ANTES QUE LOS", t, 20.05, y=290, size=80)
    header(ctx, "", "DINOSAURIOS", t, 22.9, y=400, size=96, c2=LEAF)
    y = 1000; timeline(ctx, t, 110, 930, y, ease((t - 20.0) / 0.3))
    k = back((t - 20.1) / 0.4)
    shark(ctx, tx(450) + 90, y - 130, 105 * k, t)
    if t > 20.9:
        u = ease((t - 20.9) / 1.6); xe = lerp(tx(450), tx(235), u)
        ctx.set_line_width(14); rgba(ctx, ACCENT); ctx.move_to(tx(450), y - 260); ctx.line_to(xe, y - 260); ctx.stroke()
        ctx.move_to(tx(450), y - 285); ctx.line_to(tx(450), y - 235); ctx.stroke()
        if u > 0.98: ctx.move_to(xe, y - 285); ctx.line_to(xe, y - 235); ctx.stroke()
        label(ctx, "+200 MILLONES", (tx(450) + tx(235)) / 2, y - 330, 50, ACCENT, ease((t - 21.3) / 0.3))
    dk = back((t - 22.9) / 0.4)
    dino(ctx, tx(235), y - 95, 105 * dk, t=t)

def s_extinct(ctx, t):  # 24.0–28.8
    bg(ctx, t)
    if t < 25.3:
        header(ctx, "", "SOBREVIVIERON", t, 24.05, size=96, c2=GREEN)
    else:
        header(ctx, "a varias", "EXTINCIONES", t, 25.35, size=84, c2=RED)
    # tierra con dinosaurio, mar con tiburón
    ctx.rectangle(0, 720, W, 120); ctx.set_source_rgba(0.42, 0.33, 0.2, 1); ctx.fill()
    ctx.rectangle(0, 710, W, 18); ctx.set_source_rgba(0.35, 0.55, 0.25, 1); ctx.fill()
    hit = 27.55; dead = ease((t - hit - 0.1) / 0.5)
    dino(ctx, 640, 620, 110, 1.0, rot=dead * 0.4, color=mixc((0.5, 0.72, 0.38, 1), (0.4, 0.4, 0.4, 1), dead), t=t)
    for i, tm in enumerate((24.4, 25.9)):
        u = clamp((t - tm) / 0.8)
        if 0 < u < 1: meteor(ctx, lerp(1100, 200 + i * 300, u), lerp(380, 700, u), 26, math.atan2(320, -900 + i * 300))
        if u >= 1:
            fl = clamp(1 - (t - tm - 0.8) / 0.6)
            if fl > 0: glow(ctx, 200 + i * 300, 710, 260, ORANGE, 0.9 * fl)
    u = clamp((t - 26.75) / 0.8)
    if 0 < u < 1: meteor(ctx, lerp(1200, 640, u), lerp(380, 660, u), 46, math.atan2(280, -560))
    if t > hit:
        fl = clamp(1 - (t - hit) / 0.8); ctx.set_source_rgba(1, 0.85, 0.6, 0.7 * fl); ctx.paint(); glow(ctx, 640, 660, 500, ORANGE, 0.9 * fl)
        cross(ctx, 640, 470, 64 * back((t - hit - 0.1) / 0.35))
    shark(ctx, 420 + 40 * math.sin(t * 0.8), 1060, 190, t)
    if t > 28.0: check(ctx, 660, 950, 62 * back((t - 28.0) / 0.35))

def s_secret(ctx, t):  # 28.8–31.4
    bg(ctx, t)
    pop_text(ctx, "¿SU SECRETO?", W / 2, 420, 116, ACCENT, t, 28.85)
    k = back((t - 29.9) / 0.4)
    bone(ctx, W / 2, 820, 220 * k, rot=-0.3 + 0.05 * math.sin(t * 3))
    if t > 30.6: cross(ctx, W / 2, 820, 150 * back((t - 30.6) / 0.3))
    stamp(ctx, "SIN HUESOS", W / 2, 1160, 92, RED, t, 30.72, rot=-0.08)

def s_cart(ctx, t):  # 31.4–35.15
    bg(ctx, t)
    if t < 33.35:
        header(ctx, "Esqueleto de", "CARTÍLAGO", t, 31.45, size=80, c2=CART)
        xr = ease((t - 31.6) / 0.6)
        shark(ctx, W / 2, 840, 330, t, xray=xr, wag=0.6)
        if xr > 0:
            yy = lerp(560, 1120, (t * 0.6) % 1)
            ctx.rectangle(80, yy - 3, 920, 6); rgba(ctx, CART, 0.35 * xr); ctx.fill()
    else:
        header(ctx, "Como tu", "NARIZ Y OREJAS", t, 33.4, size=72, c2=CART)
        k = back((t - 33.4) / 0.4)
        head_profile(ctx, W / 2 - 40, 830, 260 * k, nose=ease((t - 33.68) / 0.3), ear=ease((t - 34.4) / 0.3), t=t)
        if t > 33.8: label(ctx, "NARIZ", W / 2 + 330, 740, 46, CART, ease((t - 33.8) / 0.3))
        if t > 34.45: label(ctx, "OREJA", W / 2 - 300, 1060, 46, CART, ease((t - 34.45) / 0.3))

def s_light(ctx, t):  # 35.15–38.0
    bg(ctx, t)
    if t < 36.0: header(ctx, "Más", "LIGERO", t, 35.2, size=96)
    else: header(ctx, "Menos", "ENERGÍA", t, 36.05, size=96, c2=GREEN)
    k = back((t - 35.25) / 0.4)
    feather(ctx, 260, 640 + 30 * math.sin(t * 2), 130 * k, rot=0.4 + 0.2 * math.sin(t * 1.7))
    bk = back((t - 36.1) / 0.4)
    battery(ctx, 760, 640, 120 * bk, 1.0 - 0.15 * ease((t - 36.4) / 1.5))
    shark(ctx, lerp(-260, 1350, (t - 35.15) / 2.85), 1040, 190, t, wag=1.8)

def s_teeth(ctx, t):  # 38.0–44.8
    bg(ctx, t)
    if t < 39.0: header(ctx, "Sus", "DIENTES", t, 38.05, size=96)
    elif t < 42.7: header(ctx, "NUNCA SE", "ACABAN", t, 39.05, size=92)
    else: header(ctx, "En su vida:", "MILES", t, 42.75, size=92)
    a = ease((t - 38.1) / 0.4)
    ctx.save(); ctx.translate(0, (1 - a) * 60)
    jaw(ctx, W / 2 - 30, 900, t, 40.5, 41.35, a); ctx.restore()
    if 40.6 < t < 42.0: label(ctx, "SE CAE", 300, 1180, 44, RED, ease((t - 40.6) / 0.25) * (1 - ease((t - 41.7) / 0.3)))
    if 41.4 < t < 42.7: label(ctx, "SALE OTRO", 620, 1180, 44, GREEN, ease((t - 41.4) / 0.25) * (1 - ease((t - 42.4) / 0.3)))
    if t > 42.8:
        random.seed(77)
        for i in range(26):
            ph = random.random(); sx = random.uniform(80, 940); sp = random.uniform(500, 900)
            yy = -100 + (t - 42.8 - ph * 0.8) * sp
            if -100 < yy < 1300: tooth(ctx, sx, yy, random.uniform(30, 55), 0.95, rot=(t * 2 + i) % 6.28)
    stamp(ctx, "MILES", W / 2, 1150, 110, ACCENT, t, 44.16, rot=-0.1)

def s_green(ctx, t):  # 44.8–53.5
    dp = ease((t - 44.8) / 1.2)
    bg(ctx, t, deep=dp, ice=dp)
    if t < 46.05: header(ctx, "El", "RÉCORD", t, 44.9, y=330, size=110)
    elif t < 49.1: header(ctx, "Tiburón de", "GROENLANDIA", t, 46.1, y=330, size=80, c2=CART)
    elif t < 50.85: header(ctx, "Puede vivir", "CASI", t, 49.15, y=330, size=88)
    else: header(ctx, "El vertebrado", "MÁS LONGEVO", t, 50.9, y=330, size=78)
    gk = ease((t - 45.9) / 0.8)
    shark(ctx, lerp(380, 640, clamp((t - 45.9) / 7.6)), 760, 250 * gk, t, alpha=gk, body=(0.36, 0.37, 0.4), belly=(0.48, 0.48, 0.5), wag=0.35, sy=1.25)
    if 46.6 < t < 49.1: label(ctx, "VIVE EN AGUAS HELADAS", W / 2, 1000, 46, WHITE, ease((t - 47.6) / 0.3))
    if t > 49.15:
        n = int(400 * ease((t - 49.2) / 1.2))
        ctx.save(); ctx.translate(W / 2, 1100); s = back((t - 49.2) / 0.3); ctx.scale(s, s)
        counter_box(ctx, 0, 0, f"~{n}", "AÑOS", size=170, sub=60); ctx.restore()
    if t > 51.0:
        crown(ctx, lerp(380, 640, clamp((t - 45.9) / 7.6)) + 160, 590 + 10 * math.sin(t * 2), 70 * back((t - 51.0) / 0.4))
    if t > 52.0: label(ctx, "QUE SE CONOCE", W / 2, 1250, 46, WHITE, ease((t - 52.0) / 0.3))

def s_ask(ctx, t):  # 53.5–56.3
    bg(ctx, t)
    pop_text(ctx, "¿QUÉ ANIMAL", W / 2, 430, 108, WHITE, t, 53.55)
    pop_text(ctx, "ES MÁS ANTIGUO?", W / 2, 570, 96, ACCENT, t, 55.2)
    shark(ctx, W / 2 - 60, 880 + 15 * math.sin(t * 2), 200 * back((t - 53.6) / 0.4), t)
    for i, (qx, qy) in enumerate([(250, 1120), (540, 1170), (830, 1120)]):
        pop_text(ctx, "?", qx, qy, 120, [ACCENT, CART, LEAF][i], t, 54.0 + i * 0.25)

def s_end(ctx, t):  # 56.3–end
    bg(ctx, t)
    a = ease((t - 56.3) / 0.5)
    shark(ctx, lerp(-260, 1350, ((t - 56.3) / 4.5) % 1), 1490, 150, t, alpha=a)
    sc = 0.85 + 0.15 * back((t - 56.3) / 0.5); s = 300 * sc
    logo_mark(ctx, (W - s) / 2, 470 + (300 - s) / 2, s, a)
    w1 = text_w(ctx, "Logi", 120); w2 = text_w(ctx, "Datos", 120); x0 = (W - w1 - w2) / 2
    text(ctx, "Logi", x0, 900, 120, WHITE, align="left", alpha=a); text(ctx, "Datos", x0 + w1, 900, 120, ACCENT, align="left", alpha=a)
    text(ctx, "Curiosidades con lógica y datos", W / 2, 1010, 48, hexc("C8CEE0"), bold=False, alpha=a)
    bubble_icon(ctx, W / 2 - 250, 1180, 50 * back((t - 56.4) / 0.35))
    pa = back((t - 57.1) / 0.4)
    if pa > 0:
        ctx.save(); ctx.translate(W / 2 + 60, 1175); ctx.scale(pa, pa)
        pw = text_w(ctx, "SÍGUENOS", 54) + 100; rrect(ctx, -pw / 2, -52, pw, 104, 52); rgba(ctx, ACCENT); ctx.fill()
        text(ctx, "SÍGUENOS", 0, 0, 54, NAVY); ctx.restore()

SCENES = [(0.0, s_hook), (2.96, s_450), (8.3, s_385), (12.7, s_moss), (18.2, s_twist), (20.0, s_dino), (24.0, s_extinct),
          (28.8, s_secret), (31.4, s_cart), (35.15, s_light), (38.0, s_teeth), (44.8, s_green), (53.5, s_ask), (56.3, s_end)]
END_START = 56.3

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
EMPH = {"CUATROCIENTOS", "CINCUENTA", "TRESCIENTOS", "OCHENTA", "CINCO", "MUSGOS", "LOCO", "DOSCIENTOS", "DINOSAURIOS", "EXTINCIONES",
        "MASIVAS", "SECRETO", "HUESOS", "CARTÍLAGO", "NARIZ", "OREJAS", "LIGERO", "DIENTES", "MILES", "RÉCORD", "GROENLANDIA", "LONGEVO", "ANTIGUO"}
def clean(s): return s.replace("…", "").replace("¿", "").rstrip(".,;:?!…").upper()

CAP_Y, CAP_SIZE = 1400, 86
def captions(ctx, t):
    if t < 2.96: return  # el gancho ya está escrito en pantalla
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
