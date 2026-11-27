#!/usr/bin/env python3
"""LogiDatos Short #8 – Esta mañana eras más alto que ahora (discos de la columna, gravedad y astronautas). Motion graphics drawn in code (cairo).
python3 video_08_mas_alto_en_la_manana.py [preview t1 t2 ...]
Render -> build/silent.mp4; luego: musica.py mix build/silent.mp4 dl/voz.mp3 build/musica.wav <FINAL> --total TOTAL"""
import json, math, os, random, subprocess, sys
import cairo

W, H, FPS = 1080, 1920, 30
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "build"); os.makedirs(OUT, exist_ok=True)
WORDS = [w for w in json.load(open(os.path.join(BASE, "dl/words.json")))["words"] if w.get("type", "word") == "word"]
TOTAL = 53.5

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


# ---------------- episode #8: eres más alto en la mañana ----------------
SKY_D = hexc("1C3F7A"); NIGHT = hexc("0A0F2C"); SPACE = hexc("03040B")
BONE = hexc("EDE6D6"); BONE_D = hexc("C9BFA8"); DISC = hexc("8FB3D9"); WATER = hexc("3DA9FC")
PERSON = hexc("FF8A3D"); PERSON2 = hexc("7FD8FF"); SUIT = hexc("E9EEF5"); VISOR = hexc("F2B233")
SKIN = hexc("F2C9A5"); BLANKET = hexc("3D5AFE"); WOOD = hexc("7A4E2D")

random.seed(8)
STARS = [(random.random() * W, random.random() * H, random.uniform(1.2, 3.2), random.random()) for _ in range(140)]
DOTS = [(random.random(), random.random(), random.uniform(3, 7), random.random()) for _ in range(40)]

def bg(ctx, t, day=0.0, night=0.0, space=0.0):
    top = hexc("16224A"); mid = hexc("0E1634"); bot = hexc("070B1C")
    top = mixc(top, SKY_D, day); mid = mixc(mid, hexc("13285A"), day)
    top = mixc(top, NIGHT, night); mid = mixc(mid, hexc("060A20"), night); bot = mixc(bot, hexc("03050F"), night)
    top = mixc(top, SPACE, space); mid = mixc(mid, SPACE, space); bot = mixc(bot, SPACE, space)
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, top[0], top[1], top[2]); g.add_color_stop_rgb(0.55, mid[0], mid[1], mid[2]); g.add_color_stop_rgb(1, bot[0], bot[1], bot[2])
    ctx.set_source(g); ctx.paint()
    # cuadrícula tipo plano (cuerpo humano); se apaga en el espacio
    ga = 0.045 * (1 - space)
    if ga > 0:
        ctx.set_line_width(2); ctx.set_source_rgba(0.6, 0.8, 1, ga)
        off = (t * 12) % 90
        for x in range(0, W + 90, 90): ctx.move_to(x, 0); ctx.line_to(x, H)
        for y in range(-90, H + 90, 90): ctx.move_to(0, y + off); ctx.line_to(W, y + off)
        ctx.stroke()
    sa = max(night * 0.6, space)
    if sa > 0:
        for (x, y, r, ph) in STARS:
            a = sa * (0.35 + 0.45 * (0.5 + 0.5 * math.sin(t * 2.2 + ph * 20)))
            ctx.arc(x, y, r, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, a); ctx.fill()
    glow(ctx, 220 + 60 * math.sin(t * 0.3), 560, 640, mixc(BLUE, ACCENT, day), 0.10 * (1 - 0.6 * space))
    glow(ctx, 880, 1300 + 50 * math.sin(t * 0.2), 700, mixc(BLUE, PURPLE_C, night), 0.08)
    for (x, y, r, ph) in DOTS:
        yy = (y * H - t * (16 + 26 * ph)) % H; a = (0.08 + 0.06 * math.sin(t * 2 + ph * 9)) * (1 - space)
        if a > 0:
            ctx.new_path(); ctx.arc(x * W + 10 * math.sin(t + ph * 6), yy, r, 0, 2 * math.pi); ctx.set_source_rgba(0.8, 0.9, 1, a); ctx.fill()

PURPLE_C = hexc("A06CFF")

def sun(ctx, x, y, r, t, alpha=1.0):
    if alpha <= 0 or r <= 0: return
    glow(ctx, x, y, r * 2.6, ACCENT, 0.45 * alpha)
    ctx.set_line_width(r * 0.16); ctx.set_line_cap(cairo.LINE_CAP_ROUND); rgba(ctx, ACCENT, alpha)
    for k in range(10):
        a = k * math.pi / 5 + t * 0.6
        ctx.move_to(x + r * 1.3 * math.cos(a), y + r * 1.3 * math.sin(a)); ctx.line_to(x + r * 1.65 * math.cos(a), y + r * 1.65 * math.sin(a))
    ctx.stroke()
    ctx.arc(x, y, r, 0, 2 * math.pi); rgba(ctx, ACCENT, alpha); ctx.fill()

def moon(ctx, x, y, r, alpha=1.0, bgc=NIGHT):
    if alpha <= 0 or r <= 0: return
    glow(ctx, x, y, r * 2.4, (0.75, 0.82, 1, 1), 0.3 * alpha)
    ctx.push_group()
    ctx.arc(x, y, r, 0, 2 * math.pi); ctx.set_source_rgba(0.95, 0.93, 0.82, 1); ctx.fill()
    ctx.set_operator(cairo.OPERATOR_CLEAR); ctx.arc(x + r * 0.45, y - r * 0.25, r * 0.85, 0, 2 * math.pi); ctx.fill()
    ctx.pop_group_to_source(); ctx.paint_with_alpha(alpha)

