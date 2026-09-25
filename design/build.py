"""Generate the SVG panels used by the profile README.

The look follows lathif.dev: cream paper, poster type (Archivo Black),
hand-written accents (Caveat), and a yellow / red / blue palette.

Every SVG embeds only the glyphs it uses, so it renders the same on
github.com as it does locally, with no external requests.

    pip install fonttools brotli
    python design/build.py
"""

import base64
import io
import re
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "assets"

# ── palette (lifted from lathif.dev) ─────────────────────────────────
Y = "#FFD62E"   # sunflower
R = "#F5533B"   # tomato
B = "#4E8FE6"   # blue
BL = "#7CAEF5"  # band blue
BP = "#9CC4F5"  # pale blue
CREAM = "#FBF7EC"
INK = "#111111"
GREY = "#6A6A6A"
LINE = "#DFD9CB"
NIGHT = "#15161C"

FONTS = {
    "d": ("Display", "ArchivoBlack.woff2", "400"),
    "h": ("Hand", "Caveat.woff2", "700"),
    "s": ("Sans", "Inter.woff2", "100 900"),
    "m": ("Mono", "JetBrainsMono.woff2", "500"),
}
_tt = {k: TTFont(ROOT / "fonts" / f) for k, (_, f, _) in FONTS.items()}


def width(font, text, size, weight=1.0):
    """Advance width of `text` in px (good enough for layout)."""
    t = _tt[font]
    cmap, hmtx = t.getBestCmap(), t["hmtx"]
    upm = t["head"].unitsPerEm
    w = sum(hmtx[cmap.get(ord(c), cmap[32])][0] for c in text)
    return w * size / upm * weight


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def font_css(svg_body):
    """@font-face rules for the fonts used in svg_body, subset to its text."""
    rules = []
    for key, (family, file, weight) in FONTS.items():
        chunks = re.findall(
            rf'<text[^>]*class="[^"]*\b{key}\b[^"]*"[^>]*>(.*?)</text>', svg_body, re.S
        )
        if not chunks:
            continue
        text = re.sub(r"<[^>]+>", "", "".join(chunks))
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        chars = set(text) | {" "}
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "liga"]
        font = TTFont(ROOT / "fonts" / file)
        sub = subset.Subsetter(opts)
        sub.populate(text="".join(sorted(chars)))
        sub.subset(font)
        buf = io.BytesIO()
        font.flavor = "woff2"
        font.save(buf)
        data = base64.b64encode(buf.getvalue()).decode()
        rules.append(
            f"@font-face{{font-family:'{family}';font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{data}) format('woff2')}}"
            f".{key}{{font-family:'{family}',sans-serif}}"
        )
    return "".join(rules)


