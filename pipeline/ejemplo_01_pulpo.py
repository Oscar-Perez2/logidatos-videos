#!/usr/bin/env python3
"""LogiDatos Short #1 – El pulpo y sus tres corazones. Motion graphics drawn in code (cairo).
python3 motion.py [preview t1 t2 ...]"""
import json, math, os, random, subprocess, sys
import cairo

W, H, FPS = 1080, 1920, 30
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "build2"); os.makedirs(OUT, exist_ok=True)
AUDIO = os.path.join(BASE, "dl/voz.mp3")
WORDS = [w for w in json.load(open(os.path.join(BASE, "dl/words.json")))["words"] if w.get("type", "word") == "word"]
TOTAL = 38.9
FINAL = os.path.join(BASE, "LogiDatos_01_pulpo_tres_corazones.mp4")

def hexc(h, a=1.0):
    h = h.lstrip("#"); return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)
ACCENT = hexc("FFD23F"); NAVY = hexc("0B1020"); WHITE = hexc("F5F3EA")
OCT = hexc("E8664A"); OCT_D = hexc("A93A27"); OCT_L = hexc("F9B39C")
BLUE = hexc("3DA9FC"); BLUE_D = hexc("1D5FD1"); RED = hexc("E0393E"); GREEN = hexc("37E08F")
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
    ext = ctx.text_extents(s)
    w = ext.x_advance
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

def heart_path(ctx, x, y, s):
    ctx.new_path(); ctx.move_to(x, y + 0.36 * s)
    ctx.curve_to(x - 0.08 * s, y + 0.28 * s, x - 0.52 * s, y + 0.05 * s, x - 0.5 * s, y - 0.2 * s)
    ctx.curve_to(x - 0.48 * s, y - 0.46 * s, x - 0.14 * s, y - 0.56 * s, x, y - 0.3 * s)
    ctx.curve_to(x + 0.14 * s, y - 0.56 * s, x + 0.48 * s, y - 0.46 * s, x + 0.5 * s, y - 0.2 * s)
    ctx.curve_to(x + 0.52 * s, y + 0.05 * s, x + 0.08 * s, y + 0.28 * s, x, y + 0.36 * s); ctx.close_path()

def heart(ctx, x, y, s, color=RED, alpha=1.0, glow=True):
    if glow:
        g = cairo.RadialGradient(x, y, 0, x, y, s * 0.9)
        g.add_color_stop_rgba(0, color[0], color[1], color[2], 0.45 * alpha); g.add_color_stop_rgba(1, color[0], color[1], color[2], 0)
        ctx.set_source(g); ctx.arc(x, y, s * 0.9, 0, 2 * math.pi); ctx.fill()
    heart_path(ctx, x, y, s); rgba(ctx, color, alpha); ctx.fill_preserve()
    ctx.set_source_rgba(1, 1, 1, 0.25 * alpha); ctx.set_line_width(max(2, s * 0.04)); ctx.stroke()
    ctx.set_source_rgba(1, 1, 1, 0.35 * alpha); ctx.arc(x - 0.22 * s, y - 0.25 * s, s * 0.07, 0, 2 * math.pi); ctx.fill()

def drop(ctx, x, y, s, color, alpha=1.0):
    ctx.new_path(); ctx.move_to(x, y - 0.62 * s)
    ctx.curve_to(x + 0.12 * s, y - 0.35 * s, x + 0.45 * s, y - 0.05 * s, x + 0.45 * s, y + 0.2 * s)
    ctx.arc(x, y + 0.2 * s, 0.45 * s, 0, math.pi)
    ctx.curve_to(x - 0.45 * s, y - 0.05 * s, x - 0.12 * s, y - 0.35 * s, x, y - 0.62 * s); ctx.close_path()
    g = cairo.LinearGradient(x - 0.4 * s, y - 0.5 * s, x + 0.4 * s, y + 0.6 * s)
    g.add_color_stop_rgba(0, min(1, color[0] + 0.25), min(1, color[1] + 0.25), min(1, color[2] + 0.25), alpha)
    g.add_color_stop_rgba(1, color[0] * 0.7, color[1] * 0.7, color[2] * 0.7, alpha)
    ctx.set_source(g); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.4 * alpha); ctx.arc(x - 0.18 * s, y + 0.12 * s, 0.08 * s, 0, 2 * math.pi); ctx.fill()

