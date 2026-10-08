"""
Builds every animated tile in ../assets for the profile README.

Design language: the Apple web design system reference —
  · one accent: Action Blue #0066cc (Sky Link Blue #2997ff on dark tiles)
  · surfaces alternate white / parchment #f5f5f7 / graphite #272729 — the colour change is the divider
  · SF Pro (system stack) with an embedded Inter fallback, weights 300/400/600, tight tracking at display sizes
  · no gradients or shadows on UI; shading lives only inside the product "renders",
    and the single product shadow rgba(0,0,0,.22) 3px 5px 30px sits under them
  · motion: one keynote reveal in the hero; one slow, purposeful loop per render

Run from anywhere:  python3 tools/gen.py
Needs: fonttools + brotli  (pip install fonttools brotli)
"""
import base64, io, math, os, random, re

from fontTools.subset import Subsetter, Options
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets")
FONTS = {w: os.path.join(HERE, "fonts", f"inter-latin-{w}-normal.woff2") for w in (300, 400, 600)}
os.makedirs(OUT, exist_ok=True)
random.seed(11)

# ── tokens ───────────────────────────────────────────────────────────────
W = 1200
CANVAS, PARCH, PEARL = "#ffffff", "#f5f5f7", "#fafafc"
TILE1, TILE2, TILE3, BLACK = "#272729", "#2a2a2c", "#252527", "#000000"
INK, INK80, INK48 = "#1d1d1f", "#333333", "#7a7a7a"
ON_DARK, MUTED_DARK = "#ffffff", "#cccccc"
BLUE, BLUE_FOCUS, BLUE_DARK = "#0066cc", "#0071e3", "#2997ff"
HAIR = "#e0e0e0"
FAMILY = "'SF Pro Display','SF Pro Text',-apple-system,BlinkMacSystemFont,'InterE',system-ui,'Segoe UI',Helvetica,Arial,sans-serif"
EASE = "cubic-bezier(.22,.8,.24,1)"

_metrics = {w: TTFont(p) for w, p in FONTS.items()}
_used_chars = set()


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def track(size):
    """'Apple tight' tracking, nudged for Inter as the reference suggests."""
    if size >= 40:
        return -0.018 * size
    if size >= 22:
        return -0.014 * size
    return -0.01 * size


def measure(s, size, weight=400, ls=None):
    f = _metrics[weight]
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    adv = sum(hmtx[cmap[ord(ch)]][0] if ord(ch) in cmap else upm * .5 for ch in s)
    ls = track(size) if ls is None else ls
    return adv / upm * size + ls * (len(s) - 1)


def t(x, y, s, size, weight=400, fill=INK, anchor="middle", ls=None, cls="", extra=""):
    _used_chars.update(s)
    ls = track(size) if ls is None else ls
    c = f' class="{cls}"' if cls else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" letter-spacing="{ls:.2f}"{c} {extra}>{esc(s)}</text>')


def font_css():
    sub_text = "".join(sorted(_used_chars | set(" 0123456789")))
    css = []
    for w, p in FONTS.items():
        opts = Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "liga", "calt", "ss03", "tnum"]
        f = TTFont(p)
        sub = Subsetter(opts)
        sub.populate(text=sub_text)
        sub.subset(f)
        buf = io.BytesIO()
        f.flavor = "woff2"
        f.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        css.append(f'@font-face{{font-family:"InterE";font-weight:{w};src:url(data:font/woff2;base64,{b64}) format("woff2")}}')
    return "\n".join(css)