BASE_CSS = """
.spin{transform-box:fill-box;transform-origin:center;animation:spin 14s linear infinite}
.wob{transform-box:fill-box;transform-origin:center;animation:wob 4s ease-in-out infinite}
.bob{animation:bob 5s ease-in-out infinite}
.pulse{transform-box:fill-box;transform-origin:center;animation:pulse 1.6s ease-in-out infinite}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes wob{0%,100%{transform:rotate(-6deg)}50%{transform:rotate(6deg)}}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.15)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def svg(w, h, body, title, extra_css="", clip_radius=28):
    css = font_css(body) + BASE_CSS + extra_css
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">'
        f"<title>{esc(title)}</title>"
        f"<style>{css}</style>"
        f'<defs><clipPath id="card"><rect width="{w}" height="{h}" rx="{clip_radius}"/></clipPath></defs>'
        f'<g clip-path="url(#card)">{body}</g></svg>'
    )


# ── little drawing helpers ───────────────────────────────────────────

def asterisk(cx, cy, r, color, sw=None, cls="spin"):
    sw = sw or r * 0.36
    lines = "".join(
        f'<line x1="0" y1="{-r}" x2="0" y2="{r}" transform="rotate({a})"/>'
        for a in (0, 45, 90, 135)
    )
    return (
        f'<g transform="translate({cx} {cy})"><g class="{cls}" stroke="{color}" '
        f'stroke-width="{sw:.1f}" stroke-linecap="round">{lines}</g></g>'
    )


def dots(x, y, cols, rows, gap, color, r=1.6):
    return "".join(
        f'<circle cx="{x + c * gap}" cy="{y + r_ * gap}" r="{r}" fill="{color}"/>'
        for r_ in range(rows)
        for c in range(cols)
    )


def text(x, y, s, cls, size, fill=INK, anchor="start", extra=""):
    return (
        f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}" fill="{fill}" '
        f'text-anchor="{anchor}" {extra}>{esc(s)}</text>'
    )


def arrow_btn(cx, cy, r=13, color=INK):
    return (
        f'<g transform="translate({cx} {cy})" fill="none" stroke="{color}" stroke-width="1.8" '
        f'stroke-linecap="round" stroke-linejoin="round"><circle r="{r}"/>'
        f'<path d="M-5 0H5M1-4l4 4-4 4"/></g>'
    )


def heart(cx, cy, s, color):
    return (
        f'<g transform="translate({cx} {cy}) scale({s})"><path class="pulse" fill="{color}" '
        f'd="M0 7C-6-1-12-3-12-8a6 6 0 0 1 12-2 6 6 0 0 1 12 2c0 5-6 7-12 15z" '
        f'transform="translate(0 -4)"/></g>'
    )


# ── 1. hero ──────────────────────────────────────────────────────────

def hero():
    W, H = 900, 560
    photo = base64.b64encode((ROOT / "lathif.webp").read_bytes()).decode()
    pill = "BUILDING AI PRODUCTS THAT SHIP"
    pw = width("s", pill, 12, 1.08) + 44
    tag1 = "I build AI-powered products that solve"
    tag2 = "real problems & create impact."
    body = f"""
<rect width="{W}" height="{H}" fill="{CREAM}"/>
{asterisk(52, 56, 11, R, 4.4)}
{text(74, 53, "SOFTWARE ENGINEER", "d", 14)}
{text(74, 71, "&amp; AI MAKER".replace("&amp;", "&"), "d", 14)}
<rect x="{(W - pw) / 2 - 20:.1f}" y="40" width="{pw:.1f}" height="34" rx="17" fill="none" stroke="{INK}" stroke-width="1.6"/>
{text((W - 40) / 2, 62, pill, "s", 12, extra='font-weight="700" letter-spacing=".04em"', anchor="middle")}

<circle cx="700" cy="355" r="205" fill="{Y}"/>
{dots(810, 210, 7, 6, 12, INK, 1.7)}
{dots(372, 104, 7, 5, 12, R, 1.5)}
<image x="470" y="{H - 397}" width="440" height="397" xlink:href="data:image/webp;base64,{photo}"/>

<g transform="translate(824 78)"><g class="wob">
  <circle r="40" fill="{Y}"/>
  {text(0, -9, "CODE", "d", 11, anchor="middle")}
  <path d="M-7 1q7 7 14 0" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>
  <circle cx="-4" cy="-3" r="1.6" fill="{INK}"/><circle cx="4" cy="-3" r="1.6" fill="{INK}"/>
  {text(0, 21, "with purpose", "h", 14, anchor="middle")}
</g></g>

{text(44, 186, "HELLO!", "h", 112, R, extra='transform="rotate(-4 44 186)"')}
{text(40, 280, "I'M", "d", 94)}
{text(40, 372, "LATHIF", "d", 104)}
{asterisk(430, 258, 26, B, 8)}

<g transform="rotate(-1.5 40 400)">
  <rect x="40" y="398" width="{max(width('h', tag1, 27), width('h', tag2, 27)) + 30:.0f}" height="78" fill="{Y}"/>
  {text(54, 430, tag1, "h", 27)}
  {text(54, 463, tag2, "h", 27)}
