import adsk.core, adsk.fusion, os

# Design 2 CFD domain: same as cfd_geometry_fusion.py but with the improved heatsink below.
# Same envelope as stock (X ±8.75, Y ±10.5, Z 30.5–46.03 + boss to 49.03), same spine, socket, boss and latch web.
# Changes: 6 horizontal fins 0.7 mm thick (stock 5 x 1 mm) with ~1.05 mm gaps, 5 bottom fingers per side (stock 3).
HERE = r"C:\Users\natth\Documents\Asys Com aid\Ansys Project\cfd"
base = {}
exec(open(os.path.join(HERE, "cfd_geometry_fusion.py"), encoding="utf-8").read(), base)
cl = base["cl"]
V, P, OP, plane, poly, revolve = cl["V"], cl["P"], cl["OP"], cl["plane"], cl["poly"], cl["revolve"]

TOP, FIN_T, N_FIN = 46.03, 0.7, 6
BASE_Z = (35.0, 35.5)
FINGER_Z = (30.5, 34.41)
FINGERS = [(3.0, 3.7), (4.7, 5.4), (6.4, 7.1), (8.1, 8.8), (9.8, 10.5)]    # +Y side; mirrored to -Y
SLOT = dict(y=5.0, z_top=41.2)            # latch slot on +Y: fins below z_top stop at y = 5.0
WEB = [(6.0, 7.0, 37.0, 40.0)]            # latch web (holds the latch bump), joined to the fin below
HS_X = cl["HS_HALF_X"]


def fins():
    gap = (TOP - BASE_Z[1] - N_FIN * FIN_T) / N_FIN
    out = []
    for i in range(N_FIN):
        zt = TOP - i * (FIN_T + gap)
        zb = zt - FIN_T
        ymax = SLOT["y"] if zb < SLOT["z_top"] else 10.5
        out.append((-10.5, ymax, zb, zt))
    return out, gap


def build_cold_end_v2(comp):
    plates, gap = fins()
    rects = [(-2.25, 2.25, BASE_Z[0], TOP),                       # spine
             (-10.5, 10.5, BASE_Z[0], BASE_Z[1]),                  # base plate
             (-10.5, -3.0, FINGER_Z[1], BASE_Z[0]), (3.0, 10.5, FINGER_Z[1], BASE_Z[0])]
    rects += plates
    for y0, y1 in FINGERS:
        rects += [(y0, y1, FINGER_Z[0], FINGER_Z[1]), (-y1, -y0, FINGER_Z[0], FINGER_Z[1])]
    # latch web + bar joining it to the nearest fin below z 40
    hold = max((p for p in plates if p[3] <= 40.0), key=lambda p: p[3])
    rects += [(SLOT["y"], 7.0, hold[2], hold[3])] + WEB    # bar first: a join must touch the body already built
    body = None
    for y0, y1, z0, z1 in rects:
        sk = comp.sketches.add(comp.yZConstructionPlane)
        poly(sk, [P(0, y0, z0), P(0, y1, z0), P(0, y1, z1), P(0, y0, z1)])
        inp = comp.features.extrudeFeatures.createInput(
            sk.profiles.item(0), OP.NewBodyFeatureOperation if body is None else OP.JoinFeatureOperation)
        inp.setSymmetricExtent(V(2 * HS_X / 10), True)
        if body is not None:
            inp.participantBodies = [body]
        f = comp.features.extrudeFeatures.add(inp)
        body = body or f.bodies.item(0)
    # boss, boss hole and socket exactly as the stock builder
    revolve(comp, [(0, TOP), (cl["BOSS_R"], TOP), (cl["BOSS_R"], cl["BOSS_TOP"]), (0, cl["BOSS_TOP"])],
            OP.JoinFeatureOperation, [body])
    revolve(comp, [(0, TOP), (cl["BOSS_HOLE_R"], TOP), (cl["BOSS_HOLE_R"], cl["BOSS_TOP"]), (0, cl["BOSS_TOP"])],
            OP.CutFeatureOperation, [body])
    revolve(comp, [(0, cl["SOCKET_Z0"] - 0.1), (cl["SOCKET_R"], cl["SOCKET_Z0"] - 0.1), (cl["SOCKET_R"], cl["SOCKET_Z1"]),
                   (0, cl["SOCKET_Z1"])], OP.CutFeatureOperation, [body])
    body.name = "ColdEnd_Heatsink"
    bb = body.boundingBox
    print("D2 heatsink: fins %d x %.2f mm, gap %.3f mm, area %.0f mm2, vol %.0f mm3, bbox %s" % (
        N_FIN, FIN_T, gap, body.area * 100, body.volume * 1000,
        [round(v * 10, 2) for v in (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z, bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)]))
    return body


cl["build_cold_end"] = build_cold_end_v2
base["STEP"] = os.path.join(HERE, "hotend_cfd_domain_d2.step")


def run(_context: str):
    base["run"](_context)
    app = adsk.core.Application.get()
    app.activeDocument.name = "Hotend CFD domain D2"
    root = adsk.fusion.Design.cast(app.activeProduct).rootComponent
    for occ in root.occurrences:                                   # picture of the new heatsink only
        occ.isLightBulbOn = occ.component.name in ("Heatsink", "HotEnd")
    vp = app.activeViewport
    cam = vp.camera
    cam.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
    cam.isFitView = True
    vp.camera = cam
    vp.refresh()
    vp.saveAsImageFile(os.path.join(HERE, "results", "design2_heatsink_iso.png"), 900, 900)
    cam = vp.camera
    cam.viewOrientation = adsk.core.ViewOrientations.RightViewOrientation
    cam.isFitView = True
    vp.camera = cam
    vp.refresh()
    vp.saveAsImageFile(os.path.join(HERE, "results", "design2_heatsink_side.png"), 900, 900)
    for occ in root.occurrences:
        occ.isLightBulbOn = True
