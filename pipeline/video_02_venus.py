#!/usr/bin/env python3
"""LogiDatos Short #2 – Venus: un día más largo que un año. Motion graphics drawn in code (cairo).
python3 motion.py [preview t1 t2 ...]"""
import json, math, os, random, subprocess, sys
import cairo

W, H, FPS = 1080, 1920, 30
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "build"); os.makedirs(OUT, exist_ok=True)
AUDIO = os.path.join(BASE, "dl/voz.mp3")
WORDS = [w for w in json.load(open(os.path.join(BASE, "dl/words.json")))["words"] if w.get("type", "word") == "word"]
TOTAL = 42.0
FINAL = os.path.join(BASE, "LogiDatos_02_venus_dia_mas_largo.mp4")

def hexc(h, a=1.0):
    h = h.lstrip("#"); return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)
ACCENT = hexc("FFD23F"); NAVY = hexc("0B1020"); WHITE = hexc("F5F3EA")
VEN = hexc("E9B96A"); VEN_L = hexc("FBE7B5"); VEN_D = hexc("9A5E25")
SUN = hexc("FFC93C"); SUN_D = hexc("FF7A1A")
BLUE = hexc("3DA9FC"); RED = hexc("E0393E"); GREEN = hexc("37E08F"); GRAY = hexc("9AA0AA")
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
    w = text_w(ctx, s, size)
    if bg:
        rrect(ctx, x - w / 2 - 26, y - size * 0.75, w + 52, size * 1.5, size * 0.5); ctx.set_source_rgba(0.03, 0.03, 0.09, 0.75 * alpha); ctx.fill()
    text(ctx, s, x, y, size, color, alpha=alpha)

def header(ctx, s1, s2, t, t0, y=300, size=66, alpha=1.0):
    a = ease((t - t0) / 0.35) * alpha
    if a <= 0: return
    ctx.save(); ctx.translate(0, (1 - ease((t - t0) / 0.35)) * 30)
    w1 = text_w(ctx, s1 + " ", size); w2 = text_w(ctx, s2, size); x0 = (W - w1 - w2) / 2
    text(ctx, s1, x0, y, size, WHITE, stroke=10, align="left", alpha=a)
    text(ctx, s2, x0 + w1, y, size, ACCENT, stroke=10, align="left", alpha=a)
    ctx.restore()

def arrow_arc(ctx, x, y, r, a0, a1, color, width=12, alpha=1.0, head=34):
    """Circular arc from a0 to a1 (radians, cairo convention) with an arrowhead at a1."""
    rgba(ctx, color, alpha); ctx.set_line_width(width); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.new_path()
    if a1 >= a0: ctx.arc(x, y, r, a0, a1)
    else: ctx.arc_negative(x, y, r, a0, a1)
    ctx.stroke()
    d = 1 if a1 >= a0 else -1
    px, py = x + r * math.cos(a1), y + r * math.sin(a1)
    tx, ty = -math.sin(a1) * d, math.cos(a1) * d  # tangent direction of travel
    nx, ny = math.cos(a1), math.sin(a1)
    ctx.new_path(); ctx.move_to(px + tx * head * 0.9, py + ty * head * 0.9)
    ctx.line_to(px - tx * head * 0.3 + nx * head * 0.6, py - ty * head * 0.3 + ny * head * 0.6)
    ctx.line_to(px - tx * head * 0.3 - nx * head * 0.6, py - ty * head * 0.3 - ny * head * 0.6); ctx.close_path()
    rgba(ctx, color, alpha); ctx.fill()

# ---------------- background ----------------
random.seed(11)
STARS = [(random.random(), random.random(), random.uniform(1.0, 3.6), random.random()) for _ in range(170)]

def space(ctx, t):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, 0.05, 0.04, 0.14); g.add_color_stop_rgb(0.5, 0.03, 0.03, 0.09); g.add_color_stop_rgb(1, 0.01, 0.01, 0.04)
    ctx.set_source(g); ctx.paint()
    glow(ctx, 220 + 40 * math.sin(t * 0.2), 520, 620, hexc("6B2FA3"), 0.22)
    glow(ctx, 900, 1250 + 30 * math.sin(t * 0.15), 700, hexc("1C6E8C"), 0.18)
    for (x, y, r, ph) in STARS:
        xx = (x * W - t * r * 3) % W; a = 0.35 + 0.45 * (0.5 + 0.5 * math.sin(t * 2.2 + ph * 20))
        ctx.set_source_rgba(1, 1, 0.95, a); ctx.arc(xx, y * H, r, 0, 2 * math.pi); ctx.fill()

