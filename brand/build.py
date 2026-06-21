import cv2, numpy as np, sys
from trace import load_mask, catmull_to_bezier

def get_contours(path, eps=1.4, min_area=120, **kw):
    m = load_mask(path, **kw)
    H, W = m.shape
    cnts, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    hh = hier[0]
    items = []  # (idx, approx, is_hole, parent, bbox)
    for i, c in enumerate(cnts):
        if cv2.contourArea(c) < min_area:
            items.append(None); continue
        a = cv2.approxPolyDP(c, eps, True)
        x, y, w, h = cv2.boundingRect(a)
        items.append({"a": a, "hole": hh[i][3] != -1, "parent": hh[i][3],
                      "bbox": (x, y, w, h)})
    return W, H, items

def find_cut(path, **kw):
    """Find the empty horizontal band between KS1 body and PRODUCOES."""
    m = load_mask(path, **kw)
    H, W = m.shape
    rows = (m > 0).sum(axis=1)
    lo, hi = int(0.68*H), int(0.88*H)
    band = rows[lo:hi]
    cut = lo + int(np.argmin(band))
    return cut, H

def classify(W, H, items):
    """idx-> 'mark' or 'tag' by contour area. Holes follow parent.
    KS1 strokes are >0.6% of image; PRODUCOES letters are <0.1%."""
    thr = 0.003 * W * H
    cls = {}
    for i, it in enumerate(items):
        if it is None or it["hole"]: continue
        cls[i] = "tag" if cv2.contourArea(it["a"]) < thr else "mark"
    for i, it in enumerate(items):
        if it is None or not it["hole"]: continue
        cls[i] = cls.get(it["parent"], "mark")
    return cls

def group_path(items, cls, want):
    sub = [it for i, it in enumerate(items) if it is not None and cls.get(i) == want]
    if not sub:
        return None, None
    xs0 = min(it["bbox"][0] for it in sub)
    ys0 = min(it["bbox"][1] for it in sub)
    xs1 = max(it["bbox"][0]+it["bbox"][2] for it in sub)
    ys1 = max(it["bbox"][1]+it["bbox"][3] for it in sub)
    bbox = (xs0, ys0, xs1-xs0, ys1-ys0)
    d = ""
    for it in sub:
        pts = [(float(p[0][0]), float(p[0][1])) for p in it["a"]]
        if len(pts) >= 3:
            d += catmull_to_bezier(pts)
    return d, bbox

def render_group(W, H, items, cls, want, out):
    canvas = np.zeros((H, W), np.uint8)
    for i, it in enumerate(items):
        if it is None or cls.get(i) != want: continue
        cv2.drawContours(canvas, [it["a"]], -1, 0 if it["hole"] else 255, cv2.FILLED)
    scale = 500.0/max(H, W)
    small = cv2.resize(canvas, (int(W*scale), int(H*scale)))
    cv2.imwrite(out, small)

def full_path(items):
    d, x0, y0, x1, y1 = "", 1e9, 1e9, -1e9, -1e9
    for it in items:
        if it is None: continue
        x, y, w, h = it["bbox"]
        x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x+w), max(y1, y+h)
        pts = [(float(p[0][0]), float(p[0][1])) for p in it["a"]]
        if len(pts) >= 3:
            d += catmull_to_bezier(pts)
    return d, (x0, y0, x1-x0, y1-y0)

def place(d, bbox, tx, ty, target_h):
    """Wrap path d so its bbox maps to height target_h at top-left (tx,ty)."""
    x0, y0, w, h = bbox
    s = target_h / h
    return (f'<g transform="translate({tx - x0*s:.2f},{ty - y0*s:.2f}) '
            f'scale({s:.5f})"><path d="{d}"/></g>'), w*s

HEAD = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" aria-label="{al}">\n<title>{t}</title>\n'
FONT = "'Helvetica Neue',Arial,sans-serif"

def write(name, body):
    with open(name, "w", encoding="utf-8") as f:
        f.write(body)
    print("wrote", name)

