"""Moteur de rendu des vidéos FEG (format vertical 720x1280).
Usage : python3 engine/render.py <dossier_video> <tag> <align.json> [preview]
"""
import math, subprocess, sys, json, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storylib
from brand import *

ROOT = storylib.ROOT
VDIR = os.path.abspath(sys.argv[1]); TAG = sys.argv[2]; ALIGN = json.load(open(sys.argv[3]))
PREVIEW = len(sys.argv) > 4 and sys.argv[4] == "preview"
BUILD = os.path.join(VDIR, "build"); os.makedirs(BUILD, exist_ok=True)
FONTS = os.path.join(ROOT, "brand", "fonts")
W, H, FPS = 720, 1280, 25
_story_mod = storylib.load(VDIR)
story = _story_mod.story
PHOTOS = _story_mod.PHOTOS

# ---------- fonts ----------
_fc = {}
def font(kind, size):
    key = (kind, size)
    if key in _fc: return _fc[key]
    if kind == "script": f = ImageFont.truetype(f"{FONTS}/KaushanScript-Regular.ttf", size)
    elif kind == "anton": f = ImageFont.truetype(f"{FONTS}/Anton-Regular.ttf", size)
    else:
        f = ImageFont.truetype(f"{FONTS}/Montserrat-Variable.ttf", size)
        f.set_variation_by_name({"xb": "ExtraBold", "b": "Bold", "sb": "SemiBold", "m": "Medium"}[kind])
    _fc[key] = f
    return f

# ---------- photos (pre-upscaled) ----------
photos = {}
for i, fn in PHOTOS.items():
    im = Image.open(os.path.join(VDIR, "photos", fn)).convert("RGB")
    sc = 1500 / im.height
    im = im.resize((round(im.width * sc), 1500), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    arr = np.asarray(im).astype(np.float32)
    arr = (arr - 128) * 1.12 + 118
    arr *= np.array([1.0, 1.0, 0.97])
    lum = arr.mean(axis=2, keepdims=True); arr = lum + (arr - lum) * 0.95
    photos[i] = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def ease(x): return 0.5 - 0.5 * math.cos(math.pi * max(0, min(1, x)))
def ease_out(x):
    x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def back_out(x):
    x = max(0, min(1, x)); c = 1.7; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

def photo_frame(pid, p, cx0, cx1, z0, z1, cy=0.5):
    im = photos[pid]
    z = z0 + (z1 - z0) * ease(p)
    ch = im.height / z
    cw = ch * W / H
    if cw > im.width:
        cw = im.width; ch = cw * H / W
    cx = (cx0 + (cx1 - cx0) * ease(p)) * im.width
    cx = max(cw / 2, min(im.width - cw / 2, cx))
    cyy = max(ch / 2, min(im.height - ch / 2, cy * im.height))
    box = (cx - cw / 2, cyy - ch / 2, cx + cw / 2, cyy + ch / 2)
    fr = im.resize((W, H), Image.BICUBIC, box=box)
    # subtle darkening for caption legibility
    shade = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.blend(fr, shade, 0.22)

# ---------- card backgrounds ----------
random.seed(3)
noise = (np.random.rand(H, W) * 255).astype(np.uint8)
noise_img = Image.fromarray(noise).filter(ImageFilter.GaussianBlur(0.6))
_bg = {}
def card_bg(c1, c2, grain=10):
    key = (c1, c2)
    if key in _bg: return _bg[key]
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / W) ** 2 + ((y - H * 0.45) / H) ** 2) / 0.75
    d = np.clip(d, 0, 1)[..., None]
    a = np.array(c1)[None, None]; b = np.array(c2)[None, None]
    arr = a * (1 - d) + b * d
    n = (np.asarray(noise_img, dtype=np.float32)[..., None] - 128) / 128 * grain
    arr = np.clip(arr + n, 0, 255).astype(np.uint8)
    _bg[key] = Image.fromarray(arr, "RGB")
    return _bg[key]

# ---------- logo badge ----------
LOGO_W = Image.open(os.path.join(ROOT, "brand", "logo_blanc.png")).convert("RGBA")
LOGO_C = Image.open(os.path.join(ROOT, "brand", "logo_couleur.png")).convert("RGBA")
def logo(color, w):
    src = LOGO_C if color else LOGO_W
    return src.resize((w, round(src.height * w / src.width)), Image.LANCZOS)