# ---------------- bodies ----------------
def venus(ctx, x, y, r, t, spin=0.0, flag=None, alpha=1.0, halo=True, dark=0.0):
    if halo: glow(ctx, x, y, r * 1.45, hexc("FFC46B"), 0.33 * alpha * (1 - dark))
    ctx.save(); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.clip()
    g = cairo.RadialGradient(x - 0.35 * r, y - 0.35 * r, r * 0.05, x, y, r * 1.05)
    g.add_color_stop_rgba(0, VEN_L[0], VEN_L[1], VEN_L[2], alpha); g.add_color_stop_rgba(0.55, VEN[0], VEN[1], VEN[2], alpha)
    g.add_color_stop_rgba(1, VEN_D[0], VEN_D[1], VEN_D[2], alpha)
    ctx.set_source(g); ctx.paint()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(11):
        yk = y + (k - 5) / 5.4 * r
        light = k % 2 == 0
        ctx.set_source_rgba(1, 0.96, 0.85, 0.22 * alpha) if light else ctx.set_source_rgba(0.55, 0.3, 0.1, 0.22 * alpha)
        ctx.set_line_width(r * (0.07 + 0.03 * (k % 3)))
        ctx.new_path()
        for i in range(41):
            xx = x - r + 2 * r * i / 40
            yy = yk + math.sin((xx - x) / r * 2.6 + k * 1.7 + spin) * r * 0.06 + math.sin((xx - x) / r * 6 + k + spin * 2) * r * 0.015
            (ctx.move_to if i == 0 else ctx.line_to)(xx, yy)
        ctx.stroke()
    if flag is not None and math.cos(flag) > 0:
        c = math.cos(flag); px = x + r * 0.92 * math.sin(flag); py = y - r * 0.08
        ctx.set_source_rgba(0.15, 0.1, 0.08, alpha); ctx.set_line_width(max(3, r * 0.025))
        ctx.move_to(px, py); ctx.line_to(px, py - r * 0.32); ctx.stroke()
        ctx.new_path(); ctx.move_to(px, py - r * 0.32); ctx.line_to(px + r * 0.2 * c, py - r * 0.26); ctx.line_to(px, py - r * 0.2); ctx.close_path()
        rgba(ctx, RED, alpha); ctx.fill()
        ctx.set_source_rgba(0.15, 0.1, 0.08, alpha); ctx.arc(px, py, r * 0.03, 0, 2 * math.pi); ctx.fill()
    sh = cairo.LinearGradient(x - r, y - r, x + r, y + r)
    sh.add_color_stop_rgba(0, 0, 0, 0, 0); sh.add_color_stop_rgba(0.55, 0, 0, 0, 0.08 * alpha); sh.add_color_stop_rgba(1, 0, 0, 0, 0.55 * alpha)
    ctx.set_source(sh); ctx.paint()
    if dark > 0: ctx.set_source_rgba(0.02, 0.02, 0.06, dark * alpha); ctx.paint()
    ctx.restore()

def sun(ctx, x, y, r, t, alpha=1.0, rays=True):
    glow(ctx, x, y, r * 2.4, SUN_D, 0.35 * alpha); glow(ctx, x, y, r * 1.5, SUN, 0.5 * alpha)
    if rays:
        ctx.save(); ctx.translate(x, y); ctx.rotate(t * 0.25)
        for k in range(12):
            ctx.rotate(math.pi / 6); L = r * (1.28 + 0.08 * math.sin(t * 3 + k))
            ctx.new_path(); ctx.move_to(r * 1.05, -r * 0.09); ctx.line_to(L, 0); ctx.line_to(r * 1.05, r * 0.09); ctx.close_path()
            rgba(ctx, SUN, 0.85 * alpha); ctx.fill()
        ctx.restore()
    g = cairo.RadialGradient(x - r * 0.3, y - r * 0.3, r * 0.1, x, y, r)
    g.add_color_stop_rgba(0, 1, 0.98, 0.8, alpha); g.add_color_stop_rgba(0.6, SUN[0], SUN[1], SUN[2], alpha); g.add_color_stop_rgba(1, SUN_D[0], SUN_D[1], SUN_D[2], alpha)
    ctx.set_source(g); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.fill()