def person(ctx, x, foot, h, color=PERSON, alpha=1.0):
    """Figura tipo pictograma de pie; h = estatura en px."""
    if alpha <= 0 or h <= 0: return
    rgba(ctx, color, alpha)
    ctx.arc(x, foot - 0.915 * h, 0.075 * h, 0, 2 * math.pi); ctx.fill()
    rrect(ctx, x - 0.13 * h, foot - 0.82 * h, 0.26 * h, 0.40 * h, 0.07 * h); ctx.fill()
    for s in (-1, 1):
        rrect(ctx, x + s * 0.165 * h - 0.035 * h, foot - 0.80 * h, 0.07 * h, 0.36 * h, 0.035 * h); ctx.fill()
        rrect(ctx, x + s * 0.06 * h - 0.05 * h, foot - 0.47 * h, 0.10 * h, 0.47 * h, 0.05 * h); ctx.fill()

def ruler(ctx, x, top, bottom, alpha=1.0, w=56):
    if alpha <= 0: return
    rrect(ctx, x - w / 2, top, w, bottom - top, 8); rgba(ctx, ACCENT, alpha); ctx.fill()
    n = int((bottom - top) / 16)
    ctx.set_line_width(3); rgba(ctx, NAVY, alpha)
    for i in range(1, n):
        y = bottom - i * 16; L = w * (0.55 if i % 5 == 0 else 0.3)
        ctx.move_to(x - w / 2, y); ctx.line_to(x - w / 2 + L, y)
    ctx.stroke()

def dashed(ctx, x0, x1, y, color, alpha=1.0, w=5):
    if alpha <= 0: return
    ctx.set_dash([18, 12]); ctx.set_line_width(w); rgba(ctx, color, alpha)
    ctx.move_to(x0, y); ctx.line_to(x1, y); ctx.stroke(); ctx.set_dash([])

def bracket(ctx, x, y0, y1, color, alpha=1.0, w=8, tick=22):
    if alpha <= 0: return
    ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND); rgba(ctx, color, alpha)
    ctx.move_to(x - tick, y0); ctx.line_to(x, y0); ctx.line_to(x, y1); ctx.line_to(x - tick, y1); ctx.stroke()

def drop(ctx, x, y, s, alpha=1.0, rot=0.0):
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s)
    ctx.new_path(); ctx.move_to(0, -1.3); ctx.curve_to(0.5, -0.5, 0.9, 0.0, 0.9, 0.35); ctx.curve_to(0.9, 0.9, -0.9, 0.9, -0.9, 0.35)
    ctx.curve_to(-0.9, 0.0, -0.5, -0.5, 0, -1.3); ctx.close_path(); rgba(ctx, WATER, alpha); ctx.fill()
    ctx.arc(-0.3, 0.25, 0.18, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, 0.6 * alpha); ctx.fill(); ctx.restore()

def spine(ctx, cx, bottom, s=1.0, squash=0.0, water=0.0, built=1.0, t=0.0, alpha=1.0, wob=0.0, hl=-1):
    """Columna: 24 vértebras con 23 discos entre ellas, de abajo (lumbar) hacia arriba (cuello).
    squash 0..1 aplasta los discos; water 0..1 los pinta de agua. Devuelve la y del tope."""
    vh = 24 * s; dh = 14 * s * (1 - 0.6 * squash); y = bottom
    nb = built * 24
    for i in range(24):
        k = clamp(nb - i)
        if k <= 0: break
        w = s * (150 - 66 * i / 23); xo = cx + 26 * s * math.sin(i / 23 * math.pi * 1.7 - 0.4)
        ctx.save(); ctx.translate(xo, y - vh / 2); ctx.scale(k, k)
        rrect(ctx, -w / 2, -vh / 2, w, vh, 7 * s)
        g = cairo.LinearGradient(-w / 2, 0, w / 2, 0)
        g.add_color_stop_rgba(0, BONE_D[0], BONE_D[1], BONE_D[2], alpha); g.add_color_stop_rgba(0.5, BONE[0], BONE[1], BONE[2], alpha); g.add_color_stop_rgba(1, BONE_D[0], BONE_D[1], BONE_D[2], alpha)
        ctx.set_source(g); ctx.fill()
        # apófisis (la "espina" hacia atrás)
        ctx.new_path(); ctx.move_to(-w / 2 + 2, -vh * 0.3); ctx.line_to(-w / 2 - 14 * s, 0); ctx.line_to(-w / 2 + 2, vh * 0.3); ctx.close_path()
        rgba(ctx, BONE_D, alpha); ctx.fill(); ctx.restore()
        y -= vh
        if i < 23:
            kd = clamp(nb - i - 0.5)
            if kd <= 0: break
            dw = w * 0.9; xd = cx + 26 * s * math.sin((i + 0.5) / 23 * math.pi * 1.7 - 0.4)
            bulge = 1 + 0.25 * squash + wob * 0.06 * math.sin(t * 9 + i)
            c = mixc(DISC, WATER, water)
            if hl == i: c = ACCENT
            rrect(ctx, xd - dw * bulge / 2, y - dh, dw * bulge * kd, dh, dh / 2); rgba(ctx, c, alpha); ctx.fill()
            if water > 0: glow(ctx, xd, y - dh / 2, dw * 0.7, WATER, 0.25 * water * alpha)
            y -= dh
    return y