_lg = {}
def draw_badge(img, color=False):
    if color not in _lg:
        lg = logo(color, 112)
        sh = Image.new("RGBA", (lg.width + 30, lg.height + 30), (0, 0, 0, 0))
        a = lg.split()[3].point(lambda v: int(v * (0.25 if color else 0.55)))
        sh.paste(Image.new("RGBA", lg.size, (0, 0, 0, 255)), (15, 17), a)
        sh = sh.filter(ImageFilter.GaussianBlur(5))
        _lg[color] = (lg, sh)
    lg, sh = _lg[color]
    x, y = 26, 30
    img.paste(sh, (x - 15, y - 15), sh)
    img.paste(lg, (x, y), lg)

# ---------- karaoke captions ----------
CAP_F = 52
def layout_words(text, f, maxw=600):
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if cur and f.getlength(test) > maxw:
            lines.append(cur); cur = [w]
        else: cur.append(w)
    if cur: lines.append(cur)
    return lines

def draw_caption(img, text, t, times):
    f = font("xb", CAP_F)
    lines = layout_words(text, f)
    lh = CAP_F * 1.12
    y0 = H * 0.56 - lh * len(lines) / 2
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer); ds = ImageDraw.Draw(shadow)
    idx = 0
    sp = f.getlength(" ")
    for li, line in enumerate(lines):
        lw = sum(f.getlength(w) for w in line) + sp * (len(line) - 1)
        x = (W - lw) / 2
        y = y0 + li * lh
        for w in line:
            ts = times[idx]
            k = (t - ts) / 0.12
            if k >= 0:
                a = 255; col = (214, 186, 120) if t - ts < 0.28 else (255, 255, 255)
                dy = -12 * (1 - ease_out(k))
            else:
                a = 120; col = (225, 225, 225); dy = 0
            ds.text((x + 3, y + dy + 4), w, font=f, fill=(0, 0, 0, int(a * 0.85)))
            d.text((x, y + dy), w, font=f, fill=col + (a,), stroke_width=2, stroke_fill=(20, 20, 20, int(a * 0.6)))
            x += f.getlength(w) + sp
            idx += 1
    shadow = shadow.filter(ImageFilter.GaussianBlur(5))
    img.paste(shadow, (0, 0), shadow)
    img.paste(layer, (0, 0), layer)

# ---------- typographic cards ----------
def fit(kind, size, text, maxw=640):
    f = font(kind, size)
    while f.getlength(text) > maxw and size > 20:
        size -= 2; f = font(kind, size)
    return f

