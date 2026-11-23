"""Place the 1:1 X2D STLs in assembled position (nozzle tip at origin, Z up, clip/latch side +Y, fins
open along X) and write them to X2D_Nozzle_assembled/. Every map is a proper rotation (det +1) + shift."""
import os, struct, sys
sys.path.insert(0, os.path.dirname(__file__))
from stlinfo import tris

D = r"C:\Users\natth\Documents\Asys Com aid\Ansys Project"
SRC, OUT = os.path.join(D, "X2D_Nozzle_1x"), os.path.join(D, "X2D_Nozzle_assembled")

# Hot end printed tip-up: axis (145.975, 43.775); stub top z=0 -> Z=39, tip z=39 -> Z=0.
hot = lambda x, y, z: (x - 145.975, -(y - 43.775), 39.0 - z)
# Cold end printed on its side, boss toward -y. Socket bottom y=43.43 sits on the stub top (Z=39).
cold = lambda x, y, z: (-(z - 8.75), x - 42.67, 39.0 + 43.43 - y)
# Latch ("magnet") plate: 17.5 along X, 5.5 tall, 2 thick in the slot at Y 7..9, bump toward -Y.
mag = lambda x, y, z: (y - 42.04, 9.0 - z, 38.25 - (x - 156.27))

MAPS = {"obj_1_Hot-End.stl": hot, "obj_3_Cold-End.stl": cold, "obj_2_Magnet.stl": mag}


def det(f):
    o = f(0, 0, 0)
    m = [[f(*e)[i] - o[i] for e in ((1, 0, 0), (0, 1, 0), (0, 0, 1))] for i in range(3)]
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


os.makedirs(OUT, exist_ok=True)
for name, f in MAPS.items():
    assert abs(det(f) - 1) < 1e-9, name          # no mirroring, so normals/winding stay valid
    ts = [[f(*p) for p in t] for t in tris(os.path.join(SRC, name))]
    buf = bytearray(b"X2D assembled " + name.encode())[:80].ljust(80, b" ") + struct.pack("<I", len(ts))
    lo, hi = [1e9] * 3, [-1e9] * 3
    for a, b, c in ts:
        u = [b[i] - a[i] for i in range(3)]; w = [c[i] - a[i] for i in range(3)]
        n = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]]
        L = sum(v * v for v in n) ** 0.5 or 1.0
        buf += struct.pack("<12fH", *[v / L for v in n], *a, *b, *c, 0)
        for p in (a, b, c):
            for k in range(3):
                lo[k] = min(lo[k], p[k]); hi[k] = max(hi[k], p[k])
    open(os.path.join(OUT, name), "wb").write(buf)
    print(name, "min", [round(v, 2) for v in lo], "max", [round(v, 2) for v in hi])