</g>
<path d="M44 492q60-8 120-3t120-2" fill="none" stroke="{R}" stroke-width="3" stroke-linecap="round"/>

<g transform="translate(52 522)" fill="none" stroke="{INK}" stroke-width="1.6">
  <circle r="9"/><ellipse rx="4" ry="9"/><path d="M-9 0h18"/>
</g>
{text(72, 518, "BASED IN SYDNEY, AUSTRALIA", "s", 12.5, extra='font-weight="700"')}
{text(72, 535, "WORKING WORLDWIDE", "s", 12.5, extra='font-weight="700"')}

<g class="bob"><g transform="translate(440 420) rotate(5)">
  <rect x="3" y="5" width="122" height="96" rx="8" fill="{INK}" opacity=".18"/>
  <rect width="122" height="96" rx="8" fill="{B}" stroke="#fff" stroke-width="4"/>
  {text(18, 30, "CODE.", "d", 18, "#fff")}
  {text(18, 54, "BUILD.", "d", 18, "#fff")}
  {text(18, 78, "IMPACT.", "d", 18, "#fff")}
  <path d="M110-12l-10 18h8l-6 14 14-20h-8l6-12z" fill="#fff" stroke="{B}" stroke-width="1.5" stroke-linejoin="round"/>
</g></g>
"""
    return svg(W, H, body, "Hello! I'm Lathif — AI Engineer & Maker, based in Sydney, working worldwide.")


# ── 2. what I do ─────────────────────────────────────────────────────

ICONS = {
    # robot
    "robot": '<rect x="-9" y="-5" width="18" height="13" rx="3"/><path d="M0-5v-4"/><circle cx="0" cy="-10" r="1.5"/>'
             '<circle cx="-4" cy="1" r="1.2" fill="currentColor"/><circle cx="4" cy="1" r="1.2" fill="currentColor"/><path d="M-12 0v3M12 0v3"/>',
    # graph of agents
    "nodes": '<circle cx="0" cy="-8" r="3"/><circle cx="-8" cy="6" r="3"/><circle cx="8" cy="6" r="3"/>'
             '<path d="M-1.5-5.5-6.5 3.5M1.5-5.5 6.5 3.5M-5 6h10"/>',
    # spark / LLM
    "spark": '<path d="M0-11 2.8-2.8 11 0 2.8 2.8 0 11-2.8 2.8-11 0-2.8-2.8z"/>',
    # monitor
    "monitor": '<rect x="-10" y="-8" width="20" height="13" rx="2"/><path d="M-4 10h8M0 5v5"/>',
}


def what():
    W, H = 900, 300
    cols = [
        ("robot", Y, "AI", "SYSTEMS", ["Agentic tools with", "memory and context."]),
        ("nodes", BP, "MULTI-AGENT", "ORCHESTRATION", ["State, handoffs and typed", "contracts between agents."]),
        ("spark", R, "PRODUCTION", "LLMs", ["Evals, RAG, latency and", "token efficiency."]),
        ("monitor", Y, "FULL-STACK", "PRODUCT", ["React, FastAPI, Postgres,", "AWS. Schema to deploy."]),
    ]
    x0, cw = 196, 172
    parts = []
    for i, (icon, bg, t1, t2, desc) in enumerate(cols):
        x = x0 + i * cw
        if i:
            parts.append(f'<line x1="{x - 14}" y1="70" x2="{x - 14}" y2="222" stroke="{LINE}" stroke-width="1.2"/>')
        ic = "#fff" if bg == R else INK
        parts.append(
            f'<circle cx="{x + 26}" cy="96" r="26" fill="{bg}"/>'
            f'<g transform="translate({x + 26} 96)" fill="none" stroke="{ic}" color="{ic}" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{ICONS[icon]}</g>'
            + text(x, 150, t1, "d", 12.5)
            + text(x, 167, t2, "d", 12.5)
            + text(x, 194, desc[0], "s", 11.5, GREY)
            + text(x, 211, desc[1], "s", 11.5, GREY)
        )
    body = f"""