def draw_card(t, dur, spec):
    bg = card_bg(spec["c1"], spec["c2"], spec.get("grain", 10))
    z = 1.14 - 0.14 * ease_out(t / 0.3) + 0.04 * (t / dur)
    base = bg.copy()
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    items = []
    for (txt, kind, size, col) in spec["lines"]:
        if kind == "script":
            txt = txt.upper(); kind = "anton"; size = int(size * 0.82)
        f = fit(kind, size, txt)
        bb = f.getbbox(txt)
        h = (size * (1.08 if kind == "anton" else 1.18))
        items.append((txt, f, col, h))
    total = sum(i[3] for i in items)
    y = H * 0.5 - total / 2
    for k, (txt, f, col, h) in enumerate(items):
        p = (t - spec["ltimes"][k] + 0.08) / 0.2
        if p > 0:
            a = int(255 * min(1, p * 1.6))
            dx = (90 if k % 2 else -90) * (1 - ease_out(p))
            d.text((W / 2 + dx, y + h / 2), txt, font=f, fill=col + (a,), anchor="mm")
        y += h
    if z != 1:
        lw, lh = int(W * z), int(H * z)
        layer = layer.resize((lw, lh), Image.BICUBIC).crop(((lw - W) // 2, (lh - H) // 2, (lw - W) // 2 + W, (lh - H) // 2 + H))
    base.paste(layer, (0, 0), layer)
    return base

# ---------- title (red boxes) ----------
def draw_title(img, t, lines):
    d = ImageDraw.Draw(img, "RGBA")
    y = 330
    for k, (txt, size) in enumerate(lines):
        f = font("anton", size)
        p = (t - 0.1 - k * 0.13) / 0.25
        if p <= 0:
            y += size * 1.25; continue
        s = back_out(p)
        tw = f.getlength(txt)
        bw, bh = (tw + 26) * min(1, s), size * 1.18
        x0 = W / 2 - bw / 2
        d.rectangle((x0, y, x0 + bw, y + bh), fill=(11, 61, 32, 240))
        if p > 0.5:
            d.text((W / 2, y + bh / 2), txt, font=f, fill=(255, 255, 255, int(255 * min(1, (p - 0.5) * 2))), anchor="mm")
        y += bh + 6

# ---------- end icons ----------
def draw_end(img, t):
    d = ImageDraw.Draw(img, "RGBA")
    cy = H * 0.73
    icons = ["heart", "share", "comment"]
    for k, ic in enumerate(icons):
        p = (t - 0.3 - k * 0.35) / 0.4
        if p <= 0: continue
        s = back_out(p)
        cx = W / 2 + (k - 1) * 150
        r = 50 * s
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, 235))
        u = 22 * s
        if ic == "heart":
            col = (226, 38, 64, 255)
            d.ellipse((cx - u, cy - u * 0.8, cx, cy + u * 0.2), fill=col)
            d.ellipse((cx, cy - u * 0.8, cx + u, cy + u * 0.2), fill=col)
            d.polygon([(cx - u * 0.98, cy - u * 0.15), (cx + u * 0.98, cy - u * 0.15), (cx, cy + u)], fill=col)
        elif ic == "share":
            col = (58, 117, 196, 255)
            d.polygon([(cx - u, cy - u * 0.35), (cx + u * 0.1, cy - u * 0.35), (cx + u * 0.1, cy - u * 0.9),
                       (cx + u, cy), (cx + u * 0.1, cy + u * 0.9), (cx + u * 0.1, cy + u * 0.35), (cx - u, cy + u * 0.35)], fill=col)
        else:
            col = (0, 158, 96, 255)
            d.rounded_rectangle((cx - u, cy - u * 0.8, cx + u, cy + u * 0.5), radius=u * 0.4, fill=col)
            d.polygon([(cx - u * 0.4, cy + u * 0.4), (cx - u * 0.6, cy + u), (cx, cy + u * 0.4)], fill=col)
            for j in (-1, 0, 1):
                d.ellipse((cx + j * u * 0.5 - 3 * s, cy - u * 0.15 - 3 * s, cx + j * u * 0.5 + 3 * s, cy - u * 0.15 + 3 * s), fill=(255, 255, 255, 255))
    labels = ["J'aime", "Partagez", "Commentez"]
    f = font("b", 24)
    for k, lb in enumerate(labels):
        p = (t - 0.5 - k * 0.35) / 0.4
        if p <= 0: continue
        cx = W / 2 + (k - 1) * 150
        d.text((cx, cy + 80), lb, font=f, fill=(255, 255, 255, int(255 * ease_out(p))), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0, 160))

# ---------- FEG storyboard, timed on continuous narration ----------
pieces = lambda: storylib.pieces(story)

def prop_times(units, dur):
    lens = [len(u) + 1 for u in units]; tot = sum(lens); acc = 0; out = []
    for l in lens:
        out.append(dur * acc / tot); acc += l
    return out

LEAD = 0.3
PS = ALIGN["pieces"]; KEYS = [k for k, _ in pieces()]
def pstart(key): return PS[key][0] + LEAD
def pspan(key):
    i = KEYS.index(key)
    return (PS[KEYS[i + 1]][0] if i + 1 < len(KEYS) else PS[key][1]) - PS[key][0]
first_key = lambda i, sc: f"{i}_0" if sc["kind"] == "photo" else f"{i}"
for i, sc in enumerate(story):
    sc["start"] = 0.0 if i == 0 else pstart(first_key(i, sc)) - 0.1
