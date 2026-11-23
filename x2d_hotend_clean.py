import adsk.core, adsk.fusion, math

# Clean parametric Bambu X2D/H2/P2S hotend rebuilt from sections of the 1:1 STLs (X2D_Nozzle_assembled).
# mm, nozzle tip at origin, Z up, latch side +Y, fin channels open along X (hotend fan blows -X).
# Every number below was read from a planar section of the STL (stl_section.py).
# shortcut: the STL is a display replica with no filament bore, so none is modelled; add one if needed.

# Heatsink side profile (Y, Z), constant along X, extruded X = +/-8.75.
HS_PROFILE = [(-10.50, 45.03), (-10.50, 46.03), (10.50, 46.03), (10.50, 45.03), (2.25, 45.03), (2.25, 44.03),
              (9.00, 44.03), (9.00, 43.03), (2.25, 43.03), (2.25, 42.00), (9.00, 42.00), (9.00, 41.00),
              (2.25, 41.00), (2.25, 40.00), (7.00, 40.00), (7.00, 37.00), (6.00, 37.00), (6.00, 39.00),
              (2.25, 39.00), (2.25, 38.00), (5.00, 38.00), (5.00, 37.00), (2.25, 37.00), (2.25, 36.44),
              (4.00, 35.50), (9.00, 35.50), (9.00, 30.50), (8.00, 30.50), (8.00, 34.41), (7.00, 34.41),
              (7.00, 31.50), (6.00, 31.50), (6.00, 34.41), (5.00, 34.41), (5.00, 32.50), (4.00, 32.50),
              (4.00, 34.41), (3.70, 34.41), (2.70, 35.00), (-2.00, 35.00), (-3.00, 34.41), (-5.50, 34.41),
              (-5.50, 32.50), (-6.50, 32.50), (-6.50, 34.41), (-7.50, 34.41), (-7.50, 31.50), (-8.50, 31.50),
              (-8.50, 34.41), (-9.50, 34.41), (-9.50, 30.50), (-10.50, 30.50), (-10.50, 35.50), (-3.80, 35.50),
              (-2.25, 36.30), (-2.25, 37.00), (-10.50, 37.00), (-10.50, 38.00), (-2.25, 38.00), (-2.25, 39.00),
              (-10.50, 39.00), (-10.50, 40.00), (-2.25, 40.00), (-2.25, 41.00), (-10.50, 41.00), (-10.50, 42.00),
              (-2.25, 42.00), (-2.25, 43.03), (-10.50, 43.03), (-10.50, 44.03), (-2.25, 44.03), (-2.25, 45.03)]
HS_HALF_X = 8.75
HS_TOP, BOSS_TOP, BOSS_R, BOSS_HOLE_R = 46.03, 49.03, 2.40, 0.95
SOCKET_R, SOCKET_Z0, SOCKET_Z1 = 1.47, 35.0, 39.0
PIN_HOLE_R, PIN_Z, PIN_Y0, PIN_Y1 = 1.0, 38.5, 6.0, 7.0      # hole in the latch web for the magnet bump

# Hot end: D-section body = Ø5 core + 10 mm wide wings (Y 1..3), R4.516 fillets tangent to the core.
CORE_R, WING_X, WING_Y0, WING_Y1 = 2.5, 5.0, 1.0, 3.0
FIL_C, FIL_R = (6.138, -3.370), 4.516
BODY_Z0, BODY_Z1 = 3.5, 27.0
TAB = [(3.0, 25.4), (4.0, 25.4), (5.0, 26.4), (5.0, 26.5), (4.5, 27.0), (3.0, 27.0)]   # (Y, Z), full width
TIP = [(0.19, 0.0), (0.46, 0.0), (1.46, 1.5), (1.46, 4.0), (0.0, 4.0), (0.0, 1.0), (0.19, 1.0)]  # Ø0.38 orifice
NECK = [(0.0, 26.5), (CORE_R, 26.5), (CORE_R, 33.0), (1.46, 33.0), (1.46, 39.0), (0.0, 39.0)]

# Latch ("magnet") plate.
LATCH = dict(x=8.75, y0=7.0, y1=9.0, z0=35.5, z1=41.0, corner_r=0.8, bump_r=0.95)

STL_VOL = {"HotEnd": 1082.0, "ColdEnd_Heatsink": 2755.4, "Latch_Magnet": 191.9}   # mm3, faceted solids

app = adsk.core.Application.get()
V = adsk.core.ValueInput.createByReal
P = lambda x, y, z=0: adsk.core.Point3D.create(x / 10, y / 10, z / 10)
OP = adsk.fusion.FeatureOperations


def plane(comp, base, off):
    pi = comp.constructionPlanes.createInput()
    pi.setByOffset(base, V(off / 10))
    return comp.constructionPlanes.add(pi)