<rect width="{W}" height="{H}" fill="{CREAM}"/>
{text(40, 92, "WHAT", "d", 32)}
{text(40, 130, "I DO", "d", 32)}
<path d="M40 146q20-3 44 0" fill="none" stroke="{B}" stroke-width="2" stroke-linecap="round"/>
<g transform="translate(100 218)">
  <circle r="54" fill="{R}"/>
  {text(0, -20, "GOOD DESIGN", "s", 9.5, "#fff", "middle", 'font-weight="800" letter-spacing=".06em"')}
  {heart(0, 3, 1.05, "#fff")}
  {text(0, 32, "GOOD IMPACT", "s", 9.5, "#fff", "middle", 'font-weight="800" letter-spacing=".06em"')}
</g>
{''.join(parts)}
<path d="M806 58q12-26 24-6t24-10l12-14" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>
<path d="M858 26l10 1-2 10" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
{asterisk(846, 262, 17, B, 5)}
"""
    return svg(W, H, body, "What I do: AI systems, multi-agent orchestration, production LLMs, full-stack product.")


# ── 3. featured projects ─────────────────────────────────────────────

def chrome(x, y, dark=True):
    return (
        f'<circle cx="{x + 14}" cy="{y + 14}" r="3" fill="{R}"/>'
        f'<circle cx="{x + 24}" cy="{y + 14}" r="3" fill="{Y}"/>'
        f'<circle cx="{x + 34}" cy="{y + 14}" r="3" fill="{B}"/>'
    )


def card_visual(kind, x, y, w, h):
    cx, cy = x + w / 2, y + h / 2
    if kind == "relay":
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{NIGHT}"/>{chrome(x, y)}'
            + text(x + 16, y + 48, "app.use(", "m", 12, "#E6E6E6")
            + text(x + 16 + width("m", "app.use(", 12), y + 48, "relay()", "m", 12, Y)
            + text(x + 16 + width("m", "app.use(relay()", 12), y + 48, ")", "m", 12, "#E6E6E6")
            + text(x + 16, y + 68, "// agents see a typed API", "m", 10.5, "#8A8A8A")
            + f'<rect x="{x + 16}" y="{y + 86}" width="118" height="30" rx="15" fill="{Y}"/>'
            + text(x + 75, y + 106, "20–100x fewer tokens", "s", 10.5, INK, "middle", 'font-weight="800"')
            + f'<rect x="{x + 142}" y="{y + 86}" width="80" height="30" rx="15" fill="none" stroke="{BP}" stroke-width="1.4"/>'
            + text(x + 182, y + 106, "1–20 ms", "s", 10.5, BP, "middle", 'font-weight="800"')
        )
    if kind == "hurricane":
        rows = [
            [("const ", R), ("agent", BP), (" = ", "#E6E6E6"), ("run", Y), ("()", "#E6E6E6")],
            [("// 7 agents: plan → code → test", "#8A8A8A")],
            [("await ", R), ("patch", BP), (".", "#E6E6E6"), ("apply", Y), ("()", "#E6E6E6")],
        ]
        out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{NIGHT}"/>{chrome(x, y)}'
        for i, row in enumerate(rows):
            xx = x + 16
            for s, col in row:
                s = s.replace("→", "->")
                out += text(xx, y + 48 + i * 20, s, "m", 11, col)
                xx += width("m", s, 11)
        for i, col in enumerate([R, Y, B, BP, R, Y, B]):
            out += f'<circle cx="{x + 22 + i * 16}" cy="{y + 122}" r="5" fill="{col}"/>'
        return out
    if kind == "zen":
        pts = " ".join(f"{x + 60 + i * 24},{y + 104 - v}" for i, v in enumerate([0, 14, 6, 26, 18, 38, 30, 52]))
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{NIGHT}"/>'
            f'<rect x="{x + 14}" y="{y + 12}" width="70" height="8" rx="4" fill="#2C2E38"/>'
            f'<circle cx="{x + w - 22}" cy="{y + 22}" r="11" fill="{B}" opacity=".7"/>'
            + text(cx, y + 58, "WORKZEN", "d", 16, "#fff", "middle")
            + f'<polyline points="{pts}" fill="none" stroke="#C9CCD6" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
            + f'<circle cx="{x + 228}" cy="{y + 52}" r="4" fill="{Y}"/>'
        )
    if kind == "aether":
        nodes = [(-70, -22), (-20, 30), (30, -28), (78, 18), (0, -4)]
        edges = [(0, 4), (1, 4), (2, 4), (3, 4), (0, 1), (2, 3), (1, 3)]
        out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{B}"/>'
        for a, b in edges:
            out += (f'<line x1="{cx + nodes[a][0]}" y1="{cy + nodes[a][1]}" x2="{cx + nodes[b][0]}" '
                    f'y2="{cy + nodes[b][1]}" stroke="#fff" stroke-width="1.4" stroke-dasharray="3 4" opacity=".75"/>')
        for i, (dx, dy) in enumerate(nodes):
            out += (f'<rect x="{cx + dx - 9}" y="{cy + dy - 15}" width="18" height="30" rx="4" '
                    f'fill="{NIGHT if i == 4 else "#fff"}" stroke="#fff" stroke-width="1.5"/>')
        return out + text(x + w - 14, y + h - 12, "no internet · no SIM", "s", 9.5, "#fff", "end", 'font-weight="700"')
    if kind == "oribo":
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#1B1B1F"/>{chrome(x, y)}'
            + text(cx, y + 70, "ORIBO", "d", 18, "#fff", "middle")
            + f'<rect x="{cx - 76}" y="{y + 90}" width="44" height="24" rx="3" fill="#3A3A40"/>'
            f'<rect x="{cx - 24}" y="{y + 90}" width="44" height="24" rx="3" fill="#3A3A40"/>'
            f'<rect x="{cx + 28}" y="{y + 90}" width="44" height="24" rx="3" fill="{R}" opacity=".85"/>'
        )
    if kind == "allalong":
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{BL}"/>'
            f'<rect x="{cx - 34}" y="{y + 12}" width="68" height="{h}" rx="12" fill="#fff" fill-opacity=".25" stroke="#fff" stroke-opacity=".7" stroke-width="1.5"/>'
            f'<rect x="{cx - 22}" y="{y + 30}" width="44" height="8" rx="4" fill="#fff" opacity=".8"/>'
            f'<rect x="{cx - 22}" y="{y + 46}" width="44" height="30" rx="4" fill="#fff" opacity=".55"/>'
            f'<rect x="{cx - 22}" y="{y + 84}" width="30" height="8" rx="4" fill="#fff" opacity=".8"/>'
            + text(cx, y + h - 14, "ALL-ALONG.COM", "d", 11, "#fff", "middle")
        )
    raise ValueError(kind)


def projects():
    W, H = 900, 640
    items = [
        ("relay", "RELAY", "AI agent middleware · Node.js"),
        ("hurricane", "HURRICANE", "Multi-agent coding assistant"),
        ("zen", "WORKZENPRO", "AI hiring · LLM evaluation"),
        ("aether", "AETHER", "iOS offline mesh network"),
        ("oribo", "ORIBO", "Global founder community"),
        ("allalong", "ALL-ALONG.COM", "Event platform MVP"),
    ]
    cw, vh, fh, gap = 256, 140, 62, 20
    x0 = (W - 3 * cw - 2 * gap) / 2
    cards = []
    for i, (kind, name, sub) in enumerate(items):
        x = x0 + (i % 3) * (cw + gap)
        y = 150 + (i // 3) * (vh + fh + gap)
        cid = f"c{i}"
        cards.append(
            f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{cw}" height="{vh + fh}" rx="12"/></clipPath>'
            f'<rect x="{x}" y="{y + 5}" width="{cw}" height="{vh + fh}" rx="12" fill="{INK}" opacity=".12"/>'
            f'<g clip-path="url(#{cid})">{card_visual(kind, x, y, cw, vh)}'
            f'<rect x="{x}" y="{y + vh}" width="{cw}" height="{fh}" fill="#fff"/></g>'
            + text(x + 16, y + vh + 27, name, "d", 13)
            + text(x + 16, y + vh + 46, sub, "s", 11.5, GREY)
            + arrow_btn(x + cw - 28, y + vh + fh / 2)
        )
    tw0 = width("d", "FEATURED PROJECTS", 38)
    tx0 = (W - tw0 - 60) / 2 - 30
    body = f"""