def earth(ctx, x, y, r, rot=0.0, alpha=1.0):
    glow(ctx, x, y, r * 1.35, BLUE, 0.25 * alpha)
    ctx.save(); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.clip()
    g = cairo.RadialGradient(x - 0.3 * r, y - 0.3 * r, r * 0.1, x, y, r)
    g.add_color_stop_rgba(0, 0.45, 0.75, 1, alpha); g.add_color_stop_rgba(1, 0.06, 0.25, 0.6, alpha); ctx.set_source(g); ctx.paint()
    ctx.translate(x, y); ctx.rotate(rot)
    for (ax, ay, s) in [(-0.35, -0.3, 0.38), (0.4, 0.1, 0.3), (-0.1, 0.45, 0.25), (0.15, -0.55, 0.2)]:
        ctx.save(); ctx.translate(ax * r, ay * r); ctx.scale(1, 0.7); ctx.arc(0, 0, s * r, 0, 2 * math.pi); ctx.restore()
        ctx.set_source_rgba(0.25, 0.72, 0.38, alpha); ctx.fill()
    ctx.restore()
    ctx.save(); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.clip()
    sh = cairo.LinearGradient(x - r, y - r, x + r, y + r); sh.add_color_stop_rgba(0.5, 0, 0, 0, 0); sh.add_color_stop_rgba(1, 0, 0, 0, 0.5 * alpha)
    ctx.set_source(sh); ctx.paint(); ctx.restore()

def mercury(ctx, x, y, r, alpha=1.0):
    g = cairo.RadialGradient(x - 0.3 * r, y - 0.3 * r, r * 0.1, x, y, r)
    g.add_color_stop_rgba(0, 0.82, 0.8, 0.78, alpha); g.add_color_stop_rgba(1, 0.35, 0.34, 0.33, alpha)
    ctx.set_source(g); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.fill()
    for (cx, cy, cr) in [(-0.3, -0.2, 0.18), (0.25, 0.3, 0.14), (0.35, -0.35, 0.1), (-0.15, 0.4, 0.09)]:
        ctx.set_source_rgba(0.25, 0.24, 0.24, 0.5 * alpha); ctx.arc(x + cx * r, y + cy * r, cr * r, 0, 2 * math.pi); ctx.fill()

def thermo(ctx, x, y_top, h, level, alpha=1.0, w=44, hot=RED):
    """Thermometer: tube from y_top, bulb at bottom. level 0..1."""
    br = w * 0.95; yb = y_top + h
    ctx.set_source_rgba(1, 1, 1, 0.9 * alpha); rrect(ctx, x - w / 2 - 8, y_top - 8, w + 16, h + 8, (w + 16) / 2); ctx.fill()
    ctx.arc(x, yb, br + 8, 0, 2 * math.pi); ctx.fill()
    ctx.set_source_rgba(0.12, 0.12, 0.18, alpha); rrect(ctx, x - w / 2, y_top, w, h, w / 2); ctx.fill(); ctx.arc(x, yb, br, 0, 2 * math.pi); ctx.fill()
    lv = y_top + h - (h - w / 2) * clamp(level)
    rgba(ctx, hot, alpha); rrect(ctx, x - w / 2 + 8, lv, w - 16, yb - lv, (w - 16) / 2); ctx.fill(); ctx.arc(x, yb, br - 8, 0, 2 * math.pi); ctx.fill()
    for k in range(1, 5):
        yy = y_top + h * k / 5; ctx.set_source_rgba(0.12, 0.12, 0.18, alpha); ctx.set_line_width(4)
        ctx.move_to(x + w / 2 + 8, yy); ctx.line_to(x + w / 2 + 26, yy); ctx.stroke()

def counter_box(ctx, x, y, n, unit, alpha=1.0, color=ACCENT, size=140, sub=46):
    if alpha <= 0: return
    s = str(n); wn = text_w(ctx, s, size); wu = text_w(ctx, " " + unit, sub); tot = wn + wu
    rrect(ctx, x - tot / 2 - 40, y - size * 0.62, tot + 80, size * 1.24, 36); ctx.set_source_rgba(0.03, 0.03, 0.09, 0.78 * alpha); ctx.fill()
    text(ctx, s, x - tot / 2, y, size, color, align="left", alpha=alpha)
    text(ctx, " " + unit, x - tot / 2 + wn, y + size * 0.18, sub, WHITE, align="left", alpha=alpha)