if __name__ == "__main__":
    P = 90  # padding in source units
    # ---- KS1 ----
    # Mark (KS1 + swoosh): morph cleanup removes ragged whiskers/notches.
    # Tag (PRODUCOES, letras finas): SEM morph para nao destruir as letrinhas.
    MORPH = 25
    Wc, Hc, items_c = get_contours("ref/ks1.png", morph=MORPH)
    cls_c = classify(Wc, Hc, items_c)
    W, H, items_r = get_contours("ref/ks1.png", morph=0)
    cls_r = classify(W, H, items_r)
    mark_items = [items_c[i] for i in range(len(items_c)) if items_c[i] and cls_c.get(i)=="mark"]
    tag_items  = [items_r[i] for i in range(len(items_r)) if items_r[i] and cls_r.get(i)=="tag"]
    print("mark:", len(mark_items), "tag:", len(tag_items))
    mark_d, mark_bb = full_path(mark_items)
    tag_d,  tag_bb  = full_path(tag_items)
    full_d, full_bb = full_path(mark_items + tag_items)

    fx, fy, fw, fh = full_bb
    vb = f"{fx-P:.0f} {fy-P:.0f} {fw+2*P:.0f} {fh+2*P:.0f}"
    rx, ry, rw, rh = fx-P, fy-P, fw+2*P, fh+2*P
    EO = 'fill-rule="evenodd"'

    # principal (branco sobre preto)
    write("ks1-logo-principal.svg",
        HEAD.format(vb=vb, al="KS1 Producoes", t="KS1 PRODUCOES - Principal") +
        f'<rect x="{rx:.0f}" y="{ry:.0f}" width="{rw:.0f}" height="{rh:.0f}" rx="120" fill="#0A0A0C"/>\n'
        f'<path d="{full_d}" {EO} fill="#F5F6F8"/>\n</svg>\n')

    # preto e branco puro
    write("ks1-logo-pb.svg",
        HEAD.format(vb=vb, al="KS1 Producoes PB", t="KS1 PRODUCOES - Preto e Branco") +
        f'<rect x="{rx:.0f}" y="{ry:.0f}" width="{rw:.0f}" height="{rh:.0f}" rx="120" fill="#000000"/>\n'
        f'<path d="{full_d}" {EO} fill="#FFFFFF"/>\n</svg>\n')

    # transparente (branco)
    write("ks1-logo-transparente.svg",
        HEAD.format(vb=vb, al="KS1 Producoes transparente", t="KS1 PRODUCOES - Transparente") +
        f'<path d="{full_d}" {EO} fill="#F5F6F8"/>\n</svg>\n')

    # transparente preto (para fundo claro)
    write("ks1-logo-transparente-preto.svg",
        HEAD.format(vb=vb, al="KS1 Producoes preto", t="KS1 PRODUCOES - Transparente Preto") +
        f'<path d="{full_d}" {EO} fill="#0A0A0C"/>\n</svg>\n')

    # fundo claro
    write("ks1-logo-fundo-claro.svg",
        HEAD.format(vb=vb, al="KS1 Producoes fundo claro", t="KS1 PRODUCOES - Fundo Claro") +
        f'<rect x="{rx:.0f}" y="{ry:.0f}" width="{rw:.0f}" height="{rh:.0f}" rx="120" fill="#F5F6F8"/>\n'
        f'<path d="{full_d}" {EO} fill="#0A0A0C"/>\n</svg>\n')

    # icone quadrado (avatar) com leve gradiente + acento
    side = max(fw, fh) + 2*P
    ix = fx - (side - fw)/2
    iy = fy - (side - fh)/2
    vbi = f"{ix:.0f} {iy:.0f} {side:.0f} {side:.0f}"
    write("ks1-icon.svg",
        HEAD.format(vb=vbi, al="KS1 icone", t="KS1 - Icone") +
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#15171F"/><stop offset="1" stop-color="#06060A"/>'
        '</linearGradient></defs>\n'
        f'<rect x="{ix:.0f}" y="{iy:.0f}" width="{side:.0f}" height="{side:.0f}" rx="{side*0.22:.0f}" fill="url(#bg)"/>\n'
        f'<path d="{full_d}" {EO} fill="#F5F6F8"/>\n</svg>\n')

    # contato (logo + faixa de contato) ; canvas: logo on top, text below
    cw = rw
    ch = rh + 360
    vbc = f"{rx:.0f} {ry:.0f} {cw:.0f} {ch:.0f}"
    midx = rx + cw/2
    by = ry + rh + 60   # divider y
    write("ks1-logo-contato.svg",
        HEAD.format(vb=vbc, al="KS1 Producoes contato", t="KS1 PRODUCOES - Contato") +
        f'<rect x="{rx:.0f}" y="{ry:.0f}" width="{cw:.0f}" height="{ch:.0f}" rx="120" fill="#0A0A0C"/>\n'
        f'<path d="{full_d}" {EO} fill="#F5F6F8"/>\n'
        f'<rect x="{midx-360:.0f}" y="{by:.0f}" width="720" height="4" rx="2" fill="#23252B"/>\n'
        f'<text x="{midx:.0f}" y="{by+120:.0f}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="92" fill="#D7DAE0">Djkennim@gmail.com</text>\n'
        f'<text x="{midx:.0f}" y="{by+250:.0f}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="92" fill="#D7DAE0">+55 31 9795-2897</text>\n</svg>\n')

    # horizontal (KS1 mark + PRODUCOES brush ao lado)
    HH = 700.0
    _, mw = place(mark_d, mark_bb, 0, 0, HH)
    tagH = 175.0
    _, tw = place(tag_d, tag_bb, 0, 0, tagH)
    pad, gap = 80, 110
    div_w = 6
    mark_x, mark_y = pad, pad
    div_x = pad + mw + gap
    txt_x = div_x + div_w + gap
    # tagline metrics
    tl_text = "MUSIC . EVENTS . DJ"
    tl_fs, tl_ls = 50, 18
    tl_w = len(tl_text) * (tl_fs*0.60) + (len(tl_text)-1)*tl_ls
    # right block (PRODUCOES brush + tagline) centered vertically vs mark
    block_h = tagH + 55 + tl_fs
    block_top = pad + (HH - block_h)/2
    txt_y = block_top
    tl_y = block_top + tagH + 55 + tl_fs*0.8
    right_extent = txt_x + max(tw, tl_w)
    total_w = right_extent + pad
    total_h = HH + 2*pad
    gmark2, _ = place(mark_d, mark_bb, mark_x, mark_y, HH)
    gtag2, _  = place(tag_d, tag_bb, txt_x, txt_y, tagH)
    vbh = f"0 0 {total_w:.0f} {total_h:.0f}"
    write("ks1-logo-horizontal.svg",
        HEAD.format(vb=vbh, al="KS1 Producoes horizontal", t="KS1 PRODUCOES - Horizontal") +
        f'<rect width="{total_w:.0f}" height="{total_h:.0f}" rx="60" fill="#0A0A0C"/>\n'
        f'<g {EO} fill="#F5F6F8">{gmark2}</g>\n'
        f'<rect x="{div_x:.0f}" y="{pad+90:.0f}" width="{div_w}" height="{HH-180:.0f}" rx="3" fill="#2A2C33"/>\n'
        f'<g {EO} fill="#F5F6F8">{gtag2}</g>\n'
        f'<text x="{txt_x:.0f}" y="{tl_y:.0f}" font-family="{FONT}" font-size="{tl_fs}" '
        f'font-weight="500" letter-spacing="{tl_ls}" fill="#7C8190">{tl_text}</text>\n</svg>\n')

    # ---- KENNIM ----
    Wk, Hk, kitems = get_contours("ref/kennim.png")
    kd, kbb = full_path([it for it in kitems if it])
    kx, ky, kw_, kh_ = kbb
    Pk = 80
    vbk = f"{kx-Pk:.0f} {ky-Pk:.0f} {kw_+2*Pk:.0f} {kh_+2*Pk:.0f}"
    write("kennim-assinatura-transparente.svg",
        HEAD.format(vb=vbk, al="Kennim", t="Kennim - Assinatura Transparente") +
        f'<path d="{kd}" {EO} fill="#F5F6F8"/>\n</svg>\n')
    write("kennim-assinatura.svg",
        HEAD.format(vb=vbk, al="Kennim", t="Kennim - Assinatura") +
        f'<rect x="{kx-Pk:.0f}" y="{ky-Pk:.0f}" width="{kw_+2*Pk:.0f}" height="{kh_+2*Pk:.0f}" rx="80" fill="#0A0A0C"/>\n'
        f'<path d="{kd}" {EO} fill="#F5F6F8"/>\n</svg>\n')

    print("DONE")