def svg(h, bg, body, defs="", css=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img">
<style>
/*FONTS*/
text{{font-family:{FAMILY};font-feature-settings:"ss03","kern";-webkit-font-smoothing:antialiased}}
.fx{{transform-box:fill-box;transform-origin:center}}
@media (prefers-reduced-motion:reduce){{*{{animation-duration:.01s!important;animation-delay:0s!important;animation-iteration-count:1!important}}}}
{css}
</style>
<defs>
<filter id="ps" x="-30%" y="-30%" width="160%" height="170%"><feDropShadow dx="3" dy="5" stdDeviation="15" flood-color="#000" flood-opacity=".22"/></filter>
{defs}
</defs>
<rect width="{W}" height="{h}" fill="{bg}"/>
{body}
</svg>'''


def links(y, items, dark):
    """Apple tile link row: 'Learn more ›' style, blue, centred as a group."""
    col = BLUE_DARK if dark else BLUE
    size, gap = 24, 56
    widths = [measure(s + " ›", size) for s in items]
    x = W / 2 - (sum(widths) + gap * (len(items) - 1)) / 2
    out = []
    for s, w in zip(items, widths):
        out.append(t(x, y, s + " ›", size, 400, col, "start"))
        x += w + gap
    return "\n".join(out)


def tile_head(title, tagline, desc, link_items, dark, y0=128):
    fg = ON_DARK if dark else INK
    sub = MUTED_DARK if dark else INK80
    return "\n".join([
        t(W/2, y0, title, 64, 600, fg),
        t(W/2, y0 + 60, tagline, 36, 400, fg),
        t(W/2, y0 + 108, desc, 23, 400, sub),
        links(y0 + 160, link_items, dark),
    ])


def anim(attr, values, dur, kt=None, begin="0s", extra=""):
    k = f' keyTimes="{kt}"' if kt else ""
    return f'<animate attributeName="{attr}" values="{values}"{k} dur="{dur}s" begin="{begin}" repeatCount="indefinite" {extra}/>'


# ── glyphs used on the hero "screen" icons (drawn in a 56×56 box, centred at 0,0) ──
GLYPHS = {
    "HotelOS": '<path d="M-15 9V-9M-15 3H15V9M-15 -1H15M-9 -1V-5a3 3 0 0 1 3-3h6a3 3 0 0 1 3 3v4" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>',
    "HELIX": '<path d="M-14 -12C-4 -12 4 12 14 12M-14 12C-4 12 4 -12 14 -12M-9 -6H9M-9 6H9M-3 0H3" stroke="#fff" stroke-width="2.4" stroke-linecap="round" fill="none"/>',
    "KAAVAL": '<path d="M0 -15L12 -10V0C12 8 6 13 0 16C-6 13 -12 8 -12 0V-10Z" stroke="#fff" stroke-width="2.4" stroke-linejoin="round" fill="none"/><circle cy="-1" r="3" fill="#fff"/><path d="M0 2V7" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>',
    "Flood AI": '<path d="M0 -15C6 -6 11 0 11 5A11 11 0 0 1 -11 5C-11 0 -6 -6 0 -15Z" stroke="#fff" stroke-width="2.4" stroke-linejoin="round" fill="none"/><path d="M-6 6Q-3 9 0 6T6 6" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round"/>',
    "RiderShield": '<path d="M-14 6C-14 -8 -4 -14 4 -14C11 -14 15 -8 15 0V6H4V0H-6V6Z" stroke="#fff" stroke-width="2.4" stroke-linejoin="round" fill="none"/><path d="M4 -3H15" stroke="#fff" stroke-width="2.4"/>',
    "ProofStack": '<path d="M0 -14L14 -7L0 0L-14 -7Z M-14 0L0 7L14 0 M-14 7L0 14L14 7" stroke="#fff" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round" fill="none"/>',
}
PROJECTS = [("HotelOS", "Runs the hotel"), ("HELIX", "Heals software"), ("KAAVAL", "Protects sessions"),
            ("Flood AI", "Predicts floods"), ("RiderShield", "Senses the road"), ("ProofStack", "Scores candidates")]


# ════════════════════════════ HERO ════════════════════════════
def hero():
    H = 960
    b = []
    # global nav — thin, true black, quiet links
    b.append(f'<rect width="{W}" height="64" fill="{BLACK}"/>')
    b.append(t(56, 40, "rohith", 20, 600, ON_DARK, "start", extra='opacity=".92"'))
    navs = ["Work", "HotelOS", "HELIX", "KAAVAL", "Flood AI", "RiderShield", "ProofStack", "Contact"]
    x0, x1 = 230, 1000
    for i, n in enumerate(navs):
        b.append(t(x0 + (x1 - x0) * i / (len(navs) - 1), 39, n, 17, 400, ON_DARK, extra='opacity=".8"'))
    b.append('<g transform="translate(1124 32)" stroke="#fff" stroke-opacity=".8" stroke-width="1.8" fill="none"><circle cx="-2" cy="-2" r="7"/><path d="M3 3L8 8" stroke-linecap="round"/></g>')

    # headline stack — the one orchestrated reveal on the page
    b.append(f'<g class="r r1">{t(W/2, 236, "Rohith Pranov.", 96, 600, INK)}</g>')
    b.append(f'<g class="r r2">{t(W/2, 306, "Systems that run, heal, protect,", 40, 400, INK)}{t(W/2, 356, "predict, sense and prove.", 40, 400, INK)}</g>')
    b.append(f'<g class="r r3">{t(W/2, 412, "Computer Science at VIT Vellore, class of 2028.", 23, 400, INK80)}{links(462, ["View the work", "Get in touch"], False)}</g>')

    # laptop render
    sx, sy, sw, sh = 318, 518, 564, 352
    ix, iy, iw, ih = sx + 14, sy + 14, sw - 28, sh - 26
    b.append(f'''<g class="dev">
<g filter="url(#ps)">
<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="22" fill="#0b0b0c" stroke="#a1a1a6" stroke-width="2"/>
<path d="M{sx-74} {sy+sh+2} H{sx+sw+74} L{sx+sw+60} {sy+sh+22} Q{W/2} {sy+sh+30} {sx-60} {sy+sh+22} Z" fill="url(#alu)"/>
<rect x="{W/2-62}" y="{sy+sh+2}" width="124" height="7" rx="3.5" fill="#b8b8bd"/>
</g>
<clipPath id="scr"><rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="10"/></clipPath>
<g clip-path="url(#scr)">
<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" fill="#000"/>
<g class="on">
<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" fill="url(#wall)"/>
<rect x="{ix}" y="{iy}" width="{iw}" height="22" fill="#fff" fill-opacity=".08"/>
{t(ix+16, iy+15, "rohith.os", 11, 600, ON_DARK, "start", extra='opacity=".85"')}
{t(ix+iw-16, iy+15, "9:41", 11, 600, ON_DARK, "end", extra='opacity=".85"')}
</g>''')
    n = len(PROJECTS)
    isz, gap = 58, 18
    gx = W / 2 - (n * isz + (n - 1) * gap) / 2
    gy = iy + 120
    for i, (name, _) in enumerate(PROJECTS):
        cx = gx + i * (isz + gap) + isz / 2
        cy = gy + isz / 2
        b.append(f'''<g class="ic fx" style="animation-delay:{2.25 + i * .09:.2f}s"><rect x="{cx-isz/2:.1f}" y="{gy}" width="{isz}" height="{isz}" rx="14" fill="#1c1c1e" stroke="#fff" stroke-opacity=".14"/>
<g transform="translate({cx:.1f} {cy:.1f})">{GLYPHS[name]}</g></g>''')
    # selection ring + caption cycle (begins after the reveal)
    T = 12
    xs = ";".join(f"{gx + i * (isz + gap) - 4:.1f}" for i in range(n))
    xs_full = ";".join(sum([[f"{gx + i * (isz + gap) - 4:.1f}"] * 2 for i in range(n)], [])) + f";{gx - 4:.1f}"
    kts = ";".join(sum([[f"{i/n:.4f}", f"{(i+1)/n - .03:.4f}"] for i in range(n)], [])) + ";1"
    b.append(f'''<rect y="{gy-4}" width="{isz+8}" height="{isz+8}" rx="17" fill="none" stroke="{BLUE_DARK}" stroke-width="2.5" opacity="0">
<animate attributeName="opacity" values="0;1" dur=".4s" begin="3.2s" fill="freeze"/>
<animate attributeName="x" values="{xs_full}" keyTimes="{kts}" dur="{T}s" begin="3.2s" repeatCount="indefinite" calcMode="spline" keySplines="{';'.join(['.6 0 .2 1'] * (2*n))}"/></rect>''')
    for i, (name, verb) in enumerate(PROJECTS):
        vals = ";".join("1" if j == i else "0" for j in range(n)) + ";0"
        kt = ";".join(f"{j/n:.4f}" for j in range(n)) + ";1"
        b.append(f'''<g opacity="0"><animate attributeName="opacity" values="{vals}" keyTimes="{kt}" dur="{T}s" begin="3.2s" repeatCount="indefinite" calcMode="discrete"/>
{t(W/2, gy + isz + 52, name, 20, 600, ON_DARK)}{t(W/2, gy + isz + 76, verb, 14, 400, MUTED_DARK)}</g>''')
    # glass glare sweeps once as the screen wakes
    b.append(f'<rect class="glare" x="{ix-260}" y="{iy-40}" width="120" height="{ih+80}" fill="#fff" fill-opacity=".07" transform="skewX(-18)"/>')
    b.append('</g></g>')

    defs = f'''<linearGradient id="alu" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e3e3e8"/><stop offset=".55" stop-color="#c7c7cc"/><stop offset="1" stop-color="#9a9aa0"/></linearGradient>
<radialGradient id="wall" cx=".5" cy=".95" r=".9"><stop offset="0" stop-color="#0a3a72"/><stop offset=".55" stop-color="#071a33"/><stop offset="1" stop-color="#030712"/></radialGradient>'''
    css = f'''.r{{opacity:0;animation:up 1.1s {EASE} both}}
.r1{{animation-delay:.15s}} .r2{{animation-delay:.45s}} .r3{{animation-delay:.75s}}
.dev{{opacity:0;animation:rise 1.4s {EASE} .95s both}}
.on{{opacity:0;animation:fade .9s ease 1.9s both}}
.ic{{opacity:0;animation:pop .7s {EASE} both}}
.glare{{animation:glare 1.6s ease-in-out 2.1s both}}
@keyframes up{{from{{opacity:0;transform:translateY(26px)}}to{{opacity:1;transform:none}}}}
@keyframes rise{{from{{opacity:0;transform:translateY(70px)}}to{{opacity:1;transform:none}}}}
@keyframes fade{{to{{opacity:1}}}}
@keyframes pop{{from{{opacity:0;transform:scale(.6)}}to{{opacity:1;transform:scale(1)}}}}
@keyframes glare{{from{{transform:skewX(-18deg) translateX(0)}}to{{transform:skewX(-18deg) translateX(1400px)}}}}'''
    return svg(H, CANVAS, "\n".join(b), defs, css)


# ════════════════════════════ AT A GLANCE ════════════════════════════
def glance():
    H = 470
    b = [t(W/2, 126, "Built, shipped and filed.", 56, 600, INK)]
    stats = [("20+", "projects shipped", "in eight months"), ("6", "flagship systems", "across AI, security, hardware"),
             ("1", "patent application", "filed through VIT"), ("2", "invention disclosures", "with VIT IPR & TT Cell")]
    for i, (num, l1, l2) in enumerate(stats):
        cx = 165 + i * 290
        b.append(t(cx, 278, num, 88, 600, INK))
        b.append(t(cx, 330, l1, 23, 600, INK))
        b.append(t(cx, 362, l2, 21, 400, INK80))
    return svg(H, PARCH, "\n".join(b))


# ════════════════════════════ 001 HotelOS — dark tile, iPad running the ops screen ════════════════════════════
def hotelos():
    H = 860
    T = 9
    b = [tile_head("HotelOS", "Runs the whole hotel.",
                   "Bookings, housekeeping, staff and payments, orchestrated from one conversation.",
                   ["View the code", "Tech specs"], True)]
    dx, dy, dw, dh = 250, 340, 700, 452
    sx, sy, sw, sh = dx + 20, dy + 20, dw - 40, dh - 40
    b.append(f'''<g filter="url(#ps)"><rect x="{dx}" y="{dy}" width="{dw}" height="{dh}" rx="38" fill="#0b0b0c" stroke="#636366" stroke-width="3"/></g>
<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="20" fill="{PARCH}"/>''')
    # sidebar: conversation
    px, py, pw = sx + 18, sy + 18, 236
    b.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{sh-36}" rx="14" fill="#fff"/>')
    b.append(t(px + 16, py + 30, "Room 204", 15, 600, INK, "start"))
    b.append(t(px + 16, py + 50, "WhatsApp guest chat", 11.5, 400, INK48, "start"))
    bubbles = [("Can I check out late?", False, .06), ("Done, 2 pm checkout.", True, .2),
               ("Housekeeping moved to 2:30.", True, .28), ("Perfect, thank you!", False, .44)]
    by = py + 82
    for txt, me, start in bubbles:
        tw = measure(txt, 12.5) + 26
        bx = px + pw - 14 - tw if me else px + 14
        fill, col = (BLUE, "#fff") if me else ("#e9e9eb", INK)
        b.append(f'''<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{start};{start+.04:.2f};.9;1" dur="{T}s" repeatCount="indefinite"/>
<animateTransform attributeName="transform" type="translate" values="0 14;0 14;0 0;0 0;0 0" keyTimes="0;{start};{start+.05:.2f};.9;1" dur="{T}s" repeatCount="indefinite" calcMode="spline" keySplines="0 0 1 1;.2 .8 .2 1;0 0 1 1;0 0 1 1"/>
<rect x="{bx:.1f}" y="{by}" width="{tw:.1f}" height="32" rx="16" fill="{fill}"/>{t(bx + tw/2, by + 21, txt, 12.5, 400, col)}</g>''')
        by += 44
    # typing indicator at the bottom of the chat
    b.append(f'<rect x="{px+14}" y="{py+sh-36-52}" width="{pw-28}" height="34" rx="17" fill="#fff" stroke="{HAIR}"/>')
    b.append(t(px + 30, py + sh - 36 - 30, "Message", 12.5, 400, INK48, "start"))
    # rooms grid
    gx0, gy0 = px + pw + 18, py
    gw = sw - pw - 54
    b.append(f'<rect x="{gx0}" y="{gy0}" width="{gw}" height="216" rx="14" fill="#fff"/>')
    b.append(t(gx0 + 16, gy0 + 30, "Rooms", 15, 600, INK, "start"))
    b.append(t(gx0 + gw - 16, gy0 + 30, "Today", 12, 400, INK48, "end"))
    cols, rows = 6, 3
    cw, ch, g = (gw - 32 - 5 * 8) / 6, 42, 8
    rooms = [101, 102, 103, 104, 105, 106, 201, 202, 203, 204, 205, 206, 301, 302, 303, 304, 305, 306]
    states = ["occ", "ready", "occ", "occ", "ready", "occ", "ready", "occ", "occ", "occ", "ready", "occ", "occ", "ready", "occ", "ready", "occ", "occ"]
    for k, (r, st) in enumerate(zip(rooms, states)):
        cx = gx0 + 16 + (k % cols) * (cw + g)
        cy = gy0 + 48 + (k // cols) * (ch + g)
        fill = "#e9e9eb" if st == "occ" else "#fff"
        stroke = "none" if st == "occ" else HAIR
        extra = ""
        if r == 204:
            extra = f'<animate attributeName="fill" values="#e9e9eb;#e9e9eb;{BLUE};{BLUE};#e9e9eb" keyTimes="0;.2;.24;.9;1" dur="{T}s" repeatCount="indefinite"/>'
        txtcol = INK80
        b.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cw:.1f}" height="{ch}" rx="9" fill="{fill}" stroke="{stroke}">{extra}</rect>')
        if r == 204:
            b.append(f'<text x="{cx+cw/2:.1f}" y="{cy+26:.1f}" font-size="12.5" font-weight="600" fill="{INK80}" text-anchor="middle" letter-spacing="-.1">204<animate attributeName="fill" values="{INK80};{INK80};#fff;#fff;{INK80}" keyTimes="0;.2;.24;.9;1" dur="{T}s" repeatCount="indefinite"/></text>')
            _used_chars.update("204")
        else:
            b.append(t(cx + cw/2, cy + 26, str(r), 12.5, 400, txtcol))
    # occupancy card with drawing line
    oy = gy0 + 232
    oh = sh - 36 - 232
    b.append(f'<rect x="{gx0}" y="{oy}" width="{gw}" height="{oh}" rx="14" fill="#fff"/>')
    b.append(t(gx0 + 16, oy + 30, "Occupancy this week", 15, 600, INK, "start"))
    pts = [0.42, 0.55, 0.5, 0.68, 0.74, 0.7, 0.86]
    lx0, lx1, ly0, ly1 = gx0 + 20, gx0 + gw - 20, oy + oh - 22, oy + 52
    path = " ".join(f"{'M' if i == 0 else 'L'}{lx0 + (lx1-lx0) * i/(len(pts)-1):.1f} {ly0 - (ly0-ly1) * p:.1f}" for i, p in enumerate(pts))
    L = 520
    b.append(f'''<line x1="{lx0}" y1="{ly0}" x2="{lx1}" y2="{ly0}" stroke="{HAIR}"/>
<path d="{path}" stroke="{BLUE}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{L}" stroke-dashoffset="{L}">
<animate attributeName="stroke-dashoffset" values="{L};{L};0;0;{L}" keyTimes="0;.3;.55;.9;1" dur="{T}s" repeatCount="indefinite" calcMode="spline" keySplines="0 0 1 1;.3 0 .2 1;0 0 1 1;.6 0 1 1"/></path>''')
    return svg(H, TILE1, "\n".join(b))


# ════════════════════════════ 002 HELIX — white tile, rotating double helix ════════════════════════════
def helix():
    H = 820
    b = [tile_head("HELIX", "Software that heals itself.",
                   "A control loop modelled on homeostasis: sense, diagnose, correct, verify.",
                   ["Tech specs"], False)]
    T = 12
    cy, A = 560, 112
    N, x0, step = 24, 274, 28
    S = 25
    b.append(f'<ellipse cx="{W/2}" cy="722" rx="330" ry="16" fill="#000" fill-opacity=".10" filter="url(#soft)"/>')
    fmt = lambda arr: ";".join(f"{v:.1f}" for v in arr)
    rungs, front = [], []
    for j in range(N):
        x = x0 + j * step
        ph = j * 0.36
        ang = [2 * math.pi * s / (S - 1) + ph for s in range(S)]
        ya = [cy + A * math.sin(a) for a in ang]
        yb = [2 * cy - y for y in ya]
        za = [math.cos(a) for a in ang]
        ra = [10 + 5.5 * z for z in za]
        rb = [10 - 5.5 * z for z in za]
        oa = [.55 + .45 * (z + 1) / 2 for z in za]
        ob = [.55 + .45 * (1 - z) / 2 for z in za]
        rungs.append(f'<line x1="{x}" x2="{x}" stroke="#d2d2d7" stroke-width="2.5"><animate attributeName="y1" values="{fmt(ya)}" dur="{T}s" repeatCount="indefinite"/><animate attributeName="y2" values="{fmt(yb)}" dur="{T}s" repeatCount="indefinite"/></line>')
        front.append(f'<circle cx="{x}" fill="url(#graphite)"><animate attributeName="cy" values="{fmt(ya)}" dur="{T}s" repeatCount="indefinite"/><animate attributeName="r" values="{fmt(ra)}" dur="{T}s" repeatCount="indefinite"/><animate attributeName="opacity" values="{fmt(oa)}" dur="{T}s" repeatCount="indefinite"/></circle>')
        front.append(f'<circle cx="{x}" fill="url(#blueSphere)"><animate attributeName="cy" values="{fmt(yb)}" dur="{T}s" repeatCount="indefinite"/><animate attributeName="r" values="{fmt(rb)}" dur="{T}s" repeatCount="indefinite"/><animate attributeName="opacity" values="{fmt(ob)}" dur="{T}s" repeatCount="indefinite"/></circle>')
    b += rungs + front
    defs = '''<radialGradient id="graphite" cx=".35" cy=".3" r=".75"><stop offset="0" stop-color="#8e8e93"/><stop offset=".45" stop-color="#3a3a3c"/><stop offset="1" stop-color="#1d1d1f"/></radialGradient>
<radialGradient id="blueSphere" cx=".35" cy=".3" r=".75"><stop offset="0" stop-color="#8cc4ff"/><stop offset=".45" stop-color="#0071e3"/><stop offset="1" stop-color="#004a99"/></radialGradient>
<filter id="soft" x="-20%" y="-200%" width="140%" height="500%"><feGaussianBlur stdDeviation="12"/></filter>'''
    return svg(H, CANVAS, "\n".join(b), defs)


# ════════════════════════════ 003 KAAVAL — graphite tile, machined shield ════════════════════════════
def kaaval():
    H = 840
    T = 6
    b = [tile_head("KAAVAL", "A stolen cookie is worthless.",
                   "PulseLock binds every session to a key that never leaves your browser.",
                   ["View the code", "Tech specs"], True)]
    cx, cy = W / 2, 560
    ln = 300 + 260
    b.append(f'<line x1="150" y1="{cy}" x2="{W-150}" y2="{cy}" stroke="#48484a" stroke-width="2"/>')
    # capsules: the signed request passes behind the shield; the replayed cookie stops at it
    b.append(f'''<g><animateTransform attributeName="transform" type="translate" values="0 0;0 0;{W-300} 0;{W-300} 0" keyTimes="0;.05;.62;1" dur="{T}s" repeatCount="indefinite" calcMode="spline" keySplines="0 0 1 1;.45 0 .55 1;0 0 1 1"/>
<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.06;.58;.64;1" dur="{T}s" repeatCount="indefinite"/>
<rect x="128" y="{cy-15}" width="64" height="30" rx="15" fill="{BLUE_DARK}"/>
<path d="M146 {cy} a5 5 0 1 0 10 0a5 5 0 1 0 -10 0M156 {cy}h18v6M168 {cy}v5" stroke="#fff" stroke-width="2.2" fill="none" stroke-linecap="round"/></g>
<g><animateTransform attributeName="transform" type="translate" values="0 0;0 0;{cx-150-128-60-64:.0f} 0;{cx-150-128-60-64:.0f} 0" keyTimes="0;.35;.68;1" dur="{T}s" repeatCount="indefinite" calcMode="spline" keySplines="0 0 1 1;.45 0 .7 1;0 0 1 1"/>
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;.35;.4;.68;.74;1" dur="{T}s" repeatCount="indefinite"/>
<rect x="128" y="{cy-15}" width="64" height="30" rx="15" fill="#8e8e93"/>
<circle cx="152" cy="{cy}" r="7" fill="none" stroke="#fff" stroke-width="2"/><circle cx="150" cy="{cy-2}" r="1.4" fill="#fff"/><circle cx="155" cy="{cy+2}" r="1.4" fill="#fff"/><path d="M166 {cy}h12" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/></g>''')
    # contact ripple where the cookie is refused
    rx = cx - 150 - 2
    b.append(f'''<circle cx="{rx}" cy="{cy}" r="10" fill="none" stroke="#8e8e93" stroke-width="2" opacity="0">
<animate attributeName="r" values="10;10;46;46" keyTimes="0;.68;.86;1" dur="{T}s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0;0;.9;0;0" keyTimes="0;.68;.7;.86;1" dur="{T}s" repeatCount="indefinite"/></circle>''')
    # shield
    sw, sh = 300, 340
    top = cy - sh / 2
    P = (f"M{cx} {top} C{cx+70} {top+28} {cx+sw/2} {top+30} {cx+sw/2} {top+30} "
         f"L{cx+sw/2} {top+150} C{cx+sw/2} {top+250} {cx+60} {top+310} {cx} {top+sh} "
         f"C{cx-60} {top+310} {cx-sw/2} {top+250} {cx-sw/2} {top+150} L{cx-sw/2} {top+30} C{cx-sw/2} {top+30} {cx-70} {top+28} {cx} {top} Z")
    b.append(f'''<clipPath id="shc"><path d="{P}"/></clipPath>
<g filter="url(#ps)"><path d="{P}" fill="url(#steel)"/></g>
<path d="{P}" fill="none" stroke="#ffffff" stroke-opacity=".55" stroke-width="2"/>
<path d="{P}" transform="translate({cx} {cy}) scale(.86) translate({-cx} {-cy})" fill="url(#steelIn)" stroke="#000" stroke-opacity=".12"/>
<g clip-path="url(#shc)"><rect x="{cx-sw}" y="{top-40}" width="90" height="{sh+80}" fill="#fff" fill-opacity=".38" transform="skewX(-20)">
<animateTransform attributeName="transform" type="translate" values="-120 0;1000 0;1000 0" keyTimes="0;.35;1" dur="{T}s" additive="sum" repeatCount="indefinite" calcMode="spline" keySplines=".5 0 .5 1;0 0 1 1"/></rect></g>
<circle cx="{cx}" cy="{cy-26}" r="24" fill="#1d1d1f"/><path d="M{cx-12} {cy-14} L{cx-18} {cy+44} H{cx+18} L{cx+12} {cy-14}Z" fill="#1d1d1f"/>
<circle cx="{cx}" cy="{cy-26}" r="7" fill="{BLUE_DARK}"><animate attributeName="opacity" values=".35;1;1;.35" keyTimes="0;.06;.6;1" dur="{T}s" repeatCount="indefinite"/></circle>''')
    for lx, lab in [(160, "Your browser"), (cx, "GatewayCore"), (W - 160, "Your app")]:
        b.append(t(lx, cy + sh / 2 + 52 if lx == cx else cy + 52, lab, 19, 400, MUTED_DARK))
    defs = '''<linearGradient id="steel" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f5f5f7"/><stop offset=".45" stop-color="#b8b8bd"/><stop offset=".7" stop-color="#8e8e93"/><stop offset="1" stop-color="#d1d1d6"/></linearGradient>
<linearGradient id="steelIn" x1="1" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e5e5ea"/><stop offset=".5" stop-color="#a1a1a6"/><stop offset="1" stop-color="#c7c7cc"/></linearGradient>'''
    return svg(H, TILE3, "\n".join(b), defs)


# ════════════════════════════ 004 Flood AI — parchment tile, isometric street model ════════════════════════════
def flood():
    H = 900
    T = 10
    b = [tile_head("Flood AI", "Sees the flood before the rain.",
                   "Street-level water depth, 72 hours out, from neural physics and live sensors.",
                   ["Tech specs"], False)]
    rain_at = len(b)
    s = 31
    ox, oy = W / 2 - 40, 410
    c30, s30 = math.cos(math.radians(30)), .5

    def P(x, y, z=0):
        return (ox + (x - y) * c30 * s, oy + (x + y) * s30 * s - z * s)

    def poly(pts):
        return " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)

    G = 11
    # slab
    b.append(f'<g filter="url(#ps)"><polygon points="{poly([P(0,0), P(G,0), P(G,G), P(0,G)])}" fill="#fff"/>'
             f'<polygon points="{poly([P(0,G), P(G,G), P(G,G,-.9), P(0,G,-.9)])}" fill="#e3e3e8"/>'
             f'<polygon points="{poly([P(G,0), P(G,G), P(G,G,-.9), P(G,0,-.9)])}" fill="#d2d2d7"/></g>')
    # road grid on the slab
    for k in (3.5, 7.5):
        b.append(f'<polygon points="{poly([P(k,0), P(k+1,0), P(k+1,G), P(k,G)])}" fill="#ececf0"/>')
        b.append(f'<polygon points="{poly([P(0,k), P(G,k), P(G,k+1), P(0,k+1)])}" fill="#ececf0"/>')
    levels = [0, .25, 1.1, 1.1, .35, 0]
    kt = "0;.2;.5;.68;.88;1"
    spl = ";".join([".45 0 .55 1"] * 5)

    def water_poly(L):
        return poly([P(0, 0, L), P(G, 0, L), P(G, G, L), P(0, G, L)])

    b.append(f'''<polygon fill="{BLUE}" fill-opacity=".22" stroke="{BLUE}" stroke-opacity=".35" points="{water_poly(0)}">
<animate attributeName="points" values="{';'.join(water_poly(L) for L in levels)}" keyTimes="{kt}" dur="{T}s" repeatCount="indefinite" calcMode="spline" keySplines="{spl}"/></polygon>''')
    # buildings, back to front
    blds = [(0.6, 0.6, 2.4, 2.3, 3.6), (4.8, 0.5, 2.2, 2.4, 2.2), (8.7, 0.6, 1.8, 2.4, 4.8),
            (0.6, 4.8, 2.4, 2.2, 1.8), (4.8, 4.8, 2.2, 2.2, 3.0), (8.7, 4.8, 1.8, 2.2, 2.4),
            (0.6, 8.7, 2.4, 1.8, 2.8), (4.8, 8.7, 2.2, 1.8, 1.6), (8.7, 8.7, 1.8, 1.8, 3.4)]
    blds.sort(key=lambda q: q[0] + q[1])
    for (x, y, w, d, h) in blds:
        top = [P(x, y, h), P(x+w, y, h), P(x+w, y+d, h), P(x, y+d, h)]
        left = [P(x, y+d, 0), P(x+w, y+d, 0), P(x+w, y+d, h), P(x, y+d, h)]
        right = [P(x+w, y, 0), P(x+w, y+d, 0), P(x+w, y+d, h), P(x+w, y, h)]
        b.append(f'<polygon points="{poly(left)}" fill="#ececf0"/><polygon points="{poly(right)}" fill="#d9d9de"/><polygon points="{poly(top)}" fill="#fff"/>')
        # water collar on the two visible faces
        def collar(L):
            return poly([P(x, y+d, 0), P(x+w, y+d, 0), P(x+w, y, 0), P(x+w, y, L), P(x+w, y+d, L), P(x, y+d, L)])
        b.append(f'''<polygon fill="{BLUE}" fill-opacity=".28" points="{collar(0)}"><animate attributeName="points" values="{';'.join(collar(min(L, h)) for L in levels)}" keyTimes="{kt}" dur="{T}s" repeatCount="indefinite" calcMode="spline" keySplines="{spl}"/></polygon>''')
    # sensor on the near corner of the crossroads
    sx, sy = P(7.5, 7.5, 0)
    tx, ty = P(7.5, 7.5, 2.6)
    b.append(f'''<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" stroke="{INK}" stroke-width="2.5"/>
<circle cx="{tx:.1f}" cy="{ty:.1f}" r="6" fill="{BLUE}"/>
{''.join(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="6" fill="none" stroke="{BLUE}" stroke-width="2"><animate attributeName="r" values="6;34" dur="2.4s" begin="{k*.8}s" repeatCount="indefinite"/><animate attributeName="opacity" values=".8;0" dur="2.4s" begin="{k*.8}s" repeatCount="indefinite"/></circle>' for k in range(3))}''')
    # forecast card (utility card: white, hairline, 18px radius)
    cx0, cy0, cw, ch = 846, 470, 290, 150
    b.append(f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" rx="26" fill="#fff" stroke="{HAIR}"/>')
    b.append(t(cx0 + 24, cy0 + 40, "Crossroads, sector 4", 17, 600, INK, "start"))
    b.append(t(cx0 + 24, cy0 + 64, "Forecast 72 h ahead", 14, 400, INK48, "start"))
    reads = [("0.05 m", ".0;.2"), ("0.31 m", ".2;.4"), ("0.74 m", ".4;.78"), ("0.22 m", ".78;1")]
    for v, win in reads:
        a, z = map(float, win.split(";"))
        vals = "0;1;0" if a > 0 else "1;0"
        ktt = f"0;{a};{z}" if a > 0 else f"0;{z}"
        b.append(f'<g opacity="{1 if a == 0 else 0}"><animate attributeName="opacity" values="{vals}" keyTimes="{ktt}" dur="{T}s" repeatCount="indefinite" calcMode="discrete"/>{t(cx0 + 24, cy0 + 118, v, 40, 600, INK, "start")}</g>')
    b.append(f'''<g opacity="0"><animate attributeName="opacity" values="0;1;0" keyTimes="0;.45;.78" dur="{T}s" repeatCount="indefinite" calcMode="discrete"/>
<rect x="{cx0+cw-100}" y="{cy0+90}" width="76" height="34" rx="17" fill="{BLUE}"/>{t(cx0+cw-62, cy0+113, "Alert", 15, 400, "#fff")}</g>''')
    rain_l = []
    # rain, kept faint so the model stays the subject
    for _ in range(36):
        x = random.uniform(260, 960)
        d = random.uniform(.8, 1.3)
        bg = -random.uniform(0, d)
        rain_l.append(f'<line x1="{x:.0f}" y1="0" x2="{x-5:.0f}" y2="18" stroke="{INK48}" stroke-opacity=".35" stroke-width="1.4"><animateTransform attributeName="transform" type="translate" values="0 300;-30 640" dur="{d:.2f}s" begin="{bg:.2f}s" repeatCount="indefinite"/></line>')
    b[rain_at:rain_at] = rain_l
    return svg(H, PARCH, "\n".join(b))


# ════════════════════════════ 005 RiderShield AI — dark tile, helmet with sensing field ════════════════════════════
def ridershield():
    H = 840
    T = 5
    b = [tile_head("RiderShield AI", "Reads the road. Reads the rider.",
                   "An edge AI helmet that maps potholes and catches fatigue. Patent filed.",
                   ["View the code", "See the demo", "Tech specs"], True)]
    cx, cy = 520, 560
    shell = (f"M{cx-190} {cy+70} C{cx-210} {cy-60} {cx-120} {cy-170} {cx+10} {cy-172} "
             f"C{cx+130} {cy-172} {cx+205} {cy-90} {cx+210} {cy+5} L{cx+212} {cy+60} "
             f"C{cx+160} {cy+86} {cx+80} {cy+96} {cx+40} {cy+96} L{cx-150} {cy+96} C{cx-176} {cy+96} {cx-188} {cy+86} {cx-190} {cy+70} Z")
    visor = (f"M{cx+30} {cy-82} C{cx+110} {cy-92} {cx+176} {cy-58} {cx+204} {cy+4} "
             f"L{cx+206} {cy+40} C{cx+150} {cy+44} {cx+80} {cy+40} {cx+30} {cy+30} Z")
    # sensing field ahead of the visor
    for k in range(4):
        b.append(f'''<path d="M{cx+230} {cy-70} A120 120 0 0 1 {cx+230} {cy+70}" fill="none" stroke="{BLUE_DARK}" stroke-width="2.5" stroke-linecap="round" opacity="0">
<animateTransform attributeName="transform" type="translate" values="0 0;240 0" dur="2.8s" begin="{k*.7}s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0;.85;0" keyTimes="0;.15;1" dur="2.8s" begin="{k*.7}s" repeatCount="indefinite"/></path>''')
    b.append(f'''<clipPath id="hc"><path d="{shell}"/></clipPath>
<g filter="url(#ps)"><path d="{shell}" fill="url(#gloss)"/></g>
<path d="{shell}" fill="none" stroke="#fff" stroke-opacity=".16" stroke-width="2"/>
<g clip-path="url(#hc)">
<path d="M{cx-170} {cy-40} C{cx-120} {cy-140} {cx-10} {cy-160} {cx+60} {cy-150}" stroke="#fff" stroke-opacity=".22" stroke-width="16" fill="none" stroke-linecap="round"/>
<rect x="{cx-420}" y="{cy-200}" width="80" height="420" fill="#fff" fill-opacity=".14" transform="skewX(-22)">
<animateTransform attributeName="transform" type="translate" values="0 0;1200 0;1200 0" keyTimes="0;.45;1" dur="{T}s" additive="sum" repeatCount="indefinite" calcMode="spline" keySplines=".5 0 .5 1;0 0 1 1"/></rect>
<path d="M{cx-190} {cy+52} H{cx+212}" stroke="#000" stroke-opacity=".35" stroke-width="10"/>
</g>
<path d="{visor}" fill="url(#visor)" stroke="#000" stroke-opacity=".4"/>
<path d="M{cx+60} {cy-62} C{cx+120} {cy-66} {cx+164} {cy-40} {cx+186} {cy-6}" stroke="#fff" stroke-opacity=".35" stroke-width="5" fill="none" stroke-linecap="round"/>
<rect x="{cx-120}" y="{cy-6}" width="46" height="10" rx="5" fill="#000" fill-opacity=".45"/>
<circle cx="{cx-97}" cy="{cy-1}" r="3.5" fill="{BLUE_DARK}">{anim("opacity", "1;.2;1", 1.2)}</circle>''')
    # road strip
    ry = 742
    b.append(f'<line x1="140" y1="{ry}" x2="{W-140}" y2="{ry}" stroke="#48484a" stroke-width="2"/>')
    b.append(f'<line x1="140" y1="{ry+18}" x2="{W-140}" y2="{ry+18}" stroke="#636366" stroke-width="3" stroke-dasharray="34 26"><animate attributeName="stroke-dashoffset" from="0" to="60" dur=".6s" repeatCount="indefinite"/></line>')
    b.append(f'''<g><animateTransform attributeName="transform" type="translate" values="{W-160} 0;140 0" dur="{T}s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.06;.94;1" dur="{T}s" repeatCount="indefinite"/>
<ellipse cx="0" cy="{ry+18}" rx="26" ry="7" fill="#000" stroke="#636366"/></g>''')
    # "mapped" label appears as the pothole passes under the sensing field (x≈870 → t≈.26)
    b.append(f'''<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;.2;.24;.5;.56;1" dur="{T}s" repeatCount="indefinite"/>
<rect x="{W-330}" y="{ry-84}" width="190" height="40" rx="20" fill="{TILE2}" stroke="#48484a"/>
<circle cx="{W-306}" cy="{ry-64}" r="5" fill="{BLUE_DARK}"/>{t(W-292, ry-58, "Pothole mapped", 16, 400, ON_DARK, "start")}</g>''')
    defs = '''<radialGradient id="gloss" cx=".38" cy=".25" r=".9"><stop offset="0" stop-color="#6e6e73"/><stop offset=".35" stop-color="#2c2c2e"/><stop offset="1" stop-color="#0b0b0c"/></radialGradient>
<linearGradient id="visor" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b2a4a"/><stop offset=".5" stop-color="#050d18"/><stop offset="1" stop-color="#1b3b5c"/></linearGradient>'''
    return svg(H, TILE1, "\n".join(b), defs)


# ════════════════════════════ 006 ProofStack — white tile, stacking verified passes ════════════════════════════
def proofstack():
    H = 860
    T = 10
    b = [tile_head("ProofStack", "Every resume, scored the same way.",
                   "Parses each resume and ranks candidates on one consistent rubric.",
                   ["View the code", "Tech specs"], False)]
    # candidate cards, ranked: highest score at the back, each new card lands in front
    cards = [("Candidate 01", "6 yrs, backend", 94, (96, 90, 95)),
             ("Candidate 02", "4 yrs, full-stack", 89, (91, 84, 92)),
             ("Candidate 03", "3 yrs, backend", 82, (85, 78, 83)),
             ("Candidate 04", "2 yrs, data", 77, (80, 70, 81))]
    cw, chh = 500, 136
    x = W / 2 - cw / 2
    top, peek = 400, 62
    for k, (name, meta, score, parts) in enumerate(cards):
        y = top + k * peek
        t0 = .06 + k * .13
        kt = f"0;{t0:.2f};{t0+.09:.2f};.9;.96;1"
        bars = []
        for j, (lab, v) in enumerate(zip(["Skills", "Experience", "Projects"], parts)):
            bx = x + 30 + j * 150
            full = 120 * v / 100
            bars.append(t(bx, y + 92, lab, 14, 400, INK48, "start")
                        + f'<rect x="{bx}" y="{y+104}" width="120" height="6" rx="3" fill="#e9e9eb"/>'
                        + f'<rect x="{bx}" y="{y+104}" height="6" rx="3" fill="{BLUE}" width="0"><animate attributeName="width" values="0;0;{full:.0f};{full:.0f};0" keyTimes="0;{t0+.08:.2f};{t0+.16:.2f};.9;1" dur="{T}s" repeatCount="indefinite" calcMode="spline" keySplines="0 0 1 1;.2 .8 .2 1;0 0 1 1;0 0 1 1"/></rect>')
        b.append(f'''<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt}" dur="{T}s" repeatCount="indefinite"/>
<animateTransform attributeName="transform" type="translate" values="0 110;0 110;0 0;0 0;0 0;0 110" keyTimes="{kt}" dur="{T}s" repeatCount="indefinite" calcMode="spline" keySplines="0 0 1 1;.2 .8 .2 1;0 0 1 1;0 0 1 1;0 0 1 1"/>
<g filter="url(#ps)"><rect x="{x}" y="{y}" width="{cw}" height="{chh}" rx="26" fill="#fff"/></g>
<rect x="{x}" y="{y}" width="{cw}" height="{chh}" rx="26" fill="none" stroke="{HAIR}"/>
{t(x + 30, y + 39, name, 21, 600, INK, "start")}
{t(x + 30 + measure(name, 21, 600) + 14, y + 39, meta, 17, 400, INK48, "start")}
{"".join(bars)}
<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{t0+.1:.2f};{t0+.13:.2f};.9;1" dur="{T}s" repeatCount="indefinite"/>
<circle cx="{x+cw-44}" cy="{y+32}" r="21" fill="{BLUE}"/>{t(x+cw-44, y+39, str(score), 18, 600, "#fff")}</g></g>''')
    # shortlist badge, once all four are ranked
    bw = measure("Shortlist ready", 18, 600) + 64
    sx, sy = W / 2 - bw / 2, top + 3 * peek + chh + 40
    b.append(f'''<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;.62;.66;.9;1" dur="{T}s" repeatCount="indefinite"/>
<g class="fx"><animateTransform attributeName="transform" type="scale" values=".7;.7;1;1" keyTimes="0;.62;.68;1" dur="{T}s" repeatCount="indefinite" calcMode="spline" keySplines="0 0 1 1;.2 .8 .2 1;0 0 1 1"/>
<rect x="{sx:.1f}" y="{sy}" width="{bw:.1f}" height="48" rx="24" fill="{BLUE}"/>
<path d="M{sx+24:.1f} {sy+24} l6 6 l11 -12" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
{t(sx + 44 + (bw - 44) / 2 - 6, sy + 31, "Shortlist ready", 18, 600, "#fff")}</g></g>''')
    return svg(H, CANVAS, "\n".join(b))


# ════════════════════════════ toolkit, activity, contact, footer ════════════════════════════
def toolkit():
    H = 640
    b = [t(W/2, 126, "The toolkit.", 56, 600, INK),
         t(W/2, 180, "What the six systems are built with.", 26, 400, INK80)]
    cols = [("Intelligence", ["LangGraph", "Claude and OpenAI APIs", "PyTorch Geometric", "Hugging Face", "YOLOv8 and LSTMs"]),
            ("Interface", ["Next.js and React", "Three.js", "Tailwind CSS", "Framer Motion", "Figma"]),
            ("Systems", ["FastAPI and Node.js", "Kafka", "PostgreSQL and Supabase", "AWS, ML Associate", "Kubernetes"]),
            ("Hardware", ["ESP32-S3", "Raspberry Pi Zero 2 W", "IMU and ultrasonic", "OpenCV", "Photogrammetry"])]
    cw, gap = 272, 16
    x0 = W / 2 - (4 * cw + 3 * gap) / 2
    for i, (head, items) in enumerate(cols):
        x = x0 + i * (cw + gap)
        b.append(f'<rect x="{x}" y="232" width="{cw}" height="340" rx="26" fill="#fff" stroke="{HAIR}"/>')
        b.append(t(x + 28, 286, head, 24, 600, INK, "start"))
        for k, it in enumerate(items):
            b.append(t(x + 28, 336 + k * 46, it, 18, 400, INK80, "start"))
    return svg(H, PARCH, "\n".join(b))


def activity():
    H = 250
    return svg(H, CANVAS, "\n".join([t(W/2, 126, "Something ships every week.", 56, 600, INK),
                                    t(W/2, 182, "Contribution activity, redrawn twice a day.", 26, 400, INK80)]))


def contact():
    H = 380
    return svg(H, TILE1, "\n".join([t(W/2, 170, "Let's build something.", 72, 600, ON_DARK),
                                   t(W/2, 236, "Open to SWE and AI internships, research collaborations,", 28, 400, MUTED_DARK),
                                   t(W/2, 276, "and hard problems with real-world stakes.", 28, 400, MUTED_DARK)]))


def pill(label, filled, bg=TILE1, w=400, h=150):
    pw = measure(label, 26) + 64
    x, y = (w - pw) / 2, (h - 64) / 2 - 18
    body = (f'<rect x="{x:.1f}" y="{y}" width="{pw:.1f}" height="64" rx="32" fill="{BLUE if filled else "none"}" '
            f'stroke="{BLUE_DARK if not filled else BLUE}" stroke-width="2"/>'
            + t(w / 2, y + 41, label, 26, 400, "#fff" if filled else BLUE_DARK))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">
<style>/*FONTS*/ text{{font-family:{FAMILY};font-feature-settings:"ss03"}}</style>
<rect width="{w}" height="{h}" fill="{bg}"/>{body}</svg>'''


def footer():
    H = 480
    b = []
    cols = [("Work", ["HotelOS", "HELIX", "KAAVAL", "Flood AI", "RiderShield AI", "ProofStack"]),
            ("Connect", ["rohithpranov.online", "LinkedIn", "GitHub", "rohithpranovv@gmail.com"]),
            ("About", ["B.Tech CSE, VIT Vellore", "IEEE Computer Society VIT", "ISGF Student Chapter VIT", "SDE intern, Contus Tech"])]
    xs = [120, 470, 820]
    for (head, items), x in zip(cols, xs):
        b.append(t(x, 78, head, 18, 600, INK, "start"))
        for k, it in enumerate(items):
            b.append(t(x, 122 + k * 38, it, 18, 400, INK80, "start"))
    b.append(f'<line x1="120" y1="{H-92}" x2="{W-120}" y2="{H-92}" stroke="#d2d2d7"/>')
    b.append(t(120, H - 52, "Copyright © 2026 V Rohith Pranov. Designed in Vellore.", 16, 400, INK48, "start"))
    b.append(t(W - 120, H - 52, "All systems nominal", 16, 400, INK48, "end"))
    return svg(H, PARCH, "\n".join(b))


FILES = {
    "hero.svg": hero, "glance.svg": glance,
    "01-hotelos.svg": hotelos, "02-helix.svg": helix, "03-kaaval.svg": kaaval,
    "04-flood.svg": flood, "05-ridershield.svg": ridershield, "06-proofstack.svg": proofstack,
    "toolkit.svg": toolkit, "activity.svg": activity, "contact.svg": contact, "footer.svg": footer,
    "pill-email.svg": lambda: pill("Email me", True),
    "pill-linkedin.svg": lambda: pill("LinkedIn", False),
    "pill-portfolio.svg": lambda: pill("Portfolio", False),
}

if __name__ == "__main__":
    rendered = {fn: f() for fn, f in FILES.items()}     # pass 1 collects every glyph used
    css = font_css()                                     # pass 2 subsets Inter to exactly those glyphs
    for fn, s in rendered.items():
        with open(os.path.join(OUT, fn), "w", encoding="utf-8") as fh:
            fh.write(s.replace("/*FONTS*/", css))
    print(f"wrote {len(rendered)} tiles · {len(_used_chars)} glyphs embedded")