def logo_mark(ctx, x, y, s, alpha=1.0):
    rrect(ctx, x, y, s, s, s * 0.21); rgba(ctx, ACCENT, alpha); ctx.fill()
    k = s / 200 * 0.70; ox = x + s * 0.15 - 5 * k; oy = y + s * 0.15 + 3 * k
    rgba(ctx, NAVY, alpha)
    for (a, b, c, d) in [(38, 28, 34, 144), (38, 138, 134, 34), (88, 98, 34, 56), (138, 66, 34, 88)]:
        rrect(ctx, ox + a * k, oy + b * k, c * k, d * k, 8 * k); ctx.fill()
    ctx.arc(ox + 155 * k, oy + 38 * k, 15 * k, 0, 2 * math.pi); ctx.fill()

# ---------------- background ----------------
random.seed(7)
SNOW = [(random.random(), random.random(), random.uniform(1.5, 4.5), random.uniform(8, 30), random.random()) for _ in range(90)]
RAYS = [(random.uniform(0.05, 0.95), random.uniform(60, 160), random.uniform(0.2, 0.6), random.random() * 6) for _ in range(6)]
BUBBLES = [(random.uniform(-1, 1), random.uniform(0, 1), random.uniform(5, 16), random.uniform(0.6, 1.4)) for _ in range(26)]

def ocean(ctx, t, floor=None):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, 0.07, 0.30, 0.47); g.add_color_stop_rgb(0.45, 0.03, 0.14, 0.27); g.add_color_stop_rgb(1, 0.02, 0.05, 0.11)
    ctx.set_source(g); ctx.paint()
    for (x, w, a, ph) in RAYS:
        cx = x * W + math.sin(t * 0.4 + ph) * 60
        gr = cairo.LinearGradient(0, 0, 0, H * 0.75)
        gr.add_color_stop_rgba(0, 0.75, 0.92, 1, 0.10 * a); gr.add_color_stop_rgba(1, 0.75, 0.92, 1, 0)
        ctx.set_source(gr); ctx.new_path(); ctx.move_to(cx - w / 2, 0); ctx.line_to(cx + w / 2, 0)
        ctx.line_to(cx + w * 1.6 + 120, H * 0.75); ctx.line_to(cx - w * 0.4 + 120, H * 0.75); ctx.close_path(); ctx.fill()
    for (x, y, r, sp, ph) in SNOW:
        yy = (y * H - t * sp) % H; xx = x * W + math.sin(t * 0.6 + ph * 6) * 12
        ctx.set_source_rgba(0.85, 0.95, 1, 0.18 + 0.15 * ph); ctx.arc(xx, yy, r, 0, 2 * math.pi); ctx.fill()
    if floor is not None:
        ctx.new_path(); ctx.move_to(0, floor)
        for i in range(0, W + 41, 40): ctx.line_to(i, floor + math.sin(i * 0.013) * 18)
        ctx.line_to(W, H); ctx.line_to(0, H); ctx.close_path()
        gs = cairo.LinearGradient(0, floor, 0, H); gs.add_color_stop_rgb(0, 0.76, 0.66, 0.47); gs.add_color_stop_rgb(1, 0.30, 0.25, 0.17)
        ctx.set_source(gs); ctx.fill()
        random.seed(3)
        for _ in range(60):
            ctx.set_source_rgba(0.45, 0.38, 0.26, 0.5); ctx.arc(random.uniform(0, W), random.uniform(floor + 30, H), random.uniform(2, 6), 0, 2 * math.pi); ctx.fill()
        for (rx, rs) in [(90, 120), (990, 160), (860, 80)]:
            ctx.set_source_rgba(0.22, 0.26, 0.3, 1); ctx.save(); ctx.translate(rx, floor + 10); ctx.scale(1, 0.62)
            ctx.arc(0, 0, rs, math.pi, 2 * math.pi); ctx.fill(); ctx.restore()
    vg = cairo.RadialGradient(W / 2, H * 0.42, H * 0.25, W / 2, H * 0.5, H * 0.75)
    vg.add_color_stop_rgba(0, 0, 0, 0, 0); vg.add_color_stop_rgba(1, 0, 0, 0, 0.55)
    ctx.set_source(vg); ctx.paint()

