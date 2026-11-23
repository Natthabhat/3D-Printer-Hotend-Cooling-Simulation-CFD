"""Print triangle count and bounding box of STL files (binary or ASCII). Usage: python stlinfo.py f1.stl ..."""
import struct, sys

def tris(path):
    data = open(path, "rb").read()
    n = struct.unpack_from("<I", data, 80)[0] if len(data) >= 84 else -1
    if len(data) == 84 + 50 * n:                      # binary
        for i in range(n):
            v = struct.unpack_from("<12f", data, 84 + 50 * i)
            yield v[3:6], v[6:9], v[9:12]
    else:                                             # ASCII
        pts = [tuple(map(float, l.split()[1:4])) for l in data.decode("ascii", "ignore").splitlines()
               if l.strip().startswith("vertex")]
        for i in range(0, len(pts), 3):
            yield pts[i:i + 3]

for f in (sys.argv[1:] if __name__ == "__main__" else []):
    lo, hi, n = [1e9] * 3, [-1e9] * 3, 0
    for t in tris(f):
        n += 1
        for p in t:
            for k in range(3):
                lo[k] = min(lo[k], p[k]); hi[k] = max(hi[k], p[k])
    size = [hi[k] - lo[k] for k in range(3)]
    print(f, "tris", n, "min", [round(v, 2) for v in lo], "max", [round(v, 2) for v in hi],
          "size", [round(v, 2) for v in size], "size/3", [round(v / 3, 2) for v in size])
