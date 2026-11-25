#!/usr/bin/env python3
"""LogiDatos Short #6 – La caja negra de los aviones no es negra. Motion graphics drawn in code (cairo).
python3 video_06_caja_negra.py [preview t1 t2 ...]
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
    w1 = text_w(ctx, s1 + " ", size) if s1 else 0; w2 = text_w(ctx, s2, size); x0 = (W - w1 - w2) / 2
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

# ---------------- background ----------------
random.seed(6)
DOTS = [(random.random(), random.random(), random.uniform(2, 5), random.random()) for _ in range(60)]

def bg(ctx, t, tint=None, sea=0.0):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, 0.05, 0.07, 0.15); g.add_color_stop_rgb(0.55, 0.04, 0.05, 0.11); g.add_color_stop_rgb(1, 0.02, 0.02, 0.05)
    ctx.set_source(g); ctx.paint()
    # faint radar grid
    ctx.set_line_width(1.5); ctx.set_source_rgba(0.4, 0.6, 1.0, 0.05)
    off = (t * 12) % 90
    for x in range(0, W + 90, 90): ctx.move_to(x, 0); ctx.line_to(x, H)
    for y in range(-90, H + 90, 90): ctx.move_to(0, y + off); ctx.line_to(W, y + off)
    ctx.stroke()
    glow(ctx, 220 + 60 * math.sin(t * 0.3), 620, 650, ORANGE, 0.12)
    glow(ctx, 880, 1250 + 50 * math.sin(t * 0.2), 700, BLUE, 0.10)
    for (x, y, r, ph) in DOTS:
        yy = (y * H - t * (10 + 20 * ph)) % H; a = 0.10 + 0.08 * math.sin(t * 2 + ph * 9)
        ctx.set_source_rgba(1, 0.9, 0.75, a); ctx.arc(x * W, yy, r, 0, 2 * math.pi); ctx.fill()
    if sea > 0: water(ctx, lerp(H + 40, 420, sea), t)
    if tint: ctx.set_source_rgba(tint[0], tint[1], tint[2], tint[3]); ctx.paint()

def water(ctx, top, t, alpha=1.0):
    ctx.new_path(); ctx.move_to(0, H); ctx.line_to(0, top)
    for x in range(0, W + 20, 20): ctx.line_to(x, top + 12 * math.sin(x / 70 + t * 2.5))
    ctx.line_to(W, H); ctx.close_path()
    g = cairo.LinearGradient(0, top, 0, H)
    g.add_color_stop_rgba(0, 0.12, 0.45, 0.75, 0.55 * alpha); g.add_color_stop_rgba(1, 0.01, 0.06, 0.16, 0.92 * alpha)
    ctx.set_source(g); ctx.fill()
    ctx.set_line_width(4); ctx.set_source_rgba(0.6, 0.85, 1, 0.5 * alpha); ctx.move_to(0, top)
    for x in range(0, W + 20, 20): ctx.line_to(x, top + 12 * math.sin(x / 70 + t * 2.5))
    ctx.stroke()
    # light rays + bubbles
    for k in range(5):
        x0 = 120 + k * 220 + 40 * math.sin(t * 0.4 + k)
        ctx.new_path(); ctx.move_to(x0, top); ctx.line_to(x0 + 60, top); ctx.line_to(x0 + 160, H); ctx.line_to(x0 + 40, H); ctx.close_path()
        ctx.set_source_rgba(0.7, 0.9, 1, 0.035 * alpha); ctx.fill()
    for k in range(14):
        ph = (t * 0.25 + k / 14) % 1; y = H - ph * (H - top)
        ctx.set_source_rgba(0.8, 0.95, 1, 0.35 * alpha * math.sin(ph * math.pi)); ctx.set_line_width(2)
        ctx.arc(60 + (k * 173) % 960, y, 5 + 3 * (k % 3), 0, 2 * math.pi); ctx.stroke()

# ---------------- objects ----------------
BLACK = (0.07, 0.07, 0.08, 1.0)
def black_box(ctx, x, y, s, mix=1.0, alpha=1.0, rot=0.0, glow_a=0.0):
    """Flight recorder centred at x,y, width 2s. mix 0 = black, 1 = international orange."""
    if alpha <= 0 or s <= 0: return
    if glow_a > 0: glow(ctx, x, y, s * 2.0, ORANGE, 0.45 * glow_a * alpha)
    body = mixc(BLACK, ORANGE, mix); light = mixc((0.2, 0.2, 0.22, 1), ORANGE_L, mix); dark = mixc((0.02, 0.02, 0.03, 1), ORANGE_D, mix)
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s)
    # shadow
    ctx.save(); ctx.scale(1, 0.18); ctx.arc(0, 4.2, 1.15, 0, 2 * math.pi); ctx.restore(); ctx.set_source_rgba(0, 0, 0, 0.35 * alpha); ctx.fill()
    # handle
    ctx.set_line_width(0.1); rgba(ctx, dark, alpha); ctx.new_path(); ctx.arc(0, -0.55, 0.32, math.pi, 2 * math.pi); ctx.stroke()
    # beacon cylinder (left)
    rrect(ctx, -1.32, -0.2, 0.36, 0.34, 0.08); rgba(ctx, mixc((0.25, 0.25, 0.27, 1), (0.85, 0.85, 0.82, 1), mix), alpha); ctx.fill()
    ctx.set_source_rgba(0.1, 0.1, 0.1, alpha); ctx.rectangle(-1.3, -0.06, 0.04, 0.06); ctx.fill()
    # body
    rrect(ctx, -1, -0.55, 2, 1.1, 0.14)
    g = cairo.LinearGradient(0, -0.55, 0, 0.55)
    g.add_color_stop_rgba(0, light[0], light[1], light[2], alpha); g.add_color_stop_rgba(0.5, body[0], body[1], body[2], alpha)
    g.add_color_stop_rgba(1, dark[0], dark[1], dark[2], alpha); ctx.set_source(g); ctx.fill()
    # reflective stripes
    for sx in (-0.78, 0.62):
        ctx.rectangle(sx, -0.55, 0.16, 1.1); ctx.set_source_rgba(0.92, 0.94, 0.96, (0.25 + 0.65 * mix) * alpha); ctx.fill()
    # bolts
    for (bx, by) in [(-0.88, -0.44), (0.88, -0.44), (-0.88, 0.44), (0.88, 0.44)]:
        ctx.arc(bx, by, 0.04, 0, 2 * math.pi); rgba(ctx, dark, alpha); ctx.fill()
    # lettering
    tc = mixc((0.45, 0.45, 0.48, 1), (0.08, 0.05, 0.03, 1), mix)
    for (s_, yy, sz) in [("FLIGHT", -0.2, 0.2), ("RECORDER", 0.04, 0.2), ("DO NOT OPEN", 0.28, 0.12)]:
        ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(sz)
        w = ctx.text_extents(s_).x_advance; ctx.move_to(-0.08 - w / 2, yy + sz * 0.36); rgba(ctx, tc, alpha); ctx.show_text(s_)
    ctx.restore()

def plane(ctx, x, y, s, alpha=1.0, rot=0.0, tail_box=0.0, t=0.0):
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s)
    body = (0.93, 0.95, 0.98)
    # far wing
    ctx.new_path(); ctx.move_to(0.12, -0.02); ctx.line_to(-0.05, -0.28); ctx.line_to(-0.13, -0.28); ctx.line_to(-0.08, -0.02); ctx.close_path()
    ctx.set_source_rgba(0.62, 0.68, 0.78, alpha); ctx.fill()
    # tail fin
    ctx.new_path(); ctx.move_to(-0.62, -0.1); ctx.line_to(-0.86, -0.48); ctx.line_to(-0.97, -0.48); ctx.line_to(-0.92, -0.1); ctx.close_path()
    ctx.set_source_rgba(0.2, 0.45, 0.85, alpha); ctx.fill()
    # fuselage
    ctx.new_path(); ctx.move_to(0.97, 0.02)
    ctx.curve_to(0.97, -0.08, 0.86, -0.11, 0.74, -0.11); ctx.line_to(-0.66, -0.11); ctx.line_to(-0.98, -0.15)
    ctx.line_to(-0.96, -0.05); ctx.curve_to(-0.86, 0.07, -0.76, 0.11, -0.6, 0.11); ctx.line_to(0.74, 0.11)
    ctx.curve_to(0.88, 0.11, 0.97, 0.09, 0.97, 0.02); ctx.close_path()
    g = cairo.LinearGradient(0, -0.11, 0, 0.11); g.add_color_stop_rgba(0, body[0], body[1], body[2], alpha); g.add_color_stop_rgba(1, 0.62, 0.66, 0.74, alpha)
    ctx.set_source(g); ctx.fill()
    # stripe + windows
    ctx.rectangle(-0.6, 0.03, 1.4, 0.018); ctx.set_source_rgba(0.2, 0.45, 0.85, alpha); ctx.fill()
    for k in range(18):
        ctx.arc(-0.5 + k * 0.066, -0.035, 0.016, 0, 2 * math.pi); ctx.set_source_rgba(0.15, 0.22, 0.35, alpha); ctx.fill()
    ctx.new_path(); ctx.move_to(0.83, -0.07); ctx.line_to(0.92, -0.07); ctx.line_to(0.95, -0.03); ctx.line_to(0.83, -0.03); ctx.close_path()
    ctx.set_source_rgba(0.15, 0.22, 0.35, alpha); ctx.fill()
    # stabilizer + near wing + engine
    ctx.new_path(); ctx.move_to(-0.7, 0.0); ctx.line_to(-0.95, 0.08); ctx.line_to(-0.88, 0.08); ctx.line_to(-0.62, 0.02); ctx.close_path()
    ctx.set_source_rgba(0.75, 0.8, 0.88, alpha); ctx.fill()
    ctx.new_path(); ctx.move_to(0.16, 0.05); ctx.line_to(-0.22, 0.36); ctx.line_to(-0.32, 0.36); ctx.line_to(-0.1, 0.05); ctx.close_path()
    ctx.set_source_rgba(0.8, 0.84, 0.9, alpha); ctx.fill()
    rrect(ctx, -0.08, 0.13, 0.2, 0.08, 0.04); ctx.set_source_rgba(0.55, 0.6, 0.7, alpha); ctx.fill()
    if tail_box > 0:
        bx, by = -0.8, -0.03
        glow(ctx, bx, by, 0.2, ORANGE, 0.8 * tail_box * alpha)
        rrect(ctx, bx - 0.06, by - 0.035, 0.12, 0.07, 0.015); rgba(ctx, ORANGE, tail_box * alpha); ctx.fill()
    ctx.restore()

def wreck(ctx, x, y, s, rot, alpha, seed):
    if s <= 0: return
    rnd = random.Random(seed); n = rnd.randint(5, 7)
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s); ctx.new_path()
    for i in range(n):
        a = i * 2 * math.pi / n + rnd.uniform(-0.3, 0.3); r = rnd.uniform(0.5, 1.0)
        (ctx.move_to if i == 0 else ctx.line_to)(r * math.cos(a), r * math.sin(a))
    ctx.close_path(); c = rnd.uniform(0.35, 0.6); ctx.set_source_rgba(c, c * 1.02, c * 1.08, alpha); ctx.fill_preserve()
    ctx.set_source_rgba(0.15, 0.15, 0.18, alpha); ctx.set_line_width(0.06); ctx.stroke(); ctx.restore()

def mic(ctx, x, y, s, alpha=1.0):
    if s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rrect(ctx, -0.32, -1, 0.64, 1.25, 0.32); rgba(ctx, WHITE, alpha); ctx.fill()
    ctx.set_line_width(0.14); rgba(ctx, WHITE, alpha); ctx.new_path(); ctx.arc(0, -0.05, 0.6, 0, math.pi); ctx.stroke()
    ctx.move_to(0, 0.55); ctx.line_to(0, 0.85); ctx.move_to(-0.35, 0.88); ctx.line_to(0.35, 0.88); ctx.stroke(); ctx.restore()

def waveform(ctx, x, y, w, h, t, alpha=1.0, color=ACCENT):
    n = 15; bw = w / n
    for i in range(n):
        v = 0.2 + 0.8 * abs(math.sin(t * 7 + i * 1.3) * math.sin(t * 3.1 + i * 0.7))
        rrect(ctx, x - w / 2 + i * bw + bw * 0.2, y - h * v / 2, bw * 0.6, h * v, bw * 0.3); rgba(ctx, color, alpha); ctx.fill()

def chart(ctx, x, y, w, h, t, alpha=1.0, color=GREEN):
    rrect(ctx, x - w / 2, y - h / 2, w, h, 18); ctx.set_source_rgba(0.03, 0.05, 0.1, 0.85 * alpha); ctx.fill()
    ctx.set_line_width(5); rgba(ctx, color, alpha); ctx.new_path()
    for i in range(41):
        u = i / 40; xx = x - w / 2 + 20 + u * (w - 40)
        yy = y + h * 0.3 * math.sin(u * 7 + t * 3) * math.cos(u * 3 - t)
        (ctx.move_to if i == 0 else ctx.line_to)(xx, yy)
    ctx.stroke()

def gauge(ctx, x, y, r, kind, t, alpha=1.0):
    if alpha <= 0 or r <= 0: return
    ctx.arc(x, y, r, 0, 2 * math.pi); ctx.set_source_rgba(0.03, 0.05, 0.1, 0.9 * alpha); ctx.fill_preserve()
    ctx.set_line_width(6); rgba(ctx, WHITE, 0.85 * alpha); ctx.stroke()
    ctx.set_line_width(3)
    for k in range(12):
        a = k * math.pi / 6; ctx.move_to(x + r * 0.78 * math.cos(a), y + r * 0.78 * math.sin(a)); ctx.line_to(x + r * 0.92 * math.cos(a), y + r * 0.92 * math.sin(a))
    ctx.stroke()
    if kind == "compass":
        ang = 0.6 * math.sin(t * 1.6)
        ctx.save(); ctx.translate(x, y); ctx.rotate(ang)
        ctx.new_path(); ctx.move_to(0, -r * 0.7); ctx.line_to(r * 0.13, 0); ctx.line_to(-r * 0.13, 0); ctx.close_path(); rgba(ctx, RED, alpha); ctx.fill()
        ctx.new_path(); ctx.move_to(0, r * 0.7); ctx.line_to(r * 0.13, 0); ctx.line_to(-r * 0.13, 0); ctx.close_path(); rgba(ctx, WHITE, alpha); ctx.fill()
        ctx.restore()
        text(ctx, "N", x, y - r * 0.62, r * 0.26, ACCENT, alpha=alpha)
    else:
        ang = (-2.2 + 2.6 * (0.5 + 0.5 * math.sin(t * (1.3 if kind == "alt" else 2.1)))) if kind else 0
        ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND); rgba(ctx, ACCENT if kind == "alt" else GREEN, alpha)
        ctx.move_to(x, y); ctx.line_to(x + r * 0.7 * math.cos(ang), y + r * 0.7 * math.sin(ang)); ctx.stroke()
    ctx.arc(x, y, r * 0.09, 0, 2 * math.pi); rgba(ctx, WHITE, alpha); ctx.fill()

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

def boat(ctx, x, y, s, alpha=1.0):
    if s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.new_path(); ctx.move_to(-1, -0.2); ctx.line_to(1, -0.2); ctx.line_to(0.75, 0.3); ctx.line_to(-0.8, 0.3); ctx.close_path()
    ctx.set_source_rgba(0.92, 0.93, 0.96, alpha); ctx.fill()
    ctx.rectangle(-0.35, -0.6, 0.6, 0.4); ctx.set_source_rgba(0.75, 0.8, 0.88, alpha); ctx.fill()
    ctx.rectangle(-0.05, -0.95, 0.06, 0.35); ctx.fill()
    ctx.rectangle(-1, 0.0, 2, 0.08); rgba(ctx, RED, alpha); ctx.fill(); ctx.restore()

def person(ctx, x, y, s, alpha=1.0, cap=False, shake=0.0, glasses=False, color=(0.55, 0.62, 0.78)):
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.new_path(); ctx.arc(0, 1.25, 0.95, math.pi, 2 * math.pi); ctx.close_path(); ctx.set_source_rgba(color[0] * 0.8, color[1] * 0.8, color[2] * 0.9, alpha); ctx.fill()
    if cap:
        ctx.new_path(); ctx.move_to(-0.15, 0.4); ctx.line_to(0, 0.75); ctx.line_to(0.15, 0.4); ctx.close_path(); ctx.set_source_rgba(0.95, 0.95, 0.95, alpha); ctx.fill()
    ctx.save(); ctx.rotate(shake)
    ctx.arc(0, 0, 0.5, 0, 2 * math.pi); ctx.set_source_rgba(0.96, 0.8, 0.66, alpha); ctx.fill()
    ctx.set_source_rgba(0.12, 0.1, 0.1, alpha)
    for ex in (-0.17, 0.17): ctx.arc(ex, 0.0, 0.055, 0, 2 * math.pi); ctx.fill()
    if glasses:
        ctx.set_line_width(0.04)
        for ex in (-0.17, 0.17): ctx.arc(ex, 0.0, 0.12, 0, 2 * math.pi); ctx.stroke()
        ctx.move_to(-0.05, 0); ctx.line_to(0.05, 0); ctx.stroke()
        ctx.new_path(); ctx.arc(0, -0.08, 0.5, math.pi * 1.1, math.pi * 1.9); ctx.set_line_width(0.14); ctx.set_source_rgba(0.85, 0.85, 0.85, alpha); ctx.stroke()
    ctx.set_line_width(0.05); ctx.set_source_rgba(0.35, 0.15, 0.1, alpha)
    ctx.new_path()
    if cap: ctx.move_to(-0.14, 0.24); ctx.curve_to(-0.05, 0.18, 0.05, 0.18, 0.14, 0.24)
    else: ctx.arc(0, 0.12, 0.15, 0.2, math.pi - 0.2)
    ctx.stroke()
    if cap:
        ctx.new_path(); ctx.move_to(-0.55, -0.22); ctx.curve_to(-0.5, -0.75, 0.5, -0.75, 0.55, -0.22); ctx.close_path(); ctx.set_source_rgba(0.1, 0.14, 0.28, alpha); ctx.fill()
        ctx.rectangle(-0.62, -0.28, 1.24, 0.1); ctx.set_source_rgba(0.05, 0.05, 0.08, alpha); ctx.fill()
        ctx.arc(0, -0.45, 0.08, 0, 2 * math.pi); rgba(ctx, ACCENT, alpha); ctx.fill()
    ctx.restore(); ctx.restore()

def eye(ctx, x, y, s, t, alpha=1.0):
    if s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.new_path(); ctx.move_to(-1, 0); ctx.curve_to(-0.5, -0.7, 0.5, -0.7, 1, 0); ctx.curve_to(0.5, 0.7, -0.5, 0.7, -1, 0); ctx.close_path()
    ctx.set_source_rgba(0.97, 0.97, 0.97, alpha); ctx.fill()
    px = 0.25 * math.sin(t * 2.2)
    ctx.arc(px, 0, 0.38, 0, 2 * math.pi); rgba(ctx, RED, alpha); ctx.fill()
    ctx.arc(px, 0, 0.17, 0, 2 * math.pi); ctx.set_source_rgba(0.05, 0.05, 0.05, alpha); ctx.fill()
    ctx.arc(px + 0.1, -0.1, 0.06, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, alpha); ctx.fill(); ctx.restore()

AUS = [(0.08, 0.38), (0.2, 0.25), (0.32, 0.2), (0.38, 0.1), (0.46, 0.12), (0.5, 0.05), (0.56, 0.12), (0.62, 0.2), (0.66, 0.1),
       (0.72, 0.0), (0.76, 0.12), (0.8, 0.28), (0.88, 0.38), (0.95, 0.5), (0.98, 0.62), (0.94, 0.78), (0.86, 0.9), (0.78, 0.95),
       (0.7, 0.9), (0.64, 0.82), (0.58, 0.74), (0.54, 0.79), (0.48, 0.7), (0.38, 0.68), (0.26, 0.72), (0.14, 0.78), (0.06, 0.74),
       (0.06, 0.6), (0.02, 0.5)]
def australia(ctx, x, y, s, alpha=1.0, fill=(0.95, 0.6, 0.2), pulse=0.0):
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x - s / 2, y - s * 0.45); ctx.scale(s, s * 0.9)
    ctx.new_path()
    for i, (px, py) in enumerate(AUS): (ctx.move_to if i == 0 else ctx.line_to)(px, py)
    ctx.close_path()
    ctx.set_source_rgba(fill[0], fill[1], fill[2], alpha * (0.85 + 0.15 * pulse)); ctx.fill_preserve()
    ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_width(0.012); ctx.set_source_rgba(1, 1, 1, 0.8 * alpha); ctx.stroke()
    ctx.arc(0.86, 1.03, 0.035, 0, 2 * math.pi); ctx.set_source_rgba(fill[0], fill[1], fill[2], alpha); ctx.fill()
    ctx.restore()

def bubble_icon(ctx, x, y, s, alpha=1.0):
    if s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rrect(ctx, -1, -0.75, 2, 1.4, 0.4); ctx.move_to(-0.5, 0.6); ctx.line_to(-0.7, 1.0); ctx.line_to(-0.1, 0.6); ctx.close_path()
    rgba(ctx, ACCENT, alpha); ctx.fill()
    for i in (-0.45, 0, 0.45): ctx.arc(i, -0.05, 0.13, 0, 2 * math.pi); rgba(ctx, NAVY, alpha); ctx.fill()
    ctx.restore()

# ---------------- scenes ----------------
def s_hook(ctx, t):  # 0–2.85 (texto + movimiento desde el cuadro 0)
    bg(ctx, t)
    sh = 10 * math.sin(t * 40) * clamp((t - 1.76) / 0.1) * (1 - clamp((t - 2.2) / 0.3))
    black_box(ctx, W / 2 + sh, 880 + 12 * math.sin(t * 3), 280, mix=0.0, rot=0.06 * math.sin(t * 2.4))
    text(ctx, "La CAJA NEGRA", W / 2, 330, 104, ACCENT, stroke=14)
    text(ctx, "NO es negra", W / 2, 460, 104, WHITE, stroke=14)
    cross(ctx, W / 2 + 250, 650, 70 * back((t - 1.76) / 0.35))
    if t > 2.2:
        k = back((t - 2.2) / 0.3)
        ctx.save(); ctx.translate(W / 2, 1180); ctx.scale(k, k); text(ctx, "?", 0, 0, 200, ORANGE, stroke=14); ctx.restore()

WRECK = [(170, 760, 70, 0.3), (900, 700, 90, 1.2), (220, 1080, 95, 2.1), (870, 1100, 75, 0.7), (520, 1180, 60, 2.8), (330, 560, 55, 1.7), (760, 520, 50, 0.4)]
def s_orange(ctx, t):  # 2.85–8.85
    sea = ease((t - 6.9) / 0.9)
    bg(ctx, t, sea=sea)
    mix = ease((t - 3.0) / 0.6)
    if 3.0 < t < 3.9:
        u = (t - 3.0) / 0.9
        ctx.set_line_width(10); ctx.set_source_rgba(1, 0.6, 0.2, 0.6 * (1 - u)); ctx.arc(W / 2, 860, 200 + 400 * u, 0, 2 * math.pi); ctx.stroke()
    wa = ease((t - 4.6) / 0.4)
    for i, (x, y, s, r) in enumerate(WRECK):
        if wa <= 0: break
        k = back((t - 4.6 - i * 0.06) / 0.4)
        wreck(ctx, x, y + sea * 60, s * k, r + 0.2 * math.sin(t + i), 1.0, i + 2)
    bs = lerp(250, 150, ease((t - 4.6) / 0.5)); by = 860 + sea * 220 + 10 * math.sin(t * 3)
    gl = (0.5 + 0.5 * math.sin(t * 6)) if t > 4.6 else 0.6 * mix
    black_box(ctx, W / 2, by, bs, mix=mix, rot=0.05 * math.sin(t * 2), glow_a=gl)
    if t < 4.6:
        header(ctx, "Es", "NARANJA", t, 3.0, size=96, c2=ORANGE)
        if t > 3.6: label(ctx, "NARANJA BRILLANTE", W / 2, 1160, 56, ORANGE_L, ease((t - 3.6) / 0.3))
    elif t < 6.9:
        header(ctx, "Para", "ENCONTRARLA", t, 4.6, size=74)
        if t > 5.9: label(ctx, "ENTRE LOS RESTOS", W / 2, 1310 - 100, 50, WHITE, ease((t - 5.9) / 0.3))
    else:
        header(ctx, "Incluso en el", "FONDO DEL MAR", t, 7.0, size=58, c2=BLUE)

def s_two(ctx, t):  # 8.85–17.25
    bg(ctx, t)
    k = back((t - 9.6) / 0.4)
    if t < 10.4:
        header(ctx, "En realidad son", "DOS", t, 8.9, size=80)
    else:
        header(ctx, "Voces +", "DATOS", t, 10.4, size=80)
    # left: cockpit voice recorder, right: flight data recorder
    black_box(ctx, lerp(W / 2, 290, k), 610, lerp(160, 140, k), rot=0.05 * math.sin(t * 2))
    if t > 9.6: black_box(ctx, lerp(W / 2, 790, k), 610, 140 * k, rot=-0.05 * math.sin(t * 2))
    if t > 9.88: pop_text(ctx, "2", W / 2, 610, 130, ACCENT, t, 9.88)
    if t > 10.5:
        a = ease((t - 10.5) / 0.3)
        mic(ctx, 150, 840, 55 * back((t - 10.5) / 0.35), a)
        waveform(ctx, 330, 840, 250, 110, t, a)
        label(ctx, "VOCES", 290, 980, 44, ACCENT, a)
    if t > 12.6:
        a = ease((t - 12.6) / 0.3)
        chart(ctx, 790, 840, 380 * clamp(back((t - 12.6) / 0.35), 0.01, 1.2), 150, t, a)
        label(ctx, "CIENTOS DE DATOS", 790, 980, 40, GREEN, ease((t - 13.3) / 0.3))
    for (t0, kind, x, name) in [(15.16, "alt", 210, "ALTURA"), (15.68, "spd", 540, "VELOCIDAD"), (16.56, "compass", 860, "RUMBO")]:
        if t < t0: continue
        r = 92 * back((t - t0) / 0.35); xx = x if kind != "compass" else 850
        gauge(ctx, xx, 1120 if kind != "compass" else 1120, r, kind, t)
        label(ctx, name, xx, 1240, 34, WHITE, ease((t - t0) / 0.3))

def s_tail(ctx, t):  # 17.25–21.25
    bg(ctx, t)
    fly = ease((t - 17.25) / 0.6)
    px = lerp(-500, W / 2 + 40, fly); py = 820 + 14 * math.sin(t * 2)
    tb = ease((t - 17.84) / 0.3)
    plane(ctx, px, py, 470, rot=-0.03, tail_box=tb, t=t)
    header(ctx, "Van en la", "COLA", t, 17.3, size=92)
    if t > 17.84:
        tx, ty = px - 0.8 * 470, py - 0.03 * 470 - 14
        ring = 60 + 12 * math.sin(t * 8)
        ctx.set_line_width(8); rgba(ctx, ACCENT, tb); ctx.arc(tx, ty, ring, 0, 2 * math.pi); ctx.stroke()
        arrow(ctx, tx + 40, ty - 230, tx + 8, ty - ring - 10, ACCENT, tb)
    if t > 19.6:
        a = ease((t - 19.6) / 0.3)
        label(ctx, "LA PARTE QUE MEJOR SOBREVIVE", W / 2, 1120, 44, GREEN, a)
        check(ctx, W / 2, 1250, 50 * back((t - 20.3) / 0.35))

def s_impact(ctx, t):  # 21.25–26.9
    hit = t - 23.84
    shake = (14 * math.sin(t * 55) * math.exp(-hit * 3)) if hit > 0 else 0
    bg(ctx, t, tint=(1, 1, 1, 0.5 * math.exp(-hit * 8)) if hit > 0 else None)
    if hit > 0:
        burst(ctx, W / 2, 820, 330 + 30 * math.sin(t * 10), 14, ACCENT, 0.25, rot=t * 0.3)
        burst(ctx, W / 2, 820, 250, 10, ORANGE, 0.3, rot=-t * 0.4)
    drop = 0 if hit > 0 else -260 * (1 - ease((t - 23.0) / 0.84)) if t > 23.0 else -260
    black_box(ctx, W / 2 + shake, 820 + drop + shake * 0.5, 200, rot=0.04 * math.sin(t * 3), glow_a=0.6)
    header(ctx, "Lo que", "AGUANTAN", t, 21.35, size=92)
    if hit > 0.4:
        n = int(round(3400 * ease((t - 24.3) / 1.3)))
        counter_box(ctx, W / 2, 1140, n, "G", ease((t - 24.2) / 0.3), size=150, sub=70)
    if t > 25.7:
        label(ctx, "VECES LA GRAVEDAD", W / 2, 1265, 46, WHITE, ease((t - 25.7) / 0.3))

def s_fire(ctx, t):  # 26.9–29.5
    bg(ctx, t, tint=(0.6, 0.12, 0.0, 0.25 + 0.05 * math.sin(t * 9)))
    glow(ctx, W / 2, 930, 520, ORANGE, 0.35)
    for i in range(9):
        x = 200 + i * 85; s = 120 + 60 * math.sin(i * 1.7) ** 2
        flame(ctx, x, 1020, s * ease((t - 26.9) / 0.4), t, i)
    black_box(ctx, W / 2, 880, 190, rot=0.03 * math.sin(t * 4), glow_a=0.4)
    for i in range(7):
        x = 250 + i * 95; flame(ctx, x, 1040, (90 + 30 * (i % 3)) * ease((t - 27.0) / 0.4), t, i + 11, 0.9)
    header(ctx, "", "FUEGO", t, 26.95, size=100, c2=ORANGE)
    if t > 27.5:
        n = int(round(1100 * ease((t - 27.5) / 0.6)))
        counter_box(ctx, W / 2, 520, n, "°C", ease((t - 27.5) / 0.2), size=130, sub=64)
    if t > 28.7:
        a = ease((t - 28.7) / 0.3)
        clock(ctx, 330, 1210, 60 * back((t - 28.7) / 0.35), t, a)
        label(ctx, "1 HORA", 560, 1210, 60, ACCENT, a)

def s_deep(ctx, t):  # 29.5–32.7
    bg(ctx, t, sea=1.0)
    dark = ease((t - 30.4) / 1.6)
    ctx.set_source_rgba(0, 0.01, 0.04, 0.55 * dark); ctx.paint()
    by = lerp(700, 900, ease((t - 29.5) / 2.5))
    black_box(ctx, W / 2 + 60, by, 165, rot=0.05 * math.sin(t * 1.5), glow_a=0.5)
    pa = ease((t - 29.7) / 0.3)
    if pa > 0:
        sq = 12 * math.sin(t * 6)
        for (dx, dy) in [(-1, 0), (1, 0), (0, -1), (0, 1), (-0.7, -0.7), (0.7, -0.7), (-0.7, 0.7), (0.7, 0.7)]:
            x0, y0 = W / 2 + 60 + dx * (330 + sq), by + dy * (280 + sq); x1, y1 = W / 2 + 60 + dx * 225, by + dy * 165
            arrow(ctx, x0, y0, x1, y1, BLUE, pa * 0.9, w=9, head=28)
    # depth bar (left)
    ctx.set_line_width(6); ctx.set_source_rgba(1, 1, 1, 0.6); ctx.move_to(110, 520); ctx.line_to(110, 1220); ctx.stroke()
    for k in range(7):
        y = 520 + k * 700 / 6; ctx.move_to(95, y); ctx.line_to(125, y); ctx.stroke()
    u = ease((t - 30.6) / 1.1); my = 520 + 700 * u
    ctx.new_path(); ctx.move_to(130, my); ctx.line_to(165, my - 20); ctx.line_to(165, my + 20); ctx.close_path(); rgba(ctx, ACCENT); ctx.fill()
    header(ctx, "La", "PRESIÓN", t, 29.6, size=90, c2=BLUE)
    if t > 30.6:
        counter_box(ctx, W / 2 + 60, 1250, f"{int(round(6000 * u))}", "m", ease((t - 30.6) / 0.2), size=120, sub=60)

def s_ping(ctx, t):  # 32.7–37.2
    bg(ctx, t, sea=1.0)
    ctx.set_source_rgba(0, 0.01, 0.04, 0.4); ctx.paint()
    # sea floor
    ctx.new_path(); ctx.move_to(0, H)
    for x in range(0, W + 40, 40): ctx.line_to(x, 1130 + 25 * math.sin(x / 130))
    ctx.line_to(W, H); ctx.close_path(); ctx.set_source_rgba(0.12, 0.1, 0.08, 1); ctx.fill()
    bx, by = W / 2, 1060
    if t > 33.9:
        for k in range(4):
            ph = ((t - 33.9) * 0.8 + k / 4) % 1
            ctx.set_line_width(8 * (1 - ph) + 2); ctx.set_source_rgba(1, 0.75, 0.3, 0.8 * (1 - ph))
            ctx.arc(bx - 150, by, 40 + ph * 520, 0, 2 * math.pi); ctx.stroke()
        if int((t - 33.9) * 2.4) % 2 == 0: label(ctx, "PIP", bx - 300, by - 170, 44, ACCENT, 1.0)
    black_box(ctx, bx, by, 120, rot=0.15, glow_a=0.6)
    header(ctx, "Si cae al", "AGUA", t, 32.75, size=90, c2=BLUE)
    if t > 35.1:
        n = int(round(90 * ease((t - 35.1) / 0.6)))
        counter_box(ctx, W / 2, 560, n, "DÍAS", ease((t - 35.1) / 0.2), size=150, sub=60)
    if t > 36.1:
        a = ease((t - 36.1) / 0.4)
        bxx = lerp(W + 150, 900, a)
        ctx.save(); ctx.rectangle(0, 0, W, 760); ctx.clip()
        boat(ctx, bxx, 430 - 8 + 6 * math.sin(t * 2), 90, 1.0); ctx.restore()
        ctx.set_dash([14, 14]); ctx.set_line_width(5); ctx.set_source_rgba(1, 1, 1, 0.7 * a)
        ctx.move_to(bxx, 480); ctx.line_to(bx + 40, by - 80); ctx.stroke(); ctx.set_dash([])

def s_inventor(ctx, t):  # 37.2–43.95
    sad = ease((t - 41.45) / 0.4)
    bg(ctx, t, tint=(0.05, 0.05, 0.08, 0.35 * sad))
    if t < 38.6:
        header(ctx, "¿Quién la", "INVENTÓ?", t, 37.25, size=90)
        k = back((t - 37.3) / 0.4)
        ctx.save(); ctx.translate(W / 2, 850); ctx.scale(k, k); ctx.rotate(0.12 * math.sin(t * 3)); text(ctx, "?", 0, 0, 420, ACCENT, stroke=18); ctx.restore()
        return
    if t < 41.45: header(ctx, "Un científico", "AUSTRALIANO", t, 38.65, size=66)
    else: header(ctx, "Su", "PADRE...", t, 41.45, size=90, c2=RED)
    ma = ease((t - 38.65) / 0.4) * (1 - ease((t - 40.3) / 0.35))
    australia(ctx, W / 2, 820, 620 * (0.9 + 0.1 * ease((t - 38.65) / 0.4)), ma, pulse=math.sin(t * 5))
    if ma > 0: label(ctx, "AUSTRALIA", W / 2, 1180, 54, ACCENT, ma)
    if t > 40.3:
        pa = 1 - sad * 0.65
        px = lerp(W / 2, 290, sad); ps = lerp(150, 110, sad)
        person(ctx, px, 720, ps * back((t - 40.3) / 0.4), pa, glasses=True)
        label(ctx, "DAVID WARREN", px if sad < 0.5 else 290, 1000 if sad < 0.5 else 960, 56 if sad < 0.5 else 38, ACCENT, ease((t - 40.4) / 0.3) * (1 - 0.3 * sad))
    if t > 41.45:
        u = clamp((t - 41.45) / 2.3)
        fx, fy = lerp(560, 900, u), lerp(560, 960, u * u)
        for k in range(10):
            uu = max(0, u - k * 0.025); sx, sy = lerp(560, 900, uu), lerp(560, 960, uu * uu)
            ctx.set_source_rgba(0.6, 0.6, 0.65, 0.35 * sad * (1 - k / 10)); ctx.arc(sx - 40, sy - 20, 18 + k * 3, 0, 2 * math.pi); ctx.fill()
        plane(ctx, fx, fy, 170, alpha=sad, rot=0.5 + 0.6 * u)


def s_reject(ctx, t):  # 43.95–49.95
    bg(ctx, t)
    spy = ease((t - 46.65) / 0.4)
    for i, x in enumerate((250, 540, 830)):
        k = back((t - 44.0 - i * 0.12) / 0.4)
        sh = 0.18 * math.sin(t * 14 + i) if t > 45.1 else 0.0
        person(ctx, x, lerp(700, 620, spy), 120 * k, cap=True, shake=sh, color=(0.25, 0.3, 0.5))
    if t < 46.65:
        header(ctx, "Los", "PILOTOS", t, 44.95, size=84)
        stamp(ctx, "RECHAZADA", W / 2, 1050, 96, RED, t, 45.68)
    else:
        header(ctx, "¿Alguien", "ESPIÁNDONOS?", t, 46.7, size=68, c2=RED)
        black_box(ctx, W / 2 - 230, 1010, 120 * back((t - 46.8) / 0.4), rot=-0.1)
        eye(ctx, W / 2 + 200, 1010, 150 * back((t - 47.0) / 0.4), t)
        if t > 48.6: label(ctx, "NINGÚN AVIÓN DESPEGARÍA", W / 2, 1210, 44, WHITE, ease((t - 48.6) / 0.3))

def s_law(ctx, t):  # 49.95–54.05
    bg(ctx, t)
    if t < 51.0:
        header(ctx, "Años", "DESPUÉS...", t, 50.0, size=90)
    else:
        header(ctx, "", "AUSTRALIA", t, 51.0, size=100)
    a = ease((t - 50.9) / 0.4)
    australia(ctx, W / 2, 720, 560 * (0.92 + 0.08 * a), a, fill=(0.95, 0.75, 0.2), pulse=math.sin(t * 5))
    if t < 51.0:
        k = back((t - 50.0) / 0.4)
        if k > 0: clock(ctx, W / 2, 720, 160 * k, t * 6, 1 - a)
    if t > 51.95:
        pop_text(ctx, "1.º", W / 2 + 40, 720, 190, NAVY, t, 51.95, stroke=0)
        label(ctx, "PRIMER PAÍS", W / 2, 1090, 58, WHITE, ease((t - 51.95) / 0.3))
    stamp(ctx, "OBLIGATORIA", W / 2, 1215, 76, GREEN, t, 53.1, rot=-0.08)

def s_ask(ctx, t):  # 54.05–55.9
    bg(ctx, t)
    pop_text(ctx, "¿SABÍAS QUE", W / 2, 470, 100, WHITE, t, 54.08)
    pop_text(ctx, "ERA NARANJA?", W / 2, 600, 100, ORANGE, t, 54.25)
    black_box(ctx, W / 2, 880, 190 * back((t - 54.1) / 0.4), rot=0.08 * math.sin(t * 4), glow_a=0.7)
    bubble_icon(ctx, W / 2, 1150, 80 * back((t - 55.0) / 0.35))

def s_end(ctx, t):  # 55.9–end
    bg(ctx, t)
    a = ease((t - 55.9) / 0.5)
    black_box(ctx, 380, 1500, 110, alpha=a, rot=-0.08 + 0.04 * math.sin(t * 2), glow_a=0.5)
    plane(ctx, 760, 1480, 200, alpha=a, rot=-0.08 + 0.03 * math.sin(t * 2))
    sc = 0.85 + 0.15 * back((t - 55.9) / 0.5); s = 300 * sc
    logo_mark(ctx, (W - s) / 2, 470 + (300 - s) / 2, s, a)
    w1 = text_w(ctx, "Logi", 120); w2 = text_w(ctx, "Datos", 120); x0 = (W - w1 - w2) / 2
    text(ctx, "Logi", x0, 900, 120, WHITE, align="left", alpha=a); text(ctx, "Datos", x0 + w1, 900, 120, ACCENT, align="left", alpha=a)
    text(ctx, "Curiosidades con lógica y datos", W / 2, 1010, 48, hexc("C8CEE0"), bold=False, alpha=a)
    pa = back((t - 56.3) / 0.4)
    if pa > 0:
        ctx.save(); ctx.translate(W / 2, 1150); ctx.scale(pa, pa)
        pw = text_w(ctx, "SÍGUENOS", 54) + 100; rrect(ctx, -pw / 2, -52, pw, 104, 52); rgba(ctx, ACCENT); ctx.fill()
        text(ctx, "SÍGUENOS", 0, 0, 54, NAVY); ctx.restore()

SCENES = [(0.0, s_hook), (2.85, s_orange), (8.85, s_two), (17.25, s_tail), (21.25, s_impact), (26.9, s_fire), (29.5, s_deep),
          (32.7, s_ping), (37.2, s_inventor), (43.95, s_reject), (49.95, s_law), (54.05, s_ask), (55.9, s_end)]
END_START = 55.9

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
EMPH = {"NEGRA", "NARANJA", "MAR", "DOS", "VOCES", "DATOS", "COLA", "CHOQUE", "CUATROCIENTAS", "GRAVEDAD", "FUEGO", "HORA",
        "PROFUNDIDAD", "NOVENTA", "DÍAS", "WARREN", "PADRE", "RECHAZARON", "ESPIÁNDOLOS", "AUSTRALIA", "PRIMER", "OBLIGATORIA"}
def clean(s): return s.replace("…", "").replace("¿", "").rstrip(".,;:?!…").upper()

CAP_Y, CAP_SIZE = 1400, 86
def captions(ctx, t):
    if t < 2.85: return  # el gancho ya está escrito en pantalla
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