# ---------------- octopus ----------------
def arm_points(i, t, s, mode, n=26):
    if mode == "swim":
        a0 = math.radians(90 + (i - 3.5) * 5.0); L = 1.55 * s; amp = 0.16; curl = 0.0; fr = 3.2
    elif mode == "crawl":
        a0 = math.radians(90 + (i - 3.5) * 25); L = 1.15 * s; amp = 0.22; curl = 0.9; fr = 1.6
    else:
        a0 = math.radians(90 + (i - 3.5) * 17); L = 1.3 * s; amp = 0.32; curl = 1.3; fr = 1.5
    side = -1 if i < 4 else 1
    if mode == "crawl": side = -side
    bx = (i - 3.5) / 3.5 * 0.26 * s; by = 0.2 * s
    pts = [(bx, by)]; x, y = bx, by
    for k in range(1, n + 1):
        u = k / n
        ang = a0 + side * curl * u * u * 0.9 + math.sin(t * fr + i * 0.9 - u * 4.2) * amp * u
        x += math.cos(ang) * L / n; y += math.sin(ang) * L / n; pts.append((x, y))
    return pts

def arm_shape(ctx, pts, s, color, under, alpha):
    n = len(pts) - 1; L, R = [], []
    for k, (x, y) in enumerate(pts):
        u = k / n; px, py = pts[max(k - 1, 0)]; nx, ny = pts[min(k + 1, n)]
        dx, dy = nx - px, ny - py; d = math.hypot(dx, dy) or 1; ox, oy = -dy / d, dx / d
        w = (0.085 * (1 - u) ** 0.9 + 0.012) * s
        L.append((x + ox * w, y + oy * w)); R.append((x - ox * w, y - oy * w))
    ctx.new_path(); ctx.move_to(*L[0])
    for p in L[1:]: ctx.line_to(*p)
    for p in reversed(R): ctx.line_to(*p)
    ctx.close_path(); rgba(ctx, color, alpha); ctx.fill()
    if under:
        for k in range(2, n - 2, 2):
            u = k / n; x, y = L[k]; r = (0.026 * (1 - u) + 0.006) * s
            rgba(ctx, OCT_L, alpha * 0.9); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.fill()

def mantle_path(ctx, s, squash=1.0):
    ctx.new_path(); ctx.move_to(-0.3 * s, 0.25 * s)
    ctx.curve_to(-0.5 * s, 0.0, -0.47 * s * squash, -0.66 * s / squash, 0, -0.68 * s / squash)
    ctx.curve_to(0.47 * s * squash, -0.66 * s / squash, 0.5 * s, 0.0, 0.3 * s, 0.25 * s)
    ctx.curve_to(0.15 * s, 0.32 * s, -0.15 * s, 0.32 * s, -0.3 * s, 0.25 * s); ctx.close_path()