def co2(ctx, x, y, s, rot, alpha):
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot)
    for sx in (-1, 1):
        ctx.set_source_rgba(0.95, 0.95, 0.95, 0.6 * alpha); ctx.set_line_width(s * 0.18); ctx.move_to(0, 0); ctx.line_to(sx * s * 0.9, 0); ctx.stroke()
    for sx in (-1, 1):
        g = cairo.RadialGradient(sx * s - s * 0.15, -s * 0.15, 1, sx * s, 0, s * 0.5)
        g.add_color_stop_rgba(0, 1, 0.55, 0.55, alpha); g.add_color_stop_rgba(1, 0.75, 0.12, 0.15, alpha); ctx.set_source(g)
        ctx.arc(sx * s, 0, s * 0.5, 0, 2 * math.pi); ctx.fill()
    g = cairo.RadialGradient(-s * 0.15, -s * 0.15, 1, 0, 0, s * 0.55)
    g.add_color_stop_rgba(0, 0.55, 0.55, 0.58, alpha); g.add_color_stop_rgba(1, 0.12, 0.12, 0.14, alpha); ctx.set_source(g)
    ctx.arc(0, 0, s * 0.55, 0, 2 * math.pi); ctx.fill()
    ctx.restore()

def co2_label(ctx, x, y, size, alpha):
    w1 = text_w(ctx, "CO", size); w2 = text_w(ctx, "2", size * 0.6); x0 = x - (w1 + w2) / 2
    rrect(ctx, x0 - 24, y - size * 0.75, w1 + w2 + 48, size * 1.5, size * 0.5); ctx.set_source_rgba(0.03, 0.03, 0.09, 0.75 * alpha); ctx.fill()
    text(ctx, "CO", x0, y, size, WHITE, align="left", alpha=alpha); text(ctx, "2", x0 + w1 + 2, y + size * 0.28, size * 0.6, WHITE, align="left", alpha=alpha)

# ---------------- scenes ----------------
def s_hook(ctx, t):  # 0–3.75
    space(ctx, t)
    x, y, r = W / 2, 600, 230
    a = ease(t / 0.4)
    glow(ctx, x, y, r * 1.35, hexc("FFC46B"), 0.18 * a)
    venus(ctx, x, y, r, t * 0.3, halo=False, dark=0.82, alpha=a)
    ctx.set_source_rgba(1, 0.85, 0.5, 0.7 * a); ctx.set_line_width(5); ctx.arc(x, y, r, math.radians(200), math.radians(320)); ctx.stroke()
    q = back((t - 0.9) / 0.4)
    if q > 0:
        ctx.save(); ctx.translate(x, y); ctx.scale(q, q); ctx.rotate(0.08 * math.sin(t * 3))
        text(ctx, "?", 0, 0, 260, ACCENT, stroke=14); ctx.restore()
    # bar race: DAY vs YEAR
    bx = 300; maxw = 640
    da = ease((t - 1.95) / 0.3)
    if da > 0:
        dl = lerp(0, 0.55, ease((t - 2.0) / 0.6)) + lerp(0, 0.45, ease((t - 3.35) / 0.35))
        text(ctx, "1 DÍA", bx - 30, 940, 52, WHITE, stroke=8, align="right", alpha=da)
        rrect(ctx, bx, 905, max(70, maxw * dl), 70, 35); rgba(ctx, ACCENT, da); ctx.fill()
    ya = ease((t - 3.15) / 0.3)
    if ya > 0:
        yl = 0.78 * ease((t - 3.15) / 0.35)
        text(ctx, "1 AÑO", bx - 30, 1040, 52, WHITE, stroke=8, align="right", alpha=ya)
        rrect(ctx, bx, 1005, max(70, maxw * yl), 70, 35); rgba(ctx, BLUE, ya); ctx.fill()

def s_reveal(ctx, t):  # 3.75–5.1
    space(ctx, t)
    u = ease((t - 3.75) / 0.8)
    venus(ctx, W / 2, lerp(600, 640, u), lerp(230, 300, u), t * 0.3, dark=lerp(0.82, 0, u))
    header(ctx, "Es", "VENUS", t, 4.25, y=250, size=96)

def s_rotate(ctx, t):  # 5.1–10.9
    space(ctx, t); x, y, r = W / 2, 680, 260
    p = ease((t - 6.25) / 3.9)
    flag = -2 * math.pi * p + 0.0
    venus(ctx, x, y, r, -p * 8, flag=flag)
    a = ease((t - 5.6) / 0.4)
    if a > 0:
        a0 = -math.pi / 2 - 0.9; arrow_arc(ctx, x, y, r + 50, a0 + 1.8, a0, ACCENT, 12, a)
    header(ctx, "1 DÍA", "en Venus", t, 5.15, y=260)
    ca = ease((t - 6.2) / 0.3)
    counter_box(ctx, x, 1040, int(round(243 * p)), "días", ca)
    if t > 10.15:
        k = back((t - 10.15) / 0.3); glow(ctx, x, 1040, 300 * k, ACCENT, 0.25 * (1 - ease((t - 10.4) / 0.5)))