for i, sc in enumerate(story):
    end = story[i + 1]["start"] if i + 1 < len(story) else PS[KEYS[-1]][1] + LEAD + 2.2
    sc["dur"] = end - sc["start"]
    if sc["kind"] == "photo":
        sc["cd"], sc["wt"] = [], []
        for j, (disp, _) in enumerate(sc["chunks"]):
            key = f"{i}_{j}"
            cs = sc["start"] + sum(sc["cd"])
            nxt = pstart(f"{i}_{j+1}") - 0.1 if j + 1 < len(sc["chunks"]) else sc["start"] + sc["dur"]
            sc["cd"].append(nxt - cs)
            off = pstart(key) - cs
            sc["wt"].append([off + x for x in prop_times(disp.split(), pspan(key) * 0.92)])
    elif sc["kind"] == "card":
        off = pstart(f"{i}") - sc["start"]
        sc["ltimes"] = [off + x for x in prop_times([l[0] for l in sc["lines"]], pspan(f"{i}") * 0.92)]
    elif sc["kind"] == "end":
        txt = sc["say"]; off = pstart(f"{i}") - sc["start"]
        at = lambda w: off + pspan(f"{i}") * 0.95 * txt.index(w) / len(txt)
        sc["cta"] = at("Pense"); sc["t_ab"] = at("abonner"); sc["t_like"] = at("liker"); sc["t_man"] = at("pour ne rien")
        if True:  # recalage sur les pauses réelles de la voix
            import soundfile as _sf
            _s, _sr = _sf.read(ALIGN["full"]); _a, _b = PS[KEYS[-1]]
            seg = _s[int(_a * _sr):int(_b * _sr) + _sr // 2]; hp = _sr // 100
            e_ = np.array([np.sqrt(np.mean(seg[q:q + hp] ** 2)) for q in range(0, len(seg) - hp, hp)])
            sl = e_ < 0.03 * e_.max(); gp = []; q = 0
            while q < len(sl):
                if sl[q]:
                    j = q
                    while j < len(sl) and sl[j]: j += 1
                    if j - q >= 8 and j < len(sl): gp.append((q / 100, j / 100))
                    q = j
                else: q += 1
            spk = (np.where(~sl)[0][-1]) / 100
            # biggest gap in the first 75% of the line = pause after "action."
            cand = [g for g in gp if g[0] < 0.75 * spk]
            pg = max(cand, key=lambda g: g[1] - g[0])
            pense = pg[1]
            nxt = [g for g in gp if g[0] > pense + 0.5]
            if len(nxt) >= 2:
                like, pour = nxt[0][1] + 0.12, nxt[1][1]
            else:
                pour = nxt[0][1] if nxt else pense + 0.55 * (spk - pense)
                like = pense + 0.72 * ((nxt[0][0] if nxt else pour) - pense)
            o = 0.1
            sc["cta"], sc["t_ab"], sc["t_like"], sc["t_man"] = pense + o - 0.05, pense + o - 0.05, like + o, pour + o
            print("gaps", gp, file=sys.stderr)
            print("cta", sc["cta"], sc["t_ab"], sc["t_like"], sc["t_man"], sc["dur"], file=sys.stderr)
total = story[-1]["start"] + story[-1]["dur"]
print("total", round(total, 2), file=sys.stderr)
json.dump({"total": total, "cuts": [sc["start"] for sc in story if sc["kind"] == "card"],
           "voice": [[LEAD, ALIGN["full"]]]}, open(f"{BUILD}/timing_{TAG}.json", "w"))

LOGO_END = logo(False, 330)
BR = (206, 178, 116)

def icon(d, ic, cx, cy, s):
    d.ellipse((cx - 46 * s, cy - 46 * s, cx + 46 * s, cy + 46 * s), fill=(255, 255, 255, 240), outline=BR + (255,), width=max(1, int(4 * s)))
    u = 21 * s; G = (11, 61, 32, 255)
    if ic == "heart":
        col = (205, 40, 60, 255)
        d.ellipse((cx - u, cy - u * 0.8, cx, cy + u * 0.2), fill=col); d.ellipse((cx, cy - u * 0.8, cx + u, cy + u * 0.2), fill=col)
        d.polygon([(cx - u * 0.98, cy - u * 0.15), (cx + u * 0.98, cy - u * 0.15), (cx, cy + u)], fill=col)
    elif ic == "bell":
        d.chord((cx - u * 0.8, cy - u, cx + u * 0.8, cy + u * 0.6), 180, 360, fill=G)
        d.rectangle((cx - u * 0.8, cy - u * 0.2, cx + u * 0.8, cy + u * 0.5), fill=G)
        d.polygon([(cx - u * 0.8, cy + u * 0.4), (cx - u * 1.05, cy + u * 0.75), (cx + u * 1.05, cy + u * 0.75), (cx + u * 0.8, cy + u * 0.4)], fill=G)
        d.ellipse((cx - u * 0.25, cy + u * 0.7, cx + u * 0.25, cy + u * 1.1), fill=G)
    elif ic == "share":
        d.polygon([(cx - u, cy - u * 0.35), (cx + u * 0.1, cy - u * 0.35), (cx + u * 0.1, cy - u * 0.9), (cx + u, cy),
                   (cx + u * 0.1, cy + u * 0.9), (cx + u * 0.1, cy + u * 0.35), (cx - u, cy + u * 0.35)], fill=G)
    elif ic == "comment":
        d.rounded_rectangle((cx - u, cy - u * 0.8, cx + u, cy + u * 0.5), radius=u * 0.4, fill=G)
        d.polygon([(cx - u * 0.4, cy + u * 0.4), (cx - u * 0.6, cy + u), (cx, cy + u * 0.4)], fill=G)
        for j in (-1, 0, 1):
            d.ellipse((cx + j * u * 0.5 - 3 * s, cy - u * 0.15 - 3 * s, cx + j * u * 0.5 + 3 * s, cy - u * 0.15 + 3 * s), fill=(255, 255, 255, 255))
    elif ic == "plus":
        d.rectangle((cx - u, cy - u * 0.18, cx + u, cy + u * 0.18), fill=G); d.rectangle((cx - u * 0.18, cy - u, cx + u * 0.18, cy + u), fill=G)

TICK = [("heart", "J'aime"), ("bell", "Abonne-toi"), ("share", "Partage"), ("comment", "Commente"), ("plus", "Suis la FEG")]
def draw_ticker(img, t, alpha):
    if alpha <= 0: return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    cy = int(H * 0.79); sp = 170; L = sp * len(TICK)
    d.rectangle((0, cy - 70, W, cy + 92), fill=(11, 61, 32, 200))
    d.rectangle((0, cy - 72, W, cy - 68), fill=BR + (255,)); d.rectangle((0, cy + 90, W, cy + 94), fill=BR + (255,))
    off = (t * 190) % L
    f = font("b", 22)
    for rep_ in range(-1, 3):
        for k, (ic, lb) in enumerate(TICK):
            cx = W - off + rep_ * L + k * sp - L + sp / 2
            if -80 < cx < W + 80:
                bob = 1 + 0.08 * math.sin(t * 6 + k)
                icon(d, ic, cx, cy, 0.95 * bob)
                d.text((cx, cy + 68), lb, font=f, fill=(255, 255, 255, 255), anchor="mm")
    a = layer.split()[3].point(lambda v: int(v * alpha)); img.paste(layer, (0, 0), a)

def draw_cta_icon(img, lt, sc):
    cx, cy = W / 2, H * 0.80
    items = [("bell", "S'ABONNER", sc["t_ab"] - 0.1), ("heart", "J'AIME", sc["t_like"] - 0.1)]
    for j, (ic, lb, ts) in enumerate(items):
        nxt = items[j + 1][2] if j + 1 < len(items) else 1e9
        if not (ts <= lt < nxt + 0.2): continue
        a_in = (lt - ts) / 0.3
        out = (lt - nxt) / 0.2  # pop-out of the previous icon
        if out > 0:
            s = 1.6 * (1 - ease_out(out)); alpha = 1 - out
        else:
            s = 1.6 * back_out(a_in); alpha = min(1, a_in * 2)
            pr = (lt - ts - 0.45) / 0.25  # "tap" pulse
            if 0 < pr < 1: s *= 1 - 0.12 * math.sin(math.pi * pr)
        if s <= 0.02: continue
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
        rb = (lt - ts - 0.55) / 0.5  # ring burst after tap
        if 0 < rb < 1 and out <= 0:
            rr = 80 + 70 * ease_out(rb)
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=BR + (int(255 * (1 - rb)),), width=5)
        icon(d, ic, cx, cy, s)
        f = font("anton", 40)
        d.text((cx, cy + 112), lb, font=f, fill=(255, 255, 255, 255), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0, 140))
        al = layer.split()[3].point(lambda v: int(v * max(0, min(1, alpha))))
        img.paste(layer, (0, 0), al)