def octopus(ctx, x, y, s, t, mode="idle", rot=0.0, xray=0.0, alpha=1.0, blink=True):
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot)
    squash = 1.0 + (0.07 * math.sin(t * 6) if mode == "swim" else 0.025 * math.sin(t * 2))
    body_a = alpha * (1 - 0.62 * xray)
    for i in [0, 7, 1, 6, 2, 5, 3, 4]:
        arm_shape(ctx, arm_points(i, t, s, mode), s, OCT_D if i in (0, 7, 1, 6) else OCT, xray < 0.5, body_a)
    mantle_path(ctx, s, squash)
    g = cairo.LinearGradient(-0.4 * s, -0.6 * s, 0.4 * s, 0.3 * s)
    g.add_color_stop_rgba(0, OCT_L[0], OCT_L[1], OCT_L[2], body_a); g.add_color_stop_rgba(0.5, OCT[0], OCT[1], OCT[2], body_a)
    g.add_color_stop_rgba(1, OCT_D[0], OCT_D[1], OCT_D[2], body_a)
    ctx.set_source(g); ctx.fill_preserve()
    if xray > 0:
        ctx.set_source_rgba(0.6, 0.9, 1, 0.8 * xray * alpha); ctx.set_line_width(4); ctx.stroke()
    else:
        ctx.new_path()
    if xray < 0.6:
        for (sx, sy, r) in [(-0.2, -0.42, 0.05), (0.12, -0.5, 0.035), (0.25, -0.3, 0.045), (-0.05, -0.25, 0.03)]:
            rgba(ctx, OCT_D, 0.35 * alpha); ctx.arc(sx * s, sy * s, r * s, 0, 2 * math.pi); ctx.fill()
    bl = 1.0
    if blink:
        ph = (t % 3.7); bl = 0.12 if 0 < ph < 0.12 else 1.0
    for ex in (-0.19, 0.19):
        ctx.save(); ctx.translate(ex * s, 0.02 * s); ctx.scale(1, bl)
        ctx.set_source_rgba(1, 0.97, 0.9, alpha); ctx.arc(0, 0, 0.1 * s, 0, 2 * math.pi); ctx.fill()
        ctx.set_source_rgba(0.08, 0.06, 0.06, alpha); rrect(ctx, -0.062 * s, -0.034 * s, 0.124 * s, 0.068 * s, 0.034 * s); ctx.fill()
        ctx.set_source_rgba(1, 1, 1, 0.8 * alpha); ctx.arc(-0.03 * s, -0.04 * s, 0.018 * s, 0, 2 * math.pi); ctx.fill()
        ctx.restore()
    ctx.restore()

def arm_world(i, t, s, x, y, mode="idle", rot=0.0):
    c, sn = math.cos(rot), math.sin(rot)
    return [(x + px * c - py * sn, y + px * sn + py * c) for (px, py) in arm_points(i, t, s, mode)]

def flow_particles(ctx, path, t, color, count=5, speed=0.6, r=9, alpha=1.0):
    n = len(path) - 1
    for j in range(count):
        u = (t * speed + j / count) % 1.0
        f = u * n; k = int(f); fr = f - k; k2 = min(k + 1, n)
        px = lerp(path[k][0], path[k2][0], fr); py = lerp(path[k][1], path[k2][1], fr)
        a = alpha * math.sin(u * math.pi)
        g = cairo.RadialGradient(px, py, 0, px, py, r * 2.4)
        g.add_color_stop_rgba(0, color[0], color[1], color[2], a); g.add_color_stop_rgba(1, color[0], color[1], color[2], 0)
        ctx.set_source(g); ctx.arc(px, py, r * 2.4, 0, 2 * math.pi); ctx.fill()

def gill(ctx, x, y, s, side, alpha):
    ctx.save(); ctx.translate(x, y)
    for k in range(7):
        yy = (k - 3) * s * 0.11
        ctx.set_source_rgba(0.55, 0.85, 1, 0.8 * alpha); ctx.set_line_width(s * 0.05); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(0, yy); ctx.line_to(side * s * (0.28 - abs(k - 3) * 0.04), yy - s * 0.04); ctx.stroke()
    ctx.set_source_rgba(0.55, 0.85, 1, alpha); ctx.set_line_width(s * 0.05); ctx.move_to(0, -s * 0.36); ctx.line_to(0, s * 0.36); ctx.stroke()
    ctx.restore()

def label(ctx, s, x, y, size=44, color=WHITE, alpha=1.0, bg=True):
    w = text_w(ctx, s, size)
    if bg:
        rrect(ctx, x - w / 2 - 26, y - size * 0.75, w + 52, size * 1.5, size * 0.5); ctx.set_source_rgba(0.02, 0.05, 0.11, 0.72 * alpha); ctx.fill()
    text(ctx, s, x, y, size, color, alpha=alpha)

def header(ctx, s1, s2, t, t0, y=300, size=66):
    a = ease((t - t0) / 0.35);
    if a <= 0: return
    ctx.save(); ctx.translate(0, (1 - a) * 30)
    w1 = text_w(ctx, s1 + " ", size); w2 = text_w(ctx, s2, size); x0 = (W - w1 - w2) / 2
    text(ctx, s1, x0, y, size, WHITE, stroke=10, align="left", alpha=a)
    text(ctx, s2, x0 + w1, y, size, ACCENT, stroke=10, align="left", alpha=a)
    ctx.restore()