def poly(sk, pts):
    pts = [sk.modelToSketchSpace(p) for p in pts]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        sk.sketchCurves.sketchLines.addByTwoPoints(a, b)


def biggest(sk):
    return max((sk.profiles.item(i) for i in range(sk.profiles.count)), key=lambda p: p.areaProperties().area)


def sym_extrude(comp, prof, total, op, bodies=None):
    inp = comp.features.extrudeFeatures.createInput(prof, op)
    inp.setSymmetricExtent(V(total / 10), True)
    if bodies:
        inp.participantBodies = bodies
    return comp.features.extrudeFeatures.add(inp).bodies


def revolve(comp, rz, op, bodies=None):
    sk = comp.sketches.add(comp.xZConstructionPlane)
    poly(sk, [P(r, 0, z) for r, z in rz])
    inp = comp.features.revolveFeatures.createInput(sk.profiles.item(0), comp.zConstructionAxis, op)
    inp.setAngleExtent(False, V(2 * math.pi))
    if bodies:
        inp.participantBodies = bodies
    return comp.features.revolveFeatures.add(inp).bodies


def new_comp(root, name):
    c = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    c.name = name
    return c


def build_cold_end(comp):
    sk = comp.sketches.add(comp.yZConstructionPlane)
    poly(sk, [P(0, y, z) for y, z in HS_PROFILE])
    body = sym_extrude(comp, biggest(sk), 2 * HS_HALF_X, OP.NewBodyFeatureOperation).item(0)
    revolve(comp, [(0, HS_TOP), (BOSS_R, HS_TOP), (BOSS_R, BOSS_TOP), (0, BOSS_TOP)], OP.JoinFeatureOperation, [body])
    revolve(comp, [(0, HS_TOP), (BOSS_HOLE_R, HS_TOP), (BOSS_HOLE_R, BOSS_TOP), (0, BOSS_TOP)], OP.CutFeatureOperation, [body])
    revolve(comp, [(0, SOCKET_Z0 - 0.1), (SOCKET_R, SOCKET_Z0 - 0.1), (SOCKET_R, SOCKET_Z1), (0, SOCKET_Z1)],
            OP.CutFeatureOperation, [body])
    body.name = "ColdEnd_Heatsink"
    return body


def build_pin_hole(comp, body):
    # Plane through the web centre (Y = 6.5); offset sign of the XZ plane is resolved by checking the result.
    for off in (0.5 * (PIN_Y0 + PIN_Y1), -0.5 * (PIN_Y0 + PIN_Y1)):
        pl = plane(comp, comp.xZConstructionPlane, off)
        sk = comp.sketches.add(pl)
        c = sk.modelToSketchSpace(P(0, 0.5 * (PIN_Y0 + PIN_Y1), PIN_Z))
        if abs(c.z) < 1e-6:          # sketch plane really is at Y = 6.5
            sk.sketchCurves.sketchCircles.addByCenterRadius(c, PIN_HOLE_R / 10)
            sym_extrude(comp, sk.profiles.item(0), PIN_Y1 - PIN_Y0, OP.CutFeatureOperation, [body])
            return
        sk.deleteMe(); pl.deleteMe()
    raise RuntimeError("could not place the latch pin hole plane")


def build_hot_end(comp):
    sk = comp.sketches.add(plane(comp, comp.xYConstructionPlane, BODY_Z0))
    s = lambda x, y: sk.modelToSketchSpace(P(x, y, BODY_Z0))
    d = math.hypot(*FIL_C)
    t = (FIL_C[0] * CORE_R / d, FIL_C[1] * CORE_R / d)                    # fillet/core tangent point (+X side)
    a0 = math.atan2(WING_Y0 - FIL_C[1], WING_X - FIL_C[0])
    a1 = math.atan2(t[1] - FIL_C[1], t[0] - FIL_C[0])
    am = 0.5 * (a0 + a1)
    fm = (FIL_C[0] + FIL_R * math.cos(am), FIL_C[1] + FIL_R * math.sin(am))
    L, A = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
    L.addByTwoPoints(s(WING_X, WING_Y1), s(-WING_X, WING_Y1))
    L.addByTwoPoints(s(-WING_X, WING_Y1), s(-WING_X, WING_Y0))
    A.addByThreePoints(s(-WING_X, WING_Y0), s(-fm[0], fm[1]), s(-t[0], t[1]))
    A.addByThreePoints(s(-t[0], t[1]), s(0, -CORE_R), s(t[0], t[1]))
    A.addByThreePoints(s(t[0], t[1]), s(fm[0], fm[1]), s(WING_X, WING_Y0))
    L.addByTwoPoints(s(WING_X, WING_Y0), s(WING_X, WING_Y1))
    inp = comp.features.extrudeFeatures.createInput(sk.profiles.item(0), OP.NewBodyFeatureOperation)
    inp.setDistanceExtent(False, V((BODY_Z1 - BODY_Z0) / 10))
    body = comp.features.extrudeFeatures.add(inp).bodies.item(0)
    if body.boundingBox.maxPoint.z * 10 < BODY_Z1 - 0.01:                 # extruded the wrong way
        raise RuntimeError("body extrude direction")
    # 45° chamfers at the bottom of the wings (z = 3.5 + (|x| - 2.5)).
    sk = comp.sketches.add(comp.xZConstructionPlane)
    for sgn in (1, -1):
        poly(sk, [P(sgn * CORE_R, 0, BODY_Z0), P(sgn * 7.0, 0, BODY_Z0), P(sgn * 7.0, 0, BODY_Z0 + 7.0 - CORE_R)])
    for i in range(sk.profiles.count):
        sym_extrude(comp, sk.profiles.item(i), 20, OP.CutFeatureOperation, [body])
    sk = comp.sketches.add(comp.yZConstructionPlane)
    poly(sk, [P(0, y, z) for y, z in TAB])
    sym_extrude(comp, sk.profiles.item(0), 2 * WING_X, OP.JoinFeatureOperation, [body])
    revolve(comp, TIP, OP.JoinFeatureOperation, [body])
    revolve(comp, NECK, OP.JoinFeatureOperation, [body])
    body.name = "HotEnd"
    return body