def clock2(ctx, x, y, r, mins, alpha=1.0, sweep=None):
    """Reloj con minutero en 'mins' (0..60) y horario acorde; sweep = (m0, m1) pinta el sector recorrido."""
    ctx.arc(x, y, r, 0, 2 * math.pi); ctx.set_source_rgba(0.03, 0.05, 0.1, 0.92 * alpha); ctx.fill_preserve()
    ctx.set_line_width(9); rgba(ctx, WHITE, alpha); ctx.stroke()
    if sweep:
        a0 = sweep[0] / 60 * 2 * math.pi - math.pi / 2; a1 = sweep[1] / 60 * 2 * math.pi - math.pi / 2
        ctx.move_to(x, y); ctx.arc(x, y, r * 0.88, a0, a1); ctx.close_path(); rgba(ctx, ACCENT, 0.35 * alpha); ctx.fill()
    ctx.set_line_width(5); rgba(ctx, WHITE, 0.7 * alpha)
    for k in range(12):
        a = k * math.pi / 6; ctx.move_to(x + r * 0.8 * math.cos(a), y + r * 0.8 * math.sin(a)); ctx.line_to(x + r * 0.9 * math.cos(a), y + r * 0.9 * math.sin(a))
    ctx.stroke()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    a = mins / 60 * 2 * math.pi - math.pi / 2; ctx.set_line_width(10); rgba(ctx, ACCENT, alpha)
    ctx.move_to(x, y); ctx.line_to(x + r * 0.72 * math.cos(a), y + r * 0.72 * math.sin(a)); ctx.stroke()
    a2 = (7 + mins / 60) / 12 * 2 * math.pi - math.pi / 2; ctx.set_line_width(12); rgba(ctx, WHITE, alpha)
    ctx.move_to(x, y); ctx.line_to(x + r * 0.45 * math.cos(a2), y + r * 0.45 * math.sin(a2)); ctx.stroke()
    ctx.arc(x, y, 12, 0, 2 * math.pi); rgba(ctx, ACCENT, alpha); ctx.fill()

def tape_measure(ctx, x, y, ext, t, alpha=1.0):
    """Cinta métrica: caja en (x, y) y cinta que sale hacia la derecha 'ext' px."""
    if ext > 0:
        rrect(ctx, x + 60, y + 40, ext, 64, 6); rgba(ctx, ACCENT, alpha); ctx.fill()
        ctx.set_line_width(3); rgba(ctx, NAVY, alpha)
        for i in range(int(ext / 14)):
            xx = x + 60 + i * 14; L = 30 if i % 5 == 0 else 16
            ctx.move_to(xx, y + 40); ctx.line_to(xx, y + 40 + L)
        ctx.stroke()
        for i in range(1, int(ext / 70) + 1):
            text(ctx, str(i * 10), x + 60 + i * 70, y + 86, 22, NAVY, alpha=alpha)
        rrect(ctx, x + 60 + ext - 8, y + 30, 16, 84, 4); ctx.set_source_rgba(0.55, 0.58, 0.62, alpha); ctx.fill()
    rrect(ctx, x - 130, y - 90, 260, 230, 50); rgba(ctx, ORANGE, alpha); ctx.fill()
    ctx.arc(x, y + 25, 72, 0, 2 * math.pi); rgba(ctx, ORANGE_D, alpha); ctx.fill()
    ctx.arc(x, y + 25, 30, 0, 2 * math.pi); ctx.set_source_rgba(0.95, 0.95, 0.95, alpha); ctx.fill()

def astronaut(ctx, x, y, s, t=0.0, rot=0.0, alpha=1.0, stretch=1.0):
    """Astronauta genérico (alto ≈ 2.3·s), centrado en el torso."""
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s * stretch)
    rgba(ctx, hexc("B8C2D0"), alpha); rrect(ctx, -0.48, -0.5, 0.96, 0.8, 0.12); ctx.fill()           # mochila
    rgba(ctx, SUIT, alpha)
    for sg in (-1, 1):
        sw = 0.15 * math.sin(t * 1.5 + sg)
        ctx.save(); ctx.translate(sg * 0.38, -0.3); ctx.rotate(sg * (0.5 + sw)); rrect(ctx, -0.12, 0, 0.24, 0.72, 0.12); ctx.fill(); ctx.restore()
        ctx.save(); ctx.translate(sg * 0.16, 0.35); ctx.rotate(sg * (0.12 + 0.5 * sw)); rrect(ctx, -0.14, 0, 0.28, 0.85, 0.12); ctx.fill(); ctx.restore()
    rrect(ctx, -0.4, -0.5, 0.8, 0.95, 0.22); ctx.fill()
    rrect(ctx, -0.2, -0.25, 0.4, 0.25, 0.05); ctx.set_source_rgba(0.24, 0.66, 0.99, alpha); ctx.fill()
    ctx.arc(0, -0.78, 0.36, 0, 2 * math.pi); rgba(ctx, SUIT, alpha); ctx.fill()
    ctx.save(); ctx.translate(0.04, -0.78); ctx.scale(0.26, 0.2); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
    g = cairo.LinearGradient(-0.2, -0.95, 0.25, -0.6); g.add_color_stop_rgba(0, 0.98, 0.8, 0.35, alpha); g.add_color_stop_rgba(1, 0.75, 0.45, 0.1, alpha)
    ctx.set_source(g); ctx.fill()
    ctx.arc(-0.05, -0.85, 0.06, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, 0.7 * alpha); ctx.fill()
    ctx.restore()