def orbit_pos(ang, cx, cy, rx, ry): return cx + rx * math.cos(ang), cy + ry * math.sin(ang)

def s_orbit(ctx, t):  # 10.9–15.45
    space(ctx, t); cx, cy, rx, ry = W / 2, 640, 390, 230
    p = ease((t - 11.4) / 2.5)
    ang = math.pi / 2 - 2 * math.pi * p  # starts at bottom, goes counter-clockwise around the Sun
    ctx.set_source_rgba(1, 1, 1, 0.25); ctx.set_line_width(4); ctx.set_dash([14, 14])
    ctx.save(); ctx.translate(cx, cy); ctx.scale(rx, ry); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); ctx.stroke(); ctx.set_dash([])
    if p > 0:  # trail
        ctx.set_source_rgba(1, 0.82, 0.25, 0.85); ctx.set_line_width(8); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.new_path()
        for i in range(61):
            a = math.pi / 2 - 2 * math.pi * p * i / 60; px, py = orbit_pos(a, cx, cy, rx, ry)
            (ctx.move_to if i == 0 else ctx.line_to)(px, py)
        ctx.stroke()
    vx, vy = orbit_pos(ang, cx, cy, rx, ry)
    behind = math.sin(ang) < 0
    if behind: venus(ctx, vx, vy, 62, t)
    sun(ctx, cx, cy, 120, t)
    if not behind: venus(ctx, vx, vy, 62, t)
    header(ctx, "1 AÑO", "en Venus", t, 10.95, y=260)
    ca = ease((t - 11.35) / 0.3) * (1 - ease((t - 13.95) / 0.25))
    counter_box(ctx, cx, 1040, int(round(225 * p)), "días", ca, color=BLUE)
    ka = back((t - 14.05) / 0.4)
    if ka > 0:
        ctx.save(); ctx.translate(cx, 1040); ctx.scale(ka, ka)
        rrect(ctx, -430, -95, 860, 190, 40); ctx.set_source_rgba(0.03, 0.03, 0.09, 0.82); ctx.fill()
        text(ctx, "DÍA", -270, -50, 40, WHITE); text(ctx, "243", -270, 25, 96, ACCENT)
        text(ctx, ">", 0, 0, 120, WHITE, stroke=8)
        text(ctx, "AÑO", 270, -50, 40, WHITE); text(ctx, "225", 270, 25, 96, BLUE)
        ctx.restore()

def s_spin(ctx, t):  # 15.45–17.3
    space(ctx, t); y = 680; r = 150
    a = ease((t - 15.45) / 0.35)
    ex, vx = 290, 790
    earth(ctx, ex, y, r, rot=-t * 1.6, alpha=a)
    ctx.save(); ctx.translate(vx, y); ctx.rotate(t * 1.6); ctx.translate(-vx, -y); venus(ctx, vx, y, r, 0, alpha=a); ctx.restore()
    sw = (t * 1.6) % (2 * math.pi)
    arrow_arc(ctx, ex, y, r + 45, -sw + 1.9, -sw, GREEN, 11, a)
    hot = ease((t - 16.4) / 0.3)
    arrow_arc(ctx, vx, y, r + 45, sw - 1.9, sw, RED if hot > 0.5 else WHITE, 11, a)
    label(ctx, "TIERRA", ex, y + r + 120, 44, WHITE, a); label(ctx, "VENUS", vx, y + r + 120, 44, ACCENT, a)
    if hot > 0: label(ctx, "AL REVÉS", vx, y - r - 120, 44, RED, hot)
    header(ctx, "Venus gira", "al revés", t, 15.5, y=260)

