import cv2, numpy as np, sys, json

def load_mask(path, upscale=2, blur=3, thr=110, morph=0):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise SystemExit(f"cannot read {path}")
    h, w = img.shape
    if upscale != 1:
        img = cv2.resize(img, (w*upscale, h*upscale), interpolation=cv2.INTER_CUBIC)
    if blur:
        img = cv2.GaussianBlur(img, (blur, blur), 0)
    # white shapes -> foreground
    _, m = cv2.threshold(img, thr, 255, cv2.THRESH_BINARY)
    if morph:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (morph, morph))
        # OPEN removes thin spikes/whiskers; CLOSE fills small notches -> clean edges
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
        m = cv2.GaussianBlur(m, (blur, blur), 0)
        _, m = cv2.threshold(m, 127, 255, cv2.THRESH_BINARY)
    return m

def catmull_to_bezier(pts, closed=True):
    """Return SVG path string using Catmull-Rom -> cubic bezier for smoothness."""
    n = len(pts)
    if n < 3:
        return ""
    def P(i): return pts[i % n]
    d = f"M {P(0)[0]:.1f},{P(0)[1]:.1f} "
    for i in range(n):
        p0 = P(i-1); p1 = P(i); p2 = P(i+1); p3 = P(i+2)
        c1x = p1[0] + (p2[0]-p0[0])/6.0
        c1y = p1[1] + (p2[1]-p0[1])/6.0
        c2x = p2[0] - (p3[0]-p1[0])/6.0
        c2y = p2[1] - (p3[1]-p1[1])/6.0
        d += f"C {c1x:.1f},{c1y:.1f} {c2x:.1f},{c2y:.1f} {p2[0]:.1f},{p2[1]:.1f} "
    return d + "Z "

def trace(path, eps=1.4, min_area=120, **kw):
    m = load_mask(path, **kw)
    H, W = m.shape
    cnts, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    paths = []
    for c in cnts:
        if cv2.contourArea(c) < min_area:
            continue
        approx = cv2.approxPolyDP(c, eps, True)
        pts = [(float(p[0][0]), float(p[0][1])) for p in approx]
        if len(pts) < 3:
            continue
        paths.append(catmull_to_bezier(pts))
    return W, H, paths

if __name__ == "__main__":
    src = sys.argv[1]
    out = sys.argv[2]
    eps = float(sys.argv[3]) if len(sys.argv) > 3 else 1.4
    minarea = float(sys.argv[4]) if len(sys.argv) > 4 else 120
    W, H, paths = trace(src, eps=eps, min_area=minarea)
    d = " ".join(paths)
    result = {"w": W, "h": H, "n": len(paths), "d": d}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f)
    print(f"traced {src}: {W}x{H}, {len(paths)} contours, {len(d)} chars")