# ---------------- scenes ----------------
def beat(t, bpm=80):
    ph = (t * bpm / 60) % 1.0
    return 1 + 0.16 * math.exp(-((ph - 0.05) ** 2) / 0.004) + 0.08 * math.exp(-((ph - 0.28) ** 2) / 0.004)

def s_hook(ctx, t):
    ocean(ctx, t)
    s = 330 * (1 + 0.04 * ease(t / 5.5)); octopus(ctx, W / 2, 830 - 10 * math.sin(t * 1.3), s, t)
    xs = [W / 2 - 200, W / 2, W / 2 + 200]; tin = [1.04, 1.36, 1.6]
    for k, x in enumerate(xs):
        a = back((t - tin[k]) / 0.35)
        if a <= 0: continue
        dead = k == 2 and t > 3.5
        sc = a * (beat(t + k * 0.1) if not dead else 1)
        col = RED if not dead else hexc("6B7280")
        heart(ctx, x, 330, 150 * sc, col, alpha=clamp(a), glow=not dead)
        if dead:
            p = ease((t - 3.5) / 0.3); ctx.set_source_rgba(0.1, 0.1, 0.12, p); ctx.set_line_width(10); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(x - 16, 300); ctx.line_to(x - 16, 352); ctx.move_to(x + 16, 300); ctx.line_to(x + 16, 352); ctx.stroke()

def s_gills(ctx, t):  # 5.5–12.0
    ocean(ctx, t); s = 420; x, y = W / 2, 820
    xr = ease((t - 6.6) / 0.6)
    octopus(ctx, x, y, s, t, xray=xr)
    if xr > 0:
        a = xr
        gill(ctx, x - 0.3 * s, y - 0.4 * s, s * 0.42, -1, a); gill(ctx, x + 0.3 * s, y - 0.4 * s, s * 0.42, 1, a)
        hs = 64 * beat(t, 90)
        for sd in (-1, 1):
            hx, hy = x + sd * 0.12 * s, y - 0.3 * s
            hl = ease((t - 7.6) / 0.3)
            if hl > 0:
                heart(ctx, hx, hy, hs * hl, RED, alpha=a)
                path = [(hx + sd * 0.18 * s * u, hy - 0.1 * s * math.sin(u * math.pi * 0.5)) for u in [i / 12 for i in range(13)]]
                if t > 8.5: flow_particles(ctx, path, t, BLUE, count=4, speed=0.9, r=10, alpha=a)
        if t > 9.6:
            la = ease((t - 9.6) / 0.3)
            for sd in (-1, 1):
                gx = x + sd * 0.42 * s; lx = x + sd * 0.66 * s
                ctx.set_source_rgba(0.55, 0.85, 1, la); ctx.set_line_width(4); ctx.move_to(gx, y - 0.4 * s); ctx.line_to(lx, y - 0.4 * s + 70); ctx.stroke()
                label(ctx, "BRANQUIA", lx, y - 0.4 * s + 110, 34, BLUE, la)
        if t > 10.9:
            for k in range(8):
                ox = x + math.sin(k * 2.1 + t * 2) * 0.45 * s; oy = y - 0.55 * s - ((t * 120 + k * 60) % 260)
                ctx.set_source_rgba(0.8, 0.95, 1, 0.6 * ease((t - 10.9) / 0.4)); ctx.arc(ox, oy, 8, 0, 2 * math.pi); ctx.fill()
            label(ctx, "+ OXÍGENO", W / 2, y - 0.95 * s, 46, ACCENT, ease((t - 10.9) / 0.3), bg=True)
    header(ctx, "2 corazones", "→ branquias", t, 7.2)

def s_systemic(ctx, t):  # 12.0–16.2
    ocean(ctx, t); s = 360; x, y = W / 2, 700
    octopus(ctx, x, y, s, t, xray=1.0)
    hx, hy = x, y - 0.2 * s
    hl = back((t - 13.0) / 0.4)
    if hl > 0: heart(ctx, hx, hy, 120 * hl * beat(t, 90), RED)
    if t > 14.4:
        a = ease((t - 14.4) / 0.4)
        for i in range(8):
            pts = arm_world(i, t, s, x, y)
            path = [(hx, hy)] + pts
            flow_particles(ctx, path, t + i * 0.13, BLUE, count=5, speed=0.55, r=9, alpha=a)
    header(ctx, "1 corazón", "→ todo el cuerpo", t, 12.9)