def s_sunrise(ctx, t):  # 17.3–21.0
    sky = cairo.LinearGradient(0, 0, 0, 1000)
    sky.add_color_stop_rgb(0, 0.30, 0.13, 0.06); sky.add_color_stop_rgb(0.6, 0.72, 0.40, 0.14); sky.add_color_stop_rgb(1, 0.95, 0.66, 0.30)
    ctx.set_source(sky); ctx.paint()
    hor = 1000
    u = ease((t - 18.0) / 2.6); ang = math.pi * (1 - u)  # 180° (west, left) → 0° (east, right)
    sx, sy = W / 2 + 430 * math.cos(ang), hor - 520 * math.sin(ang)
    ctx.set_source_rgba(1, 0.95, 0.7, 0.45); ctx.set_line_width(5); ctx.set_dash([16, 16]); ctx.new_path()
    for i in range(41):
        aa = math.pi * (1 - i / 40); px, py = W / 2 + 430 * math.cos(aa), hor - 520 * math.sin(aa)
        (ctx.move_to if i == 0 else ctx.line_to)(px, py)
    ctx.stroke(); ctx.set_dash([])
    sun(ctx, sx, sy, 78, t)
    # haze bands
    for k in range(5):
        yy = 380 + k * 120 + 10 * math.sin(t * 0.7 + k); ctx.set_source_rgba(1, 0.85, 0.55, 0.06)
        ctx.rectangle(0, yy, W, 50); ctx.fill()
    # ground
    ctx.new_path(); ctx.move_to(0, hor)
    for i in range(0, W + 1, 20): ctx.line_to(i, hor - 30 * math.sin(i * 0.006) - 18 * math.sin(i * 0.021 + 1))
    ctx.line_to(W, H); ctx.line_to(0, H); ctx.close_path()
    gg = cairo.LinearGradient(0, hor - 60, 0, H); gg.add_color_stop_rgb(0, 0.55, 0.27, 0.10); gg.add_color_stop_rgb(1, 0.18, 0.08, 0.03)
    ctx.set_source(gg); ctx.fill()
    # volcano
    ctx.new_path(); ctx.move_to(600, hor - 5); ctx.curve_to(700, hor - 40, 740, hor - 150, 765, hor - 185)
    ctx.line_to(815, hor - 185); ctx.curve_to(840, hor - 150, 880, hor - 40, 990, hor - 5); ctx.close_path()
    ctx.set_source_rgb(0.38, 0.17, 0.07); ctx.fill()
    random.seed(5)
    for _ in range(40):
        ctx.set_source_rgba(0.25, 0.1, 0.03, 0.6); ctx.arc(random.uniform(0, W), random.uniform(hor + 40, 1500), random.uniform(3, 9), 0, 2 * math.pi); ctx.fill()
    wa = ease((t - 18.9) / 0.3); ea = ease((t - 20.35) / 0.3)
    if wa > 0: label(ctx, "← OESTE", 190, hor + 60, 44, ACCENT, wa)
    if ea > 0: label(ctx, "ESTE →", W - 180, hor + 60, 44, ACCENT, ea)
    if t < 19.6: header(ctx, "El Sol sale por el", "OESTE", t, 18.3, y=260, size=62)
    else: header(ctx, "y se oculta por el", "ESTE", t, 19.6, y=260, size=62)

def s_hot(ctx, t):  # 21.0–26.3
    space(ctx, t); y = 650
    sun(ctx, -150, y, 300, t)
    ma = back((t - 21.2) / 0.4); va = back((t - 21.45) / 0.4); ea = back((t - 21.7) / 0.4)
    if ma > 0: mercury(ctx, 360, y, 42 * ma)
    if va > 0: venus(ctx, 600, y, 78 * va, t)
    if ea > 0: earth(ctx, 870, y, 72 * ea, rot=t * 0.3)
    hm = ease((t - 22.0) / 0.3)
    if hm > 0:
        label(ctx, "MERCURIO", 360, y - 150, 36, WHITE, hm)
        ctx.set_source_rgba(1, 1, 1, 0.6 * hm); ctx.set_line_width(4); ctx.move_to(360, y - 120); ctx.line_to(360, y - 55); ctx.stroke()
    if ea > 0: label(ctx, "TIERRA", 870, y + 140, 34, WHITE, clamp(ea), bg=True)
    vl = ease((t - 24.0) / 0.3)
    if vl > 0:
        label(ctx, "VENUS", 600, y + 140, 36, ACCENT, vl)
    ta = ease((t - 22.3) / 0.3)
    if ta > 0:
        thermo(ctx, 360, 860, 170, 0.5 * ease((t - 22.4) / 0.8), ta, w=40, hot=SUN_D)
        lvl = 0.5 * ease((t - 22.4) / 0.8) + 0.5 * ease((t - 25.3) / 0.6)
        thermo(ctx, 600, 860, 170, lvl, ta, w=40)
    if t > 25.45:
        k = ease((t - 25.45) / 0.3)
        for i in range(6):
            ph = (t * 0.9 + i / 6) % 1; ctx.set_source_rgba(1, 0.4, 0.15, 0.7 * k * math.sin(ph * math.pi))
            ctx.arc(600 + 50 * math.sin(i * 2.3 + t * 3), y - 90 - ph * 160, 10 + 8 * ph, 0, 2 * math.pi); ctx.fill()
    if t < 24.0: header(ctx, "Mercurio:", "más cerca", t, 22.0, y=260)
    else: header(ctx, "Venus:", "MÁS CALIENTE", t, 24.4, y=260)