def earth(ctx, x, y, r, t, alpha=1.0):
    if alpha <= 0 or r <= 0: return
    glow(ctx, x, y, r * 1.25, BLUE, 0.5 * alpha)
    ctx.save(); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.clip()
    g = cairo.RadialGradient(x - r * 0.3, y - r * 0.3, r * 0.1, x, y, r)
    g.add_color_stop_rgba(0, 0.25, 0.6, 0.95, alpha); g.add_color_stop_rgba(1, 0.05, 0.22, 0.55, alpha); ctx.set_source(g); ctx.paint()
    off = (t * 0.08 * r) % (2 * r)
    for (cx, cy, rr) in [(-0.4, -0.2, 0.35), (0.3, 0.25, 0.28), (0.55, -0.45, 0.2), (-0.1, 0.6, 0.22)]:
        for sh in (0, 2 * r):
            ctx.save(); ctx.translate(x + cx * r + off - sh, y + cy * r); ctx.scale(rr * r, rr * r * 0.7); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
            ctx.set_source_rgba(0.25, 0.7, 0.35, 0.9 * alpha); ctx.fill()
    ctx.restore()

def iss(ctx, x, y, s, alpha=1.0):
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rgba(ctx, hexc("C8CEE0"), alpha); ctx.rectangle(-1.2, -0.04, 2.4, 0.08); ctx.fill()
    for px in (-1.05, -0.65, 0.65, 1.05):
        for py in (-1, 1):
            ctx.rectangle(px - 0.15, py * 0.08 if py > 0 else -0.6, 0.3, 0.52); ctx.set_source_rgba(0.85, 0.62, 0.2, alpha); ctx.fill()
            ctx.set_line_width(0.015); ctx.set_source_rgba(0.4, 0.25, 0.05, alpha)
            for k in range(1, 5):
                yy = (py * 0.08 if py > 0 else -0.6) + k * 0.104; ctx.move_to(px - 0.15, yy); ctx.line_to(px + 0.15, yy)
            ctx.stroke()
    rgba(ctx, SUIT, alpha); rrect(ctx, -0.35, -0.12, 0.7, 0.24, 0.1); ctx.fill(); rrect(ctx, -0.1, -0.35, 0.2, 0.7, 0.08); ctx.fill()
    ctx.restore()

def bed(ctx, x, y, w, t, alpha=1.0, sleep=1.0):
    """Cama con persona acostada (cabeza a la izquierda)."""
    if alpha <= 0: return
    rgba(ctx, WOOD, alpha); rrect(ctx, x - w / 2 - 20, y - 150, 40, 260, 14); ctx.fill(); rrect(ctx, x + w / 2 - 20, y - 70, 40, 180, 14); ctx.fill()
    rrect(ctx, x - w / 2, y + 30, w, 40, 10); ctx.fill()
    rgba(ctx, WHITE, alpha); rrect(ctx, x - w / 2 + 10, y - 30, w - 20, 64, 22); ctx.fill()
    rrect(ctx, x - w / 2 + 30, y - 85, 150, 60, 28); ctx.fill()
    br = 1 + 0.03 * math.sin(t * 2.4)
    ctx.arc(x - w / 2 + 120, y - 90, 52, 0, 2 * math.pi); rgba(ctx, SKIN, alpha); ctx.fill()
    ctx.save(); ctx.translate(0, (1 - br) * 30)
    rrect(ctx, x - w / 2 + 170, y - 95 * br, w - 210, 75 * br, 32); rgba(ctx, BLANKET, alpha); ctx.fill(); ctx.restore()
    if sleep > 0:
        for i in range(3):
            ph = (t * 0.7 + i / 3) % 1
            text(ctx, "z", x - w / 2 + 170 + 60 * ph + i * 10, y - 170 - 160 * ph, 40 + 26 * i, WHITE, stroke=6, alpha=sleep * alpha * (1 - ph))

def updown(ctx, x, y, n, color, t, alpha=1.0, up=False, spacing=120, L=110):
    if alpha <= 0: return
    for i in range(n):
        xx = x + (i - (n - 1) / 2) * spacing; ph = (t * 1.6 + i * 0.3) % 1
        yy = y + (-1 if up else 1) * ph * 40
        if up: arrow(ctx, xx, yy + L / 2, xx, yy - L / 2, color, alpha * (1 - 0.6 * ph), 12, 36)
        else: arrow(ctx, xx, yy - L / 2, xx, yy + L / 2, color, alpha * (1 - 0.6 * ph), 12, 36)