<rect width="{W}" height="{H}" fill="{BL}"/>
{text(tx0, 96, "FEATURED PROJECTS", "d", 38)}
<path d="M{tx0 + tw0 + 26} 72l-12 12 12 12M{tx0 + tw0 + 44} 72l-12 12 12 12" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<g transform="translate(730 50) rotate(-5)">
  <rect width="118" height="62" rx="6" fill="{INK}"/>
  {text(14, 26, "A few things", "h", 20, "#fff")}
  {text(14, 50, "I'm proud of", "h", 20, "#fff")}
</g>
<path d="M852 78q20 10 10 34" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>
<path d="M855 104l7 9 6-10" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
{asterisk(58, 62, 16, "#fff", 5)}
{''.join(cards)}
"""
    return svg(W, H, body, "Featured projects: Relay, Hurricane, WorkZenPro, Aether, Oribo, All-along.com.")


# ── 4. toolkit + currently ───────────────────────────────────────────

def toolkit():
    W, H = 900, 330
    rows = [
        ["Python", "TypeScript", "LangChain", "FastAPI"],
        ["OpenAI", "Node.js", "React", "Next.js"],
        ["PostgreSQL", "AWS", "Docker", "Swift"],
        ["HuggingFace", "RAG", "Evals", "Agents"],
    ]
    fills = [(Y, INK), (CREAM, INK), (BP, INK), (CREAM, INK), (R, "#fff"), (CREAM, INK)]
    chips, k = [], 0
    for r, row in enumerate(rows):
        x = 40
        y = 128 + r * 44
        for name in row:
            bg, fg = fills[k % len(fills)]
            k += 1
            w = width("s", name, 13, 1.07) + 30
            chips.append(
                f'<rect x="{x + 2}" y="{y + 3}" width="{w:.1f}" height="32" rx="16" fill="{INK}"/>'
                f'<rect x="{x}" y="{y}" width="{w:.1f}" height="32" rx="16" fill="{bg}" stroke="{INK}" stroke-width="1.6"/>'
                + text(x + w / 2, y + 21, name, "s", 13, fg, "middle", 'font-weight="700"')
            )
            x += w + 10

    tx, ty, tw, th = 468, 40, 392, 250
    lines = [
        ("$ ", Y, "git status", "#fff"),
        ("> ", R, "Building Relay: agent middleware", "#E6E6E6"),
        ("  ", R, "(YC application in progress)", "#8A8A8A"),
        ("> ", R, "Shipping Oribo for founders", "#E6E6E6"),
        ("> ", R, "Writing AIToday, weekly AI", "#E6E6E6"),
        ("  ", R, "economy newsletter", "#8A8A8A"),
        ("> ", R, "Open to AI Engineer roles", "#E6E6E6"),
        ("  ", R, "in AU + SF", "#8A8A8A"),
    ]
    term = []
    for i, (p, pc, s, sc) in enumerate(lines):
        y = ty + 64 + i * 22
        term.append(
            f'<g class="ln" style="animation-delay:{0.3 + i * 0.35:.2f}s">'
            + text(tx + 20, y, p.strip() or " ", "m", 12.5, pc)
            + text(tx + 38, y, s, "m", 12.5, sc)
            + "</g>"
        )
    cursor_y = ty + 64 + len(lines) * 22
    css = (
        ".ln{animation:in .4s ease backwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-6px)}to{opacity:1;transform:none}}"
        ".cur{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
    )
    body = f"""
