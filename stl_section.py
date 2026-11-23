"""Planar section of an STL as closed polylines, with collinear points merged.
Usage: python stl_section.py file.stl axis(x|y|z) value [tol_mm]"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from stlinfo import tris


def section(ts, ax, c):
    a1, a2 = [k for k in range(3) if k != ax]
    segs = []
    for t in ts:
        pts = []
        for p, q in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            if (p[ax] - c) * (q[ax] - c) < 0:
                f = (c - p[ax]) / (q[ax] - p[ax])
                pts.append((round(p[a1] + f * (q[a1] - p[a1]), 4), round(p[a2] + f * (q[a2] - p[a2]), 4)))
        if len(pts) == 2 and pts[0] != pts[1]:
            segs.append(tuple(pts))
    return segs


def chain(segs):
    """Join segments sharing endpoints into loops."""
    adj = {}
    for a, b in segs:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    seen, loops = set(), []
    for start in adj:
        if start in seen:
            continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            nxt = [n for n in adj[cur] if n != prev and (n not in seen or n == start)]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            if cur == start:
                break
            loop.append(cur)
            seen.add(cur)
        loops.append(loop)
    return loops


def simplify(loop, tol):
    """Drop points that lie within tol of the line through their neighbours."""
    changed = True
    while changed and len(loop) > 3:
        changed = False
        for i in range(len(loop)):
            a, b, c = loop[i - 1], loop[i], loop[(i + 1) % len(loop)]
            L = ((c[0] - a[0]) ** 2 + (c[1] - a[1]) ** 2) ** 0.5
            d = abs((c[0] - a[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (c[1] - a[1])) / L if L else 0
            if d < tol:
                del loop[i]
                changed = True
                break
    return loop


def loops(path, ax, c, tol=0.03):
    out = [simplify(l, tol) for l in chain(section(list(tris(path)), ax, c))]
    return [l for l in out if len(l) >= 3]


if __name__ == "__main__":
    f, ax, c = sys.argv[1], "xyz".index(sys.argv[2]), float(sys.argv[3])
    tol = float(sys.argv[4]) if len(sys.argv) > 4 else 0.03
    for l in loops(f, ax, c, tol):
        area = 0.5 * sum(l[i - 1][0] * l[i][1] - l[i][0] * l[i - 1][1] for i in range(len(l)))
        print("loop n=%d area=%.3f" % (len(l), area))
        print("  " + " ".join("(%.2f,%.2f)" % p for p in l))