def ecg(ctx, t, x, y, w, h, flat_at):
    rrect(ctx, x, y, w, h, 28); ctx.set_source_rgba(0.02, 0.05, 0.11, 0.8); ctx.fill_preserve()
    ctx.set_source_rgba(1, 1, 1, 0.15); ctx.set_line_width(3); ctx.stroke()
    flat = t >= flat_at
    heart(ctx, x + 70, y + h / 2, 70 * (beat(t, 100) if not flat else 1), RED if not flat else hexc("6B7280"), glow=not flat)
    gx0, gx1 = x + 140, x + w - 30; mid = y + h / 2
    ctx.set_line_width(7); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.new_path()
    for k in range(0, 160):
        u = k / 159; px = lerp(gx0, gx1, u); tt = t - (1 - u) * 1.6
        v = 0
        if tt < flat_at:
            ph = (tt * 100 / 60) % 1.0
            v = -math.exp(-((ph - 0.3) ** 2) / 0.0007) * 1.0 + math.exp(-((ph - 0.34) ** 2) / 0.0006) * 0.45 + -math.exp(-((ph - 0.6) ** 2) / 0.006) * 0.15
        py = mid + v * h * 0.38
        (ctx.move_to if k == 0 else ctx.line_to)(px, py)
    rgba(ctx, GREEN if not flat else RED); ctx.stroke()

def battery(ctx, x, y, level, alpha):
    ctx.set_source_rgba(1, 1, 1, alpha); ctx.set_line_width(7); rrect(ctx, x, y, 150, 74, 14); ctx.stroke()
    rrect(ctx, x + 150, y + 22, 14, 30, 5); ctx.fill()
    col = GREEN if level > 0.5 else (ACCENT if level > 0.25 else RED)
    rgba(ctx, col, alpha); rrect(ctx, x + 12, y + 12, 126 * level, 50, 8); ctx.fill()

def s_swim(ctx, t):  # 16.2–21.7
    ocean(ctx, t); u = (t - 16.2) / 5.5
    x = lerp(220, 860, u); y = lerp(1180, 700, u) + math.sin(t * 6) * 10
    rot = math.atan2(-480, 640) + math.pi / 2
    for (bx, by, r, sp) in BUBBLES:
        age = ((t * sp + by) % 1.0); px = x - math.sin(rot) * -260 * 0 + bx * 40 - age * 200 * math.sin(rot)
        py = y + age * 260; ctx.set_source_rgba(0.85, 0.95, 1, 0.5 * (1 - age)); ctx.set_line_width(3)
        ctx.arc(px - 120 * age, py, r * (0.6 + age), 0, 2 * math.pi); ctx.stroke()
    octopus(ctx, x, y, 250, t, mode="swim", rot=rot)
    ecg(ctx, t, 140, 210, 800, 190, flat_at=19.25)
    if t > 19.25:
        label(ctx, "SE DETIENE", W / 2, 470, 46, RED, ease((t - 19.25) / 0.3))
    if t > 20.4:
        a = ease((t - 20.4) / 0.3); lvl = lerp(0.9, 0.08, ease((t - 20.6) / 1.0))
        battery(ctx, W / 2 - 82, 540, lvl, a)

def s_crawl(ctx, t):  # 21.7–24.1
    floor = 1060; ocean(ctx, t, floor=floor); u = (t - 21.7) / 2.4
    octopus(ctx, lerp(380, 660, u), floor - 250 + 6 * math.sin(t * 5), 300, t * 1.6, mode="crawl")
    header(ctx, "Prefiere", "arrastrarse", t, 21.9)