def pie(ctx, x, y, r, frac, alpha=1.0):
    ctx.arc(x, y, r, 0, 2 * math.pi); ctx.set_source_rgba(0.03, 0.05, 0.12, 0.9 * alpha); ctx.fill_preserve()
    ctx.set_line_width(8); rgba(ctx, WHITE, 0.6 * alpha); ctx.stroke()
    if frac > 0:
        ctx.move_to(x, y); ctx.arc(x, y, r * 0.92, -math.pi / 2, -math.pi / 2 + 2 * math.pi * frac); ctx.close_path(); rgba(ctx, ACCENT, alpha); ctx.fill()
    ctx.set_line_width(6); rgba(ctx, WHITE, 0.9 * alpha); ctx.move_to(x, y - r); ctx.line_to(x, y + r); ctx.stroke()

def doc_icon(ctx, x, y, s, alpha=1.0):
    if alpha <= 0 or s <= 0: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rrect(ctx, -0.75, -1, 1.5, 2, 0.12); rgba(ctx, WHITE, alpha); ctx.fill()
    ctx.set_line_width(0.08); rgba(ctx, GREY, alpha)
    for k in range(5): ctx.move_to(-0.5, -0.55 + k * 0.28); ctx.line_to(0.5 - (0.3 if k == 4 else 0), -0.55 + k * 0.28)
    ctx.stroke()
    for k, hh in enumerate((0.25, 0.45, 0.35)):
        ctx.rectangle(-0.45 + k * 0.32, 0.85 - hh, 0.2, hh); rgba(ctx, BLUE, alpha); ctx.fill()
    ctx.restore()

# ---------------- scenes ----------------
def s_hook(ctx, t):  # 0–2.5: texto + movimiento desde el cuadro 0
    sh = ease((t - 1.3) / 0.9)
    bg(ctx, t, day=0.8 * (1 - sh), night=0.7 * sh)
    text(ctx, "ESTA MAÑANA", W / 2, 300, 124, ACCENT, stroke=16)
    text(ctx, "eras MÁS ALTO", W / 2, 440, 108, WHITE, stroke=14)
    # sol que se pone y luna que sale (el día pasa)
    sun(ctx, 830, lerp(640, 900, sh), 56, t, 1 - sh)
    moon(ctx, 830, lerp(980, 660, sh), 54, sh)
    foot = 1250; h0 = 640; h = h0 - 70 * ease((t - 1.0) / 1.0)
    ruler(ctx, 360, foot - 720, foot)
    person(ctx, 560, foot, h * (1 + 0.006 * math.sin(t * 6)))
    dashed(ctx, 330, 760, foot - h0 - 4, ACCENT, 1.0)
    if t > 1.0:
        y1 = foot - h * 1.0; dashed(ctx, 330, 760, y1, RED, ease((t - 1.0) / 0.3))
        bracket(ctx, 290, foot - h0 - 4, y1, RED, ease((t - 1.3) / 0.3))
        pop_text(ctx, "?", 220, (foot - h0 + y1) / 2, 90, RED, t, 1.6, stroke=10)

def s_tape(ctx, t):  # 2.5–4.72
    bg(ctx, t)
    header(ctx, "No es un", "ERROR", t, 2.55, size=96, c2=RED)
    ext = 640 * ease((t - 2.6) / 1.0)
    tape_measure(ctx, 230, 860, ext, t)
    if t > 3.6: label(ctx, "DE LA CINTA MÉTRICA", W / 2, 1140, 50, WHITE, ease((t - 3.6) / 0.3))
    check(ctx, 820, 640, 70 * back((t - 4.0) / 0.35))

def s_spine(ctx, t):  # 4.72–9.15
    wat = ease((t - 7.6) / 0.6)
    bg(ctx, t)
    if t < 7.45: header(ctx, "Entre tus", "VÉRTEBRAS", t, 4.78, size=86, c2=BONE)
    else: header(ctx, "Cojines llenos de", "AGUA", t, 7.5, size=78, c2=WATER)
    b = ease((t - 4.9) / 1.6)
    spine(ctx, 350, 1270, 0.92, water=wat, built=b, t=t, wob=wat)
    if t > 6.05:
        n = int(23 * ease((t - 6.05) / 0.6))
        ctx.save(); ctx.translate(760, 760); s = back((t - 6.05) / 0.3); ctx.scale(s, s)
        counter_box(ctx, 0, 0, n, "", size=150); ctx.restore()
        label(ctx, "DISCOS", 760, 900, 54, WHITE, ease((t - 6.6) / 0.3))
    if t > 7.6:
        # cojín de agua ampliado
        k = back((t - 7.6) / 0.4)
        ctx.save(); ctx.translate(760, 1110); ctx.scale(k, k)
        rrect(ctx, -170, -60, 340, 120, 60); rgba(ctx, WATER); ctx.fill()
        ctx.set_line_width(6); ctx.set_source_rgba(1, 1, 1, 0.6)
        for j in range(2):
            ctx.move_to(-130, -10 + j * 35)
            for xx in range(-130, 131, 10): ctx.line_to(xx, -10 + j * 35 + 8 * math.sin(xx / 22 + t * 6 + j))
            ctx.stroke()
        ctx.restore()
        if k > 0.5:
            ctx.set_line_width(4); ctx.set_source_rgba(1, 1, 1, 0.4); ctx.set_dash([10, 8])
            ctx.move_to(420, 900); ctx.line_to(590, 1060); ctx.stroke(); ctx.set_dash([])