<rect width="{W}" height="{H}" fill="{CREAM}"/>
{text(40, 78, "TOOLKIT", "d", 32)}
{text(208, 78, "what I build with", "h", 24, R, extra='transform="rotate(-3 208 78)"')}
<path d="M40 94q30-4 60 0" fill="none" stroke="{B}" stroke-width="2" stroke-linecap="round"/>
{''.join(chips)}

<rect x="{tx + 4}" y="{ty + 6}" width="{tw}" height="{th}" rx="14" fill="{INK}" opacity=".15"/>
<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="14" fill="{NIGHT}"/>
{chrome(tx + 4, ty + 6)}
{text(tx + tw / 2, ty + 25, "~/lathif — currently", "m", 11, "#8A8A8A", "middle")}
{''.join(term)}
<rect class="cur" x="{tx + 20}" y="{cursor_y - 12}" width="8" height="15" fill="{Y}"/>
<g transform="translate({tx + tw - 24} {ty + th - 6})"><g class="wob">
  <circle r="30" fill="{Y}"/>
  {text(0, -2, "NOW", "d", 12, INK, "middle")}
  {text(0, 14, "shipping", "h", 14, INK, "middle")}
</g></g>
"""
    return svg(W, H, body, "Toolkit: Python, TypeScript, LangChain, FastAPI, OpenAI, Node.js, React, AWS and more. Currently building Relay.", css)


# ── 5. contact ───────────────────────────────────────────────────────

CONTACT_ICONS = {
    "mail": '<rect x="-7" y="-5" width="14" height="10" rx="1.5"/><path d="M-7-4l7 5 7-5"/>',
    "globe": '<circle r="7"/><ellipse rx="3" ry="7"/><path d="M-7 0h14"/>',
    "in": '<rect x="-7" y="-7" width="14" height="14" rx="3"/><path d="M-3.5-1v4.5M-3.5-3.8v.1M0 3.5V-1M0 1c0-2 3.5-2.4 3.5 0v2.5"/>',
    "ig": '<rect x="-7" y="-7" width="14" height="14" rx="4"/><circle r="3.2"/><circle cx="4" cy="-4" r=".6" fill="#fff"/>',
    "pin": '<path d="M0 8S-6 2-6-2a6 6 0 0 1 12 0C6 2 0 8 0 8z"/><circle cy="-2" r="2"/>',
}


def contact():
    W, H = 900, 330
    items = [
        ("mail", "hello@lathif.dev"),
        ("globe", "lathif.dev"),
        ("in", "in/abdullathifshaik"),
        ("ig", "@lathifdev"),
        ("pin", "Sydney, Australia"),
    ]
    rows = "".join(
        f'<g transform="translate(632 {128 + i * 27})" fill="none" stroke="#fff" stroke-width="1.5" '
        f'stroke-linecap="round" stroke-linejoin="round">{CONTACT_ICONS[ic]}</g>'
        + text(650, 132 + i * 27, s, "s", 12.5, "#fff", extra='font-weight="600"')
        for i, (ic, s) in enumerate(items)
    )
    cta = "LET'S WORK TOGETHER!"
    cw = width("s", cta, 12, 1.1) + 60
    body = f"""