def build_latch(comp):
    k = LATCH
    yc = 0.5 * (k["y0"] + k["y1"])
    for off in (yc, -yc):
        pl = plane(comp, comp.xZConstructionPlane, off)
        sk = comp.sketches.add(pl)
        if abs(sk.modelToSketchSpace(P(0, yc, 0)).z) < 1e-6:
            break
        sk.deleteMe(); pl.deleteMe()
    s = lambda x, z: sk.modelToSketchSpace(P(x, yc, z))
    sk.sketchCurves.sketchLines.addTwoPointRectangle(s(-k["x"], k["z0"]), s(k["x"], k["z1"]))
    body = sym_extrude(comp, sk.profiles.item(0), k["y1"] - k["y0"], OP.NewBodyFeatureOperation).item(0)
    edges = adsk.core.ObjectCollection.create()
    for e in body.edges:                     # the 4 corner edges run along Y
        a, b = e.startVertex.geometry, e.endVertex.geometry
        if abs(a.x - b.x) < 1e-6 and abs(a.z - b.z) < 1e-6:
            edges.add(e)
    fi = comp.features.filletFeatures.createInput()
    fi.addConstantRadiusEdgeSet(edges, V(k["corner_r"] / 10), True)
    comp.features.filletFeatures.add(fi)
    # Bump that sits in the heatsink web hole (Y 6..7).
    for off in (0.5 * (PIN_Y0 + PIN_Y1), -0.5 * (PIN_Y0 + PIN_Y1)):
        pl = plane(comp, comp.xZConstructionPlane, off)
        sk = comp.sketches.add(pl)
        c = sk.modelToSketchSpace(P(0, 0.5 * (PIN_Y0 + PIN_Y1), PIN_Z))
        if abs(c.z) < 1e-6:
            sk.sketchCurves.sketchCircles.addByCenterRadius(c, k["bump_r"] / 10)
            sym_extrude(comp, sk.profiles.item(0), PIN_Y1 - PIN_Y0, OP.JoinFeatureOperation, [body])
            break
        sk.deleteMe(); pl.deleteMe()
    body.name = "Latch_Magnet"
    return body


def run(_context: str):
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = "Bambu X2D hotend (clean, from STL)"
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent
    lib = app.materialLibraries.itemByName("Fusion Material Library")

    hot_c, cold_c, latch_c = new_comp(root, "HotEnd"), new_comp(root, "ColdEnd_Heatsink"), new_comp(root, "Latch")
    hot = build_hot_end(hot_c)
    cold = build_cold_end(cold_c)
    build_pin_hole(cold_c, cold)
    latch = build_latch(latch_c)

    for b, mat in ((hot, "Stainless Steel"), (cold, "Aluminum 6061"), (latch, "Steel")):
        m = lib.materials.itemByName(mat)
        if m:
            b.material = m
        bb = b.boundingBox
        vol = b.volume * 1000
        print("%-17s faces %3d  vol %7.1f mm3 (STL %7.1f, %+.1f%%)  bbox %s" % (
            b.name, b.faces.count, vol, STL_VOL[b.name], 100 * (vol / STL_VOL[b.name] - 1),
            [round(v * 10, 2) for v in (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z,
                                        bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)]))
        assert abs(vol / STL_VOL[b.name] - 1) < 0.03, b.name   # clean model must match the mesh within 3 %
    app.activeViewport.fit()