def render(t):
    for sc in story:
        if sc["start"] <= t < sc["start"] + sc["dur"] or sc is story[-1]:
            break
    lt = t - sc["start"]; p = lt / sc["dur"]
    k = sc["kind"]
    if k == "card":
        img = draw_card(lt, sc["dur"], sc)
    else:
        cx0, cx1, z0, z1 = sc["pan"]
        punch = 0.12 * (1 - ease_out(lt / 0.25))
        img = photo_frame(sc["pid"], p, cx0, cx1, z0 + punch, z1 + 0.14, sc.get("cy", 0.5))
        if k == "title":
            draw_title(img, lt, sc["lines"])
        elif k == "photo":
            a = 0
            for (c, _), cd, wt in zip(sc["chunks"], sc["cd"], sc["wt"]):
                if lt < a + cd or c == sc["chunks"][-1][0]:
                    draw_caption(img, c, lt - a, [x for x in wt]); break
                a += cd
        elif k == "end":
            img = Image.blend(img, Image.new("RGB", (W, H), (4, 30, 15)), 0.6)
            pp = back_out(lt / 0.5)
            lw = max(1, int(LOGO_END.width * (0.85 + 0.15 * pp)))
            lg = LOGO_END.resize((lw, round(LOGO_END.height * lw / LOGO_END.width)), Image.BICUBIC)
            al = lg.split()[3].point(lambda v: int(v * min(1, lt / 0.3)))
            img.paste(lg, ((W - lw) // 2, int(H * 0.12)), al)
            d = ImageDraw.Draw(img, "RGBA")
            q = ease_out((lt - 0.4) / 0.4)
            d.text((W / 2, H * 0.47), "LE SECTEUR PRIVÉ EN ACTION", font=font("anton", 48), fill=BR + (int(255 * q),), anchor="mm")
            c = lt - sc["cta"]
            for j, (txt, fk, sz, col) in enumerate([("PENSE À T'ABONNER,", "anton", 66, (255, 255, 255)), ("LIKER POUR NE RIEN", "anton", 66, (255, 255, 255)), ("MANQUER !", "anton", 84, BR)]):
                pj = (lt - [sc["cta"] - 0.05, sc["t_like"] - 0.1, sc["t_man"] + 0.3][j]) / 0.22
                if pj > 0:
                    s_ = back_out(pj); fz = font(fk, max(8, int(sz * (0.6 + 0.4 * s_))))
                    d.text((W / 2, H * 0.555 + j * 78), txt, font=fz, fill=col + (int(255 * min(1, pj)),), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0, 120))
            draw_cta_icon(img, lt, sc)
    if k in ("photo",) and lt < 0.16 and t > 0.1:
        q = 1 - ease_out(lt / 0.16); sh = int(160 * q)
        moved = Image.new("RGB", (W, H)); moved.paste(img, (sh, 0))
        if sh: moved.paste(img.crop((W - sh, 0, W, H)), (0, 0))
        img = moved.filter(ImageFilter.BoxBlur(int(10 * q))) if q > 0.05 else moved
    ImageDraw.Draw(img).rectangle((0, H - 7, int(W * t / total), H), fill=BR)
    draw_badge(img, color=(k == "card" and sc["c1"] == CREME[0]))
    if lt < 0.08 and t > 0.1:
        img = Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), 0.35 * (1 - lt / 0.08))
    if t > total - 0.5:
        img = Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), min(1, (t - (total - 0.5)) / 0.5))
    return img

if PREVIEW:
    import os; e = story[-1]; times = [float(x) for x in os.environ["PT"].split()] if os.environ.get("PT") else [e["start"] + e["t_ab"] + 0.2, e["start"] + e["t_ab"] + 0.7, e["start"] + e["t_like"] + 0.05, e["start"] + e["t_like"] + 0.4, e["start"] + e["t_like"] + 0.8, total - 0.8]
    ims = [render(tt).resize((240, 427)) for tt in times]
    cols = 6; rows = math.ceil(len(ims) / cols)
    sheet = Image.new("RGB", (240 * cols, 427 * rows))
    for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * 240, (i // cols) * 427))
    sheet.save(f"{BUILD}/preview_{TAG}.jpg", quality=85)
    sys.exit()

nf = int(total * FPS)
proc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", f"{BUILD}/video_{TAG}_noaudio.mp4"], stdin=subprocess.PIPE)
for i in range(nf):
    proc.stdin.write(render(i / FPS).tobytes())
proc.stdin.close(); proc.wait()
print("done frames", nf, file=sys.stderr)