random.seed(21)
MOLS = [(random.uniform(0, 2 * math.pi), random.uniform(0.15, 0.85), random.uniform(-0.3, 0.3), random.random()) for _ in range(9)]
HEAT = [(random.uniform(0, 2 * math.pi), random.uniform(0.6, 1.2), random.random()) for _ in range(10)]

def s_green(ctx, t):  # 26.3–32.5
    space(ctx, t); x, y, r = W / 2, 760, 210; R = 330
    a = ease((t - 26.3) / 0.4)
    # atmosphere shell
    g = cairo.RadialGradient(x, y, r, x, y, R)
    g.add_color_stop_rgba(0, 1, 0.75, 0.35, 0.55 * a); g.add_color_stop_rgba(0.75, 1, 0.65, 0.25, 0.35 * a); g.add_color_stop_rgba(1, 1, 0.6, 0.2, 0)
    ctx.set_source(g); ctx.arc(x, y, R, 0, 2 * math.pi); ctx.fill()
    ctx.set_source_rgba(1, 0.8, 0.45, 0.6 * a); ctx.set_line_width(4); ctx.arc(x, y, R - 25, 0, 2 * math.pi); ctx.stroke()
    venus(ctx, x, y, r, t * 0.4, halo=False)
    # CO2 molecules
    ma = ease((t - 26.95) / 0.5)
    if ma > 0:
        for (th, rr, vr, ph) in MOLS:
            ang = th + t * 0.25 * (1 if ph > 0.5 else -1); rad = r + 25 + rr * (R - r - 60)
            co2(ctx, x + rad * math.cos(ang), y + rad * math.sin(ang), 18, t * vr * 3 + ph * 6, ma)
        co2_label(ctx, x + 330, y - 330, 48, ma)
    # sunlight in
    if t > 27.9:
        la = ease((t - 27.9) / 0.4)
        for k in range(3):
            sx0, sy0 = x - 500 + k * 110, y - 400 + k * 30; ex0, ey0 = x - 120 + k * 80, y - r * 0.75 + k * 30
            u = ((t - 27.9) * 0.9 + k * 0.33) % 1
            ctx.set_source_rgba(1, 0.88, 0.3, 0.9 * la); ctx.set_line_width(10); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(sx0, sy0); ctx.line_to(lerp(sx0, ex0, 0.92), lerp(sy0, ey0, 0.92)); ctx.stroke()
            glow(ctx, lerp(sx0, ex0, u), lerp(sy0, ey0, u), 26, SUN, 0.9 * la)
    # trapped heat: particles bounce between surface and atmosphere edge
    if t > 28.4:
        ha = ease((t - 28.4) / 0.4)
        for (th, sp, ph) in HEAT:
            u = ((t - 28.4) * sp + ph) % 2.0; d = u if u < 1 else 2 - u
            rad = r + 8 + d * (R - r - 40); ang = th + 0.15 * math.sin(t + ph * 6)
            px, py = x + rad * math.cos(ang), y + rad * math.sin(ang)
            glow(ctx, px, py, 24, RED, 0.95 * ha); ctx.set_source_rgba(1, 0.6, 0.4, ha); ctx.arc(px, py, 6, 0, 2 * math.pi); ctx.fill()
        if t < 29.6: label(ctx, "EL CALOR NO ESCAPA", x, y + R + 70, 40, RED, ha)
    header(ctx, "Efecto", "invernadero", t, 26.35, y=260, alpha=1 - ease((t - 29.55) / 0.2))
    if t > 29.6:
        p = ease((t - 29.7) / 1.4); k = back((t - 29.6) / 0.35)
        ctx.save(); ctx.translate(W / 2, 270); ctx.scale(k, k)
        s = f"+{int(round(470 * p))} °C"; text(ctx, s, 0, 0, 120, RED if p > 0.98 else ACCENT, stroke=12)
        ctx.restore()
        thermo(ctx, x + 400, y - 80, 260, 0.2 + 0.78 * p, ease((t - 29.6) / 0.3), w=42)