def s_gravity(ctx, t):  # 9.15–13.25
    bg(ctx, t, day=0.7)
    if t < 10.3: header(ctx, "Durante el", "DÍA", t, 9.2, size=104)
    elif t < 12.0: header(ctx, "La gravedad los", "APLASTA", t, 10.35, size=80, c2=RED)
    else: header(ctx, "Y les exprime el", "AGUA", t, 12.05, size=78, c2=WATER)
    sun(ctx, 830, 560, 60, t, ease((t - 9.2) / 0.4))
    sq = ease((t - 10.9) / 1.0)
    top = spine(ctx, 400, 1270, 0.82, squash=sq, water=1 - 0.5 * ease((t - 12.0) / 1.0), t=t)
    if t > 10.4: updown(ctx, 400, top - 110, 3, RED, t, ease((t - 10.4) / 0.3), spacing=110, L=100)
    if t > 12.0:
        random.seed(12)
        for i in range(16):
            ph = random.random() * 0.5; side = -1 if i % 2 else 1; yy0 = random.uniform(top + 60, 1240)
            u = clamp((t - 12.0 - ph) / 0.9)
            if 0 < u < 1:
                drop(ctx, 400 + side * (70 + 260 * u), yy0 + 140 * u * u, 16, 1 - u * 0.6, rot=side * 0.6)
    if t > 12.5: label(ctx, "SALE LÍQUIDO", 780, 820, 46, WATER, ease((t - 12.5) / 0.3))

def s_result(ctx, t):  # 13.25–18.3
    bg(ctx, t, day=0.3)
    if t < 14.2: header(ctx, "", "RESULTADO:", t, 13.3, size=104)
    else: header(ctx, "Pierdes", "CASI 2 CM", t, 14.25, size=96)
    foot = 1230; h1 = 600; h2 = 545
    ruler(ctx, W / 2, foot - 680, foot, ease((t - 13.3) / 0.3))
    k1 = back((t - 13.4) / 0.4); k2 = back((t - 13.6) / 0.4)
    person(ctx, 290, foot, h1 * k1, PERSON); person(ctx, 790, foot, h2 * k2, PERSON2)
    if t > 14.3:
        a = ease((t - 14.3) / 0.3)
        dashed(ctx, 180, 900, foot - h1, ACCENT, a); dashed(ctx, 560, 900, foot - h2, RED, a)
        bracket(ctx, 950, foot - h1, foot - h2, RED, a)
    if t > 15.35:
        ctx.save(); ctx.translate(W / 2, 470); s = back((t - 15.35) / 0.3); ctx.scale(s, s)
        counter_box(ctx, 0, 0, "-2", "cm", color=RED, size=110, sub=56); ctx.restore()
    sun(ctx, 290, foot + 80, 30, t, ease((t - 16.6) / 0.3))
    moon(ctx, 790, foot + 80, 30, ease((t - 17.5) / 0.3), bgc=NAVY)
    if t > 16.7: label(ctx, "AL LEVANTARTE", 290, 1490, 40, ACCENT, ease((t - 16.7) / 0.3))
    if t > 17.5: label(ctx, "AL ACOSTARTE", 760, 1490, 40, PERSON2, ease((t - 17.5) / 0.3))

def s_twist(ctx, t):  # 18.3–20.76
    bg(ctx, t)
    sh = 8 * math.sin(t * 50) * clamp((t - 19.84) / 0.1) * (1 - clamp((t - 20.3) / 0.2))
    pop_text(ctx, "PERO LO", W / 2 + sh, 470, 130, WHITE, t, 18.35)
    pop_text(ctx, "MÁS LOCO", W / 2 + sh, 630, 140, ACCENT, t, 19.0)
    pop_text(ctx, "ES LA VELOCIDAD", W / 2 + sh, 800, 108, RED, t, 19.84)
    k = back((t - 18.5) / 0.4)
    if k > 0:
        m = (t - 18.5) * 40
        clock2(ctx, W / 2, 1110, 150 * k, m % 60)
        for i in range(4):
            ph = (t * 2 + i / 4) % 1
            ctx.set_line_width(8); ctx.set_source_rgba(1, 1, 1, 0.5 * (1 - ph)); ctx.move_to(W / 2 - 200 - 200 * ph, 1040 + i * 45); ctx.line_to(W / 2 - 280 - 200 * ph, 1040 + i * 45); ctx.stroke()

def s_study(ctx, t):  # 20.76–26.08
    bg(ctx, t, day=0.4 * ease((t - 24.0) / 0.5))
    if t < 21.7: header(ctx, "En un", "ESTUDIO", t, 20.8, size=104)
    elif t < 24.05: header(ctx, "Más de", "LA MITAD", t, 21.75, size=100)
    else: header(ctx, "En la", "PRIMERA HORA", t, 24.1, size=90)
    doc_icon(ctx, W / 2, 760, 150 * back((t - 20.85) / 0.35) * (1 - ease((t - 21.6) / 0.3)))
    if t > 21.7:
        k = back((t - 21.75) / 0.35)
        frac = 0.54 * ease((t - 22.0) / 1.2)
        ctx.save(); ctx.translate(330, 800); ctx.scale(k, k); pie(ctx, 0, 0, 210, frac); ctx.restore()
        if t > 22.9: text(ctx, "54 %", 330, 1080, 86, ACCENT, stroke=12, alpha=ease((t - 22.9) / 0.3))
        if t > 23.0: label(ctx, "DE LO QUE PIERDES", 330, 1180, 40, WHITE, ease((t - 23.0) / 0.3))
    if t > 24.05:
        k = back((t - 24.1) / 0.4); m = 60 * ease((t - 24.3) / 1.2)
        ctx.save(); ctx.translate(780, 800); ctx.scale(k, k); clock2(ctx, 0, 0, 160, m, sweep=(0, m)); ctx.restore()
        if t > 24.7: label(ctx, "1 HORA", 780, 1040, 50, ACCENT, ease((t - 24.7) / 0.3))
        sun(ctx, 780, 1160, 34, t, ease((t - 25.3) / 0.3))
        if t > 25.3: label(ctx, "TRAS LEVANTARTE", 780, 1250, 38, WHITE, ease((t - 25.4) / 0.3))