<rect width="{W}" height="{H}" fill="{CREAM}"/>
<rect width="330" height="260" fill="{Y}"/>
<rect x="600" width="300" height="260" fill="{R}"/>
{text(34, 100, "LET'S CREATE", "d", 30)}
{text(32, 146, "SOMETHING GREAT!", "h", 36, R, extra='transform="rotate(-3 32 146)"')}
<path d="M34 168q70-10 130-3t110-4" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>
{asterisk(290, 222, 12, "#fff", 4)}

{text(360, 96, "Have a project in mind?", "s", 15, INK, extra='font-weight="700"')}
{text(360, 120, "Let's bring your ideas", "s", 15, INK, extra='font-weight="700"')}
{text(360, 144, "to life. Or talk agents,", "s", 15, INK, extra='font-weight="700"')}
{text(360, 168, "evals and shipping.", "s", 15, INK, extra='font-weight="700"')}
<path d="M372 196q40 0 44 40" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>
<path d="M408 228l8 10 6-11" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>

<rect x="626" y="62" width="110" height="28" rx="14" fill="{Y}"/>
{text(681, 81, "CONTACT ME", "s", 11, INK, "middle", 'font-weight="800" letter-spacing=".04em"')}
{rows}

<rect y="260" width="{W}" height="70" fill="{BL}"/>
{text(34, 290, "PASSIONATE ABOUT TECH.", "s", 11.5, "#fff", extra='font-weight="800"')}
{text(34, 307, "FOCUSED ON IMPACT.", "s", 11.5, "#fff", extra='font-weight="800"')}
<path d="M34 314h116" stroke="{Y}" stroke-width="2"/>
<line x1="222" y1="276" x2="222" y2="314" stroke="#fff" stroke-opacity=".5"/>
{asterisk(250, 296, 8, "#fff", 2.6)}
{text(274, 290, "AVAILABLE FOR", "s", 11.5, "#fff", extra='font-weight="800"')}
{text(274, 307, "AI ENGINEER ROLES &amp; BUILDS".replace("&amp;", "&"), "s", 11.5, "#fff", extra='font-weight="800"')}