def s_recap(ctx, t):  # 32.5–36.6
    space(ctx, t)
    cards = [(32.56, "dia"), (33.84, "sol"), (35.12, "calor")]
    for k, (t0, kind) in enumerate(cards):
        a = back((t - t0) / 0.4)
        if a <= 0: continue
        cx = 200 + k * 340; cy = 700
        ctx.save(); ctx.translate(cx, cy); ctx.scale(a, a)
        rrect(ctx, -150, -210, 300, 420, 40); ctx.set_source_rgba(0.03, 0.03, 0.09, 0.8); ctx.fill_preserve()
        ctx.set_source_rgba(1, 0.82, 0.25, 0.9); ctx.set_line_width(5); ctx.stroke()
        if kind == "dia":
            venus(ctx, 0, -50, 85, t, flag=-t * 1.2); arrow_arc(ctx, 0, -50, 115, -math.pi / 2 + 1.2, -math.pi / 2 - 0.6, ACCENT, 8, 1, head=24)
            text(ctx, "DÍA > AÑO", 0, 130, 40, ACCENT)
        elif kind == "sol":
            sun(ctx, 0, -50, 62, t); arrow_arc(ctx, 0, -50, 112, -0.3, -math.pi + 0.3, WHITE, 8, 1, head=24)
            text(ctx, "AL REVÉS", 0, 130, 44, ACCENT)
        else:
            thermo(ctx, 0, -175, 170, 0.95, 1, w=36); text(ctx, "+470 °C", 0, 130, 50, RED)
        ctx.restore()

def s_end(ctx, t):  # 36.6–end
    space(ctx, t)
    a = ease((t - 36.6) / 0.5)
    venus(ctx, W / 2, 1520, 190, t * 0.4, alpha=a)
    sc = 0.85 + 0.15 * back((t - 36.6) / 0.5); s = 300 * sc
    logo_mark(ctx, (W - s) / 2, 470 + (300 - s) / 2, s, a)
    w1 = text_w(ctx, "Logi", 120); w2 = text_w(ctx, "Datos", 120); x0 = (W - w1 - w2) / 2
    text(ctx, "Logi", x0, 900, 120, WHITE, align="left", alpha=a); text(ctx, "Datos", x0 + w1, 900, 120, ACCENT, align="left", alpha=a)
    text(ctx, "Curiosidades con lógica y datos", W / 2, 1010, 48, hexc("C8CEE0"), bold=False, alpha=a)
    pa = back((t - 38.9) / 0.4)
    if pa > 0:
        ctx.save(); ctx.translate(W / 2, 1150); ctx.scale(pa, pa)
        pw = text_w(ctx, "SÍGUENOS", 54) + 100; rrect(ctx, -pw / 2, -52, pw, 104, 52); rgba(ctx, ACCENT); ctx.fill()
        text(ctx, "SÍGUENOS", 0, 0, 54, NAVY); ctx.restore()

SCENES = [(0.0, s_hook), (3.75, s_reveal), (5.1, s_rotate), (10.9, s_orbit), (15.45, s_spin), (17.3, s_sunrise),
          (21.0, s_hot), (26.3, s_green), (32.5, s_recap), (36.6, s_end)]
END_START = 36.6

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
EMPH = {"VENUS", "DÍA", "AÑO", "REVÉS", "OESTE", "CALIENTE", "MERCURIO", "CALOR", "CARBONO", "DOSCIENTOS", "CUARENTA",
        "TRES", "VEINTICINCO", "CUATROCIENTOS", "SETENTA", "INFERNAL", "ETERNO"}
def clean(s): return s.replace("…", "").replace("¿", "").rstrip(".,;:?!…").upper()

CAP_Y, CAP_SIZE = 1330, 88
def captions(ctx, t):
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
        sh = cairo.LinearGradient(0, 1100, 0, 1560); sh.add_color_stop_rgba(0, 0, 0, 0, 0); sh.add_color_stop_rgba(0.5, 0, 0, 0, 0.35); sh.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(sh); ctx.rectangle(0, 1100, W, 460); ctx.fill()
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
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", AUDIO, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-af", "apad", "-t", str(TOTAL), FINAL], check=True)
    print("OK", FINAL)
