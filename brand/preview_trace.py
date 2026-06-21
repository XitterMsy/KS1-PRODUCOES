import cv2, numpy as np, sys
from trace import load_mask

def preview(path, out, eps=1.4, min_area=120, **kw):
    m = load_mask(path, **kw)
    H, W = m.shape
    cnts, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    canvas = np.zeros((H, W), np.uint8)
    approxed = []
    hh = hier[0] if hier is not None else []
    for i, c in enumerate(cnts):
        if cv2.contourArea(c) < min_area:
            approxed.append(None); continue
        approxed.append(cv2.approxPolyDP(c, eps, True))
    # outer first (white), then holes (black)
    for i, a in enumerate(approxed):
        if a is None: continue
        is_hole = hh[i][3] != -1
        cv2.drawContours(canvas, [a], -1, 0 if is_hole else 255, thickness=cv2.FILLED)
    # downscale for viewing
    scale = 600.0 / max(H, W)
    small = cv2.resize(canvas, (int(W*scale), int(H*scale)), interpolation=cv2.INTER_AREA)
    cv2.imwrite(out, small)
    print(f"preview {out}: {small.shape[1]}x{small.shape[0]}")

if __name__ == "__main__":
    preview(sys.argv[1], sys.argv[2],
            eps=float(sys.argv[3]) if len(sys.argv)>3 else 1.4,
            min_area=float(sys.argv[4]) if len(sys.argv)>4 else 120)