def s_blood(ctx, t):  # 24.1–31.35
    ocean(ctx, t)
    a_in = back((t - 24.3) / 0.45)
    mv = ease((t - 26.9) / 0.6)
    bx = lerp(W / 2, 770, mv); bs = lerp(400, 290, mv) * (1 + 0.03 * math.sin(t * 3))
    if a_in > 0: drop(ctx, bx, 760, bs * a_in, BLUE, clamp(a_in))
    if t < 27.0: header(ctx, "Sangre", "AZUL", t, 25.3, y=330, size=84)
    ra = back((t - 27.04) / 0.45)
    if ra > 0:
        drop(ctx, 310, 760, 290 * ra, RED, clamp(ra))
        la = ease((t - 27.2) / 0.3); label(ctx, "HUMANO", 310, 420, 44, WHITE, la)
    if t > 27.8:
        a = ease((t - 27.8) / 0.3); text(ctx, "Fe", 310, 800, 110, WHITE, stroke=8, alpha=a); label(ctx, "HIERRO", 310, 1010, 48, RED, a)
    if t > 29.6:
        a = ease((t - 29.6) / 0.3); label(ctx, "PULPO", 770, 420, 44, WHITE, a)
    if t > 30.6:
        a = ease((t - 30.6) / 0.3); text(ctx, "Cu", 770, 800, 110, WHITE, stroke=8, alpha=a); label(ctx, "COBRE", 770, 1010, 48, BLUE, a)

def s_recap(ctx, t):  # 31.35–34.6
    ocean(ctx, t)
    cards = [(31.44, "x3"), (32.64, "azul"), (33.68, "8")]
    for k, (t0, kind) in enumerate(cards):
        a = back((t - t0) / 0.4)
        if a <= 0: continue
        cx = 200 + k * 340; cy = 720
        ctx.save(); ctx.translate(cx, cy); ctx.scale(a, a)
        rrect(ctx, -150, -210, 300, 420, 40); ctx.set_source_rgba(0.02, 0.05, 0.11, 0.78); ctx.fill_preserve()
        ctx.set_source_rgba(1, 0.82, 0.25, 0.9); ctx.set_line_width(5); ctx.stroke()
        if kind == "x3":
            heart(ctx, 0, -40, 150 * beat(t), RED); text(ctx, "×3", 0, 130, 70, ACCENT)
        elif kind == "azul":
            drop(ctx, 0, -40, 190, BLUE); text(ctx, "AZUL", 0, 130, 56, BLUE)
        else:
            octopus(ctx, 0, -70, 95, t, blink=False); text(ctx, "8", 0, 130, 80, ACCENT)
        ctx.restore()

def s_end(ctx, t):  # 34.6–end
    ocean(ctx, t)
    a = ease((t - 34.6) / 0.5)
    octopus(ctx, W / 2, 1480, 200, t, alpha=a)
    sc = 0.85 + 0.15 * back((t - 34.6) / 0.5); s = 300 * sc
    logo_mark(ctx, (W - s) / 2, 470 + (300 - s) / 2, s, a)
    w1 = text_w(ctx, "Logi", 120); w2 = text_w(ctx, "Datos", 120); x0 = (W - w1 - w2) / 2
    text(ctx, "Logi", x0, 900, 120, WHITE, align="left", alpha=a); text(ctx, "Datos", x0 + w1, 900, 120, ACCENT, align="left", alpha=a)
    text(ctx, "Curiosidades con lógica y datos", W / 2, 1010, 48, hexc("C8CEE0"), bold=False, alpha=a)
    pa = back((t - 36.9) / 0.4)
    if pa > 0:
        ctx.save(); ctx.translate(W / 2, 1140); ctx.scale(pa, pa)
        pw = text_w(ctx, "SÍGUENOS", 54) + 100; rrect(ctx, -pw / 2, -52, pw, 104, 52); rgba(ctx, ACCENT); ctx.fill()
        text(ctx, "SÍGUENOS", 0, 0, 54, NAVY); ctx.restore()

SCENES = [(0.0, s_hook), (5.5, s_gills), (12.0, s_systemic), (16.2, s_swim), (21.7, s_crawl), (24.1, s_blood), (31.35, s_recap), (34.6, s_end)]
END_START = 34.6

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
EMPH = {"CORAZONES", "PULPO", "AZUL", "COBRE", "HIERRO", "LATIR", "TRES", "SISTÉMICO", "BRANQUIAS", "OXÍGENO"}
def clean(s): return s.replace("…", "").replace("¿", "").rstrip(".,;:?!").upper()

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
