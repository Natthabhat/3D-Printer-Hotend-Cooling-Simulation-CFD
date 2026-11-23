"""Grid Convergence Index (Celik et al., 2008, J. Fluids Eng. 130:078001) for three meshes."""
import math


def gci(n1, n2, n3, f1, f2, f3, volume, fs=1.25):
    """n1 > n2 > n3 cells (fine, medium, coarse) and their results f1, f2, f3.
    Returns apparent order p, extrapolated value f_ext and GCI_fine / GCI_medium in % of f1 / f2."""
    h1, h2, h3 = ((volume / n) ** (1 / 3) for n in (n1, n2, n3))
    r21, r32 = h2 / h1, h3 / h2
    e21, e32 = f2 - f1, f3 - f2
    if e21 == 0 or e32 == 0:
        return dict(p=float("nan"), f_ext=f1, gci_fine=0.0, gci_medium=0.0, r21=r21, r32=r32, oscillatory=False)
    s = math.copysign(1, e32 / e21)
    p = 1.0
    for _ in range(100):                               # fixed-point iteration for the apparent order
        q = math.log((r21 ** p - s) / (r32 ** p - s))
        p_new = abs(math.log(abs(e32 / e21)) + q) / math.log(r21)
        if abs(p_new - p) < 1e-10:
            break
        p = p_new
    f_ext = (r21 ** p * f1 - f2) / (r21 ** p - 1)
    ea21, ea32 = abs(e21 / f1), abs(e32 / f2)
    return dict(p=p, f_ext=f_ext, r21=r21, r32=r32, oscillatory=s < 0,
                gci_fine=100 * fs * ea21 / (r21 ** p - 1), gci_medium=100 * fs * ea32 / (r32 ** p - 1))


if __name__ == "__main__":
    # self-check: f(h) = 10 + 3 h^2 on h = 1, 1.3, 1.69 must give p = 2 and f_ext = 10
    V = 1.0
    hs = [1.0, 1.3, 1.69]
    ns = [V / h ** 3 for h in hs]
    fs_ = [10 + 3 * h * h for h in hs]
    r = gci(*ns, *fs_, volume=V)
    assert abs(r["p"] - 2) < 1e-6 and abs(r["f_ext"] - 10) < 1e-6, r
    print("gci self-check ok:", {k: round(v, 6) if isinstance(v, float) else v for k, v in r.items()})