def s_night(ctx, t):  # 26.08–31.1
    bg(ctx, t, night=1.0)
    if t < 29.45: header(ctx, "En la", "NOCHE", t, 26.12, size=104, c2=PERSON2)
    else: header(ctx, "", "RECUPERAS TU ALTURA", t, 29.5, size=80, c2=GREEN)
    moon(ctx, 880, 450, 56, ease((t - 26.1) / 0.4))
    bed(ctx, W / 2, 1180, 760, t, ease((t - 26.4) / 0.4), sleep=1 - ease((t - 29.5) / 0.4))
    # columna acostada que se rehidrata
    if t > 27.9:
        a = ease((t - 27.9) / 0.4); inf = ease((t - 28.5) / 0.9)
        ctx.save(); ctx.translate(140, 780); ctx.rotate(math.pi / 2)
        spine(ctx, 0, 0, 0.72, squash=1 - inf, water=0.5 + 0.5 * inf, t=t, alpha=a, wob=inf)
        ctx.restore()
        if t > 28.6: label(ctx, "SE VUELVEN A LLENAR", W / 2, 600, 44, WATER, ease((t - 28.6) / 0.3))
    if t > 29.6:
        updown(ctx, 860, 900, 1, GREEN, t, ease((t - 29.6) / 0.3), up=True, L=120)
        pop_text(ctx, "+2 cm", 860, 1010, 64, GREEN, t, 29.8, stroke=10)

def s_nograv(ctx, t):  # 31.1–34.3
    sp = ease((t - 31.2) / 1.6)
    bg(ctx, t, night=1 - sp, space=sp)
    if t < 32.25: header(ctx, "Ahora", "IMAGINA…", t, 31.15, size=104)
    else: header(ctx, "", "SIN GRAVEDAD", t, 32.3, size=110, c2=PURPLE_C)
    r = lerp(900, 170, ease((t - 31.4) / 2.2)); ey = lerp(1900, 1080, ease((t - 31.4) / 2.2))
    earth(ctx, W / 2, ey, r, t)
    if t > 32.4:
        a = ease((t - 32.4) / 0.3)
        updown(ctx, W / 2, 700, 3, RED, t, a, spacing=130, L=110)
        cross(ctx, W / 2, 700, 90 * back((t - 32.8) / 0.35))
    astronaut(ctx, 300, 640 + 20 * math.sin(t * 1.4), 90 * back((t - 33.3) / 0.4), t, rot=0.3 * math.sin(t * 0.8))

def s_space(ctx, t):  # 34.3–38.2
    bg(ctx, t, space=1.0)
    if t < 36.25: header(ctx, "En el", "ESPACIO", t, 34.35, size=104, c2=PURPLE_C)
    else: header(ctx, "Los astronautas", "CRECEN", t, 36.3, size=84, c2=GREEN)
    earth(ctx, 900, 1500, 260, t, 0.9)
    st = ease((t - 36.3) / 1.0)
    astronaut(ctx, 360, 820 + 15 * math.sin(t * 1.3), 200 * back((t - 34.5) / 0.4), t, rot=0.12 * math.sin(t * 0.9), stretch=1 + 0.09 * st)
    if t > 36.3:
        updown(ctx, 360, 470, 1, GREEN, t, ease((t - 36.3) / 0.3), up=True, L=100)
        top = spine(ctx, 760, 1060, 0.6, squash=-0.6 * st, water=1.0, t=t, alpha=ease((t - 36.4) / 0.3))
    if t > 37.0:
        ctx.save(); ctx.translate(760, 1170); s = back((t - 37.0) / 0.3); ctx.scale(s, s)
        counter_box(ctx, 0, 0, f"+{int(round(3 * ease((t - 37.0) / 0.6)))}", "%", color=GREEN, size=120, sub=70); ctx.restore()