<rect x="{W - 34 - cw:.1f}" y="276" width="{cw:.1f}" height="38" rx="19" fill="#fff"/>
{asterisk(W - 34 - cw + 26, 295, 9, Y, 3)}
{text(W - 34 - cw + 44, 300, cta, "s", 12, INK, extra='font-weight="800"')}
<g class="bob"><g transform="translate({W - 34 - cw - 132} 240) rotate(-5)">
  <rect width="104" height="62" rx="8" fill="#fff"/>
  {text(12, 28, "THANK", "h", 28, INK)}
  {text(12, 54, "YOU!", "h", 28, INK)}
  {heart(84, 40, .75, BP)}
</g></g>
"""
    return svg(W, H, body, "Let's create something great. Email hello@lathif.dev, visit lathif.dev, or find me on LinkedIn.")


# ── 6. buttons ───────────────────────────────────────────────────────

def button(label, icon, bg, fg):
    w = width("s", label, 13, 1.1) + 64
    h = 46
    body = (
        f'<rect x="4" y="5" width="{w - 6:.1f}" height="{h - 8}" rx="19" fill="{INK}"/>'
        f'<rect x="1" y="1" width="{w - 6:.1f}" height="{h - 8}" rx="19" fill="{bg}" stroke="{INK}" stroke-width="2"/>'
        f'<g transform="translate(24 20)" fill="none" stroke="{fg}" stroke-width="1.6" '
        f'stroke-linecap="round" stroke-linejoin="round">{CONTACT_ICONS[icon].replace("#fff", fg)}</g>'
        + text(40, 25, label, "s", 13, fg, extra='font-weight="800" letter-spacing=".03em"')
    )
    return svg(round(w), h, body, label, clip_radius=0)


def main():
    OUT.mkdir(exist_ok=True)
    files = {
        "hero.svg": hero(),
        "what-i-do.svg": what(),
        "projects.svg": projects(),
        "toolkit.svg": toolkit(),
        "contact.svg": contact(),
        "btn-email.svg": button("EMAIL ME", "mail", Y, INK),
        "btn-site.svg": button("LATHIF.DEV", "globe", CREAM, INK),
        "btn-linkedin.svg": button("LINKEDIN", "in", B, "#fff"),
        "btn-instagram.svg": button("INSTAGRAM", "ig", R, "#fff"),
    }
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print(f"{name:22} {len(content) / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