def s_kelly(ctx, t):  # 38.2–43.5
    bg(ctx, t, space=1.0)
    header(ctx, "", "SCOTT KELLY", t, 38.25, size=104)
    if t > 38.9: label(ctx, "ASTRONAUTA", W / 2, 400, 42, hexc("C8CEE0"), ease((t - 38.9) / 0.3), bg=False)
    iss(ctx, 730, 560 + 10 * math.sin(t), 165 * back((t - 39.7) / 0.5))
    if t > 39.6:
        n = int(365 * ease((t - 39.6) / 1.2))
        ctx.save(); ctx.translate(730, 790); s = back((t - 39.6) / 0.3); ctx.scale(s, s)
        counter_box(ctx, 0, 0, n, "DÍAS", size=96, sub=44); ctx.restore()
    st = ease((t - 41.6) / 0.9)
    foot = 1300; h0 = 480; h = h0 * (1 + 0.12 * st)
    ruler(ctx, 140, foot - 620, foot, ease((t - 38.3) / 0.3))
    ax = 300
    astronaut(ctx, ax, foot - h / 2 - 20, 0.0 if t < 38.3 else (h0 / 2.3) * back((t - 38.3) / 0.4), t, stretch=1 + 0.12 * st)
    dashed(ctx, 110, 470, foot - h0 - 30, WHITE, ease((t - 38.6) / 0.3))
    if t > 41.6:
        dashed(ctx, 110, 470, foot - h - 30, GREEN, ease((t - 41.6) / 0.3))
        bracket(ctx, 520, foot - h - 30, foot - h0 - 30, GREEN, ease((t - 41.8) / 0.3))
    if t > 41.9:
        ctx.save(); ctx.translate(730, 1040); s = back((t - 41.9) / 0.3); ctx.scale(s, s)
        counter_box(ctx, 0, 0, "+5", "cm", color=GREEN, size=120, sub=60); ctx.restore()
    if t > 42.7: label(ctx, "MÁS ALTO", 730, 1170, 46, WHITE, ease((t - 42.7) / 0.3))

def s_return(ctx, t):  # 43.5–46.88
    sp = 1 - ease((t - 43.5) / 1.4)
    bg(ctx, t, day=0.6 * (1 - sp), space=sp)
    if t < 45.1: header(ctx, "Al volver a la", "TIERRA", t, 43.55, size=90, c2=BLUE)
    else: header(ctx, "La gravedad", "SE LOS QUITÓ", t, 45.15, size=84, c2=RED)
    gy = lerp(2400, 1300, ease((t - 43.5) / 1.2))
    ctx.rectangle(0, gy, W, H - gy); ctx.set_source_rgba(0.2, 0.45, 0.25, 1); ctx.fill()
    ctx.rectangle(0, gy, W, 14); ctx.set_source_rgba(0.35, 0.7, 0.35, 1); ctx.fill()
    sh = ease((t - 45.3) / 0.9)
    h0 = 480; h = h0 * (1.12 - 0.12 * sh); foot = gy
    ruler(ctx, 140, foot - 620, foot)
    land = ease((t - 43.6) / 1.2)
    astronaut(ctx, 360, lerp(500, foot - h / 2 - 20, land), h0 / 2.3, t * (1 - land), rot=0.3 * (1 - land), stretch=1.12 - 0.12 * sh)
    dashed(ctx, 110, 520, foot - h0 * 1.12 - 30, GREEN, 0.8 * (1 - sh))
    dashed(ctx, 110, 520, foot - h0 - 30, WHITE, ease((t - 45.3) / 0.3))
    if t > 45.2: updown(ctx, 360, foot - h - 200, 3, RED, t, ease((t - 45.2) / 0.3), spacing=110, L=90)
    if t > 46.1:
        ctx.save(); ctx.translate(780, 900); s = back((t - 46.1) / 0.3); ctx.scale(s, s)
        counter_box(ctx, 0, 0, "-5", "cm", color=RED, size=110, sub=56); ctx.restore()

def s_ask(ctx, t):  # 46.88–48.84
    bg(ctx, t, day=0.4)
    pop_text(ctx, "¿A QUÉ HORA", W / 2, 400, 112, WHITE, t, 46.92)
    pop_text(ctx, "TE VAS A MEDIR?", W / 2, 540, 96, ACCENT, t, 47.6)
    k = back((t - 47.0) / 0.4)
    ctx.save(); ctx.translate(330, 880); ctx.scale(k, k); clock2(ctx, 0, 0, 160, (t * 20) % 60); ctx.restore()
    ruler(ctx, 760, 700, 1240, ease((t - 47.2) / 0.3))
    for i, (qx, qy) in enumerate([(240, 1170), (450, 1210)]):
        pop_text(ctx, "?", qx, qy, 110, [ACCENT, PERSON2][i], t, 47.8 + i * 0.25)

def s_end(ctx, t):  # 48.84–end
    T0 = 48.84
    bg(ctx, t)
    a = ease((t - T0) / 0.5)
    astronaut(ctx, lerp(-150, 1230, ((t - T0) / 5.0) % 1), 1470, 60, t, rot=t * 0.6, alpha=a)
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

SCENES = [(0.0, s_hook), (2.5, s_tape), (4.72, s_spine), (9.15, s_gravity), (13.25, s_result), (18.3, s_twist), (20.76, s_study),
          (26.08, s_night), (31.1, s_nograv), (34.3, s_space), (38.2, s_kelly), (43.5, s_return), (46.88, s_ask), (48.84, s_end)]
END_START = 48.84
HOOK_END = 2.5

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
EMPH = {"VÉRTEBRAS", "VEINTITRÉS", "DISCOS", "AGUA", "GRAVEDAD", "APLASTA", "EXPRIME", "LÍQUIDO", "DOS", "CENTÍMETROS", "LOCO",
        "VELOCIDAD", "MITAD", "PRIMERA", "HORA", "HINCHARSE", "ALTURA", "ESPACIO", "TRES", "CIENTO", "CINCO", "TIERRA", "QUITÓ", "MEDIR", "CRECEN"}
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
