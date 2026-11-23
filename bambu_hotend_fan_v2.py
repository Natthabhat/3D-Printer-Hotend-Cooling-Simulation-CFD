import adsk.core, adsk.fusion, math

# Bambu H2/P2S/X2D hotend + P2S hotend fan (FAF021) + duct, stock geometry (no improvement).
# mm, z = 0 at nozzle tip, Z up. X = printer left/right (fan on +X, air flows -X through the fins),
# Y = front/back (label face at -Y).
# Sources: Bambu wiki front photo (hotend_bundles.jpg, 0.069 mm/px), side photo FAH043-1.jpg
# (0.039 mm/px), both scaled to the published 49.2 mm length; fan/duct from 009.png scaled by the
# 17.7 mm heatsink width. Fan spec: 5 V, 15500 rpm, 2.96 CFM (5.03 m3/h).
# shortcut: nozzle wing thickness, internal bores, heat-break OD inside the heatsink, duct wall and
# fan Y/Z position are estimates; replace with caliper values.

HS_X = 8.85                         # heatsink half-width in X (17.7 mm)
HS_TOP, BASE_Z0 = 46.1, 34.2        # top of top plate, bottom of base plate
SPINE_Y = 2.45                      # central wall half-thickness (4.9 mm)
PLATES = [(44.9, 46.1, 10.6), (43.0, 43.9, 9.3), (41.2, 42.0, 9.3),
          (39.2, 39.9, 9.3), (37.1, 37.8, 9.3), (BASE_Z0, 35.5, 9.3)]   # z0, z1, +Y reach
PLATE_YMIN = -10.8
FINGER_X, FINGER_Z0 = 8.5, 30.3
FINGERS_Y = [(-10.8, -9.6), (-8.7, -7.7), (-6.8, -5.9), (4.4, 5.2), (6.2, 7.0), (8.0, 9.3)]
BOSS_R, TOTAL = 2.4, 49.2
NECK_R, HB_IN_R, BORE_R = 2.45, 1.8, 1.0
NOZ_TOP, CORE_R, WING_X, WING_T = 26.7, 2.75, 4.9, 3.0

FAN, FAN_T, FAN_ZC = 25.0, 10.0, 36.2
DUCT_L, DUCT_WALL = 10.5, 0.8
FAN_X0 = HS_X + DUCT_L              # fan face toward the duct

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


def revolve(comp, rz, op, bodies=None):
    sk = comp.sketches.add(comp.xZConstructionPlane)
    poly(sk, [P(r, 0, z) for r, z in rz])
    inp = comp.features.revolveFeatures.createInput(sk.profiles.item(0), comp.zConstructionAxis, op)
    inp.setAngleExtent(False, V(2 * math.pi))
    if bodies: inp.participantBodies = bodies
    return comp.features.revolveFeatures.add(inp).bodies


def box(comp, x0, x1, y0, y1, z0, z1, op, bodies=None):
    sk = comp.sketches.add(plane(comp, comp.xYConstructionPlane, z0))
    sk.sketchCurves.sketchLines.addTwoPointRectangle(P(x0, y0), P(x1, y1))
    inp = comp.features.extrudeFeatures.createInput(sk.profiles.item(0), op)
    inp.setDistanceExtent(False, V((z1 - z0) / 10))
    if bodies: inp.participantBodies = bodies
    return comp.features.extrudeFeatures.add(inp).bodies


def new_comp(root, name):
    c = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    c.name = name
    return c


def material(body, *names):
    lib = app.materialLibraries.itemByName("Fusion Material Library")
    for n in names:
        m = lib.materials.itemByName(n)
        if m:
            body.material = m
            return n
    return "NOT FOUND"


def run(_context: str):
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = "Bambu P2S hotend + fan (stock v2)"
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent
    hot = new_comp(root, "Hotend")

    # Nozzle: round core + two flat wings (9.8 x 5.5 mm section), chamfered bottom, collar + cone tip.
    noz = revolve(hot, [(0, 0), (0.6, 0), (1.5, 1.6), (1.5, 3.5), (2.4, 3.5), (CORE_R, 4.0),
                        (CORE_R, NOZ_TOP), (0, NOZ_TOP)], OP.NewBodyFeatureOperation).item(0)
    sk = hot.sketches.add(hot.xZConstructionPlane)
    poly(sk, [P(-WING_X, 0, NOZ_TOP), P(WING_X, 0, NOZ_TOP), P(WING_X, 0, 6.0),
              P(2.4, 0, 3.5), P(-2.4, 0, 3.5), P(-WING_X, 0, 6.0)])
    inp = hot.features.extrudeFeatures.createInput(sk.profiles.item(0), OP.JoinFeatureOperation)
    inp.setSymmetricExtent(V(WING_T / 10), True)
    inp.participantBodies = [noz]
    hot.features.extrudeFeatures.add(inp)
    revolve(hot, [(0, 0), (0.2, 0), (0.2, 1.0), (BORE_R, 2.0), (BORE_R, NOZ_TOP), (0, NOZ_TOP)],
            OP.CutFeatureOperation, [noz])
    noz.name = "Nozzle"

    # Heat break: Ø4.9 exposed neck, thinner tube inside the heatsink wall.
    hb = revolve(hot, [(BORE_R, NOZ_TOP), (NECK_R, NOZ_TOP), (NECK_R, BASE_Z0), (HB_IN_R, BASE_Z0),
                       (HB_IN_R, HS_TOP), (BORE_R, HS_TOP)], OP.NewBodyFeatureOperation).item(0)
    hb.name = "HeatBreak"

    # Heatsink: central wall, 5 plates + base plate (channels open along X), 6 hanging fingers, top boss.
    hs = box(hot, -HS_X, HS_X, -SPINE_Y, SPINE_Y, BASE_Z0, HS_TOP, OP.NewBodyFeatureOperation).item(0)
    for z0, z1, ymax in PLATES:
        box(hot, -HS_X, HS_X, PLATE_YMIN, ymax, z0, z1, OP.JoinFeatureOperation, [hs])
    for y0, y1 in FINGERS_Y:
        box(hot, -FINGER_X, FINGER_X, y0, y1, FINGER_Z0, BASE_Z0, OP.JoinFeatureOperation, [hs])
    revolve(hot, [(0, HS_TOP), (BOSS_R, HS_TOP), (BOSS_R, TOTAL), (0, TOTAL)], OP.JoinFeatureOperation, [hs])
    revolve(hot, [(0, BASE_Z0), (HB_IN_R, BASE_Z0), (HB_IN_R, HS_TOP), (BORE_R, HS_TOP),
                  (BORE_R, TOTAL), (0, TOTAL)], OP.CutFeatureOperation, [hs])
    hs.name = "Heatsink"

    # Fan 2510: frame with Ø24 bore, Ø13 hub, two bottom mounting holes; axis along X, blows -X.
    fan = new_comp(root, "HotendFan_2510")
    sk = fan.sketches.add(plane(fan, fan.yZConstructionPlane, FAN_X0))
    c = lambda y, z: sk.modelToSketchSpace(P(FAN_X0, y, z))
    sk.sketchCurves.sketchLines.addTwoPointRectangle(c(-FAN / 2, FAN_ZC - FAN / 2), c(FAN / 2, FAN_ZC + FAN / 2))
    circ = sk.sketchCurves.sketchCircles
    circ.addByCenterRadius(c(0, FAN_ZC), 1.2)
    circ.addByCenterRadius(c(0, FAN_ZC), 0.65)
    for y in (-10, 10):
        circ.addByCenterRadius(c(y, FAN_ZC - 10), 0.12)
    profs = [sk.profiles.item(i) for i in range(sk.profiles.count)]
    frame = max(profs, key=lambda p: p.profileLoops.count)
    hub = min(profs, key=lambda p: abs(p.areaProperties().area - math.pi * 0.65 ** 2))
    for prof, name in ((frame, "FanFrame"), (hub, "FanHub")):
        b = fan.features.extrudeFeatures.addSimple(prof, V(FAN_T / 10), OP.NewBodyFeatureOperation).bodies.item(0)
        b.name = name

    # Duct: lofted shell from the 25x25 fan face down to the heatsink side face, open both ends.
    duct = new_comp(root, "HotendDuct")
    secs = []
    for x, (y0, y1, z0, z1) in ((FAN_X0, (-FAN / 2, FAN / 2, FAN_ZC - FAN / 2, FAN_ZC + FAN / 2)),
                                (HS_X, (PLATE_YMIN, 10.6, FINGER_Z0, HS_TOP))):
        sk = duct.sketches.add(plane(duct, duct.yZConstructionPlane, x))
        poly(sk, [P(x, y0, z0), P(x, y1, z0), P(x, y1, z1), P(x, y0, z1)])
        secs.append(sk.profiles.item(0))
    li = duct.features.loftFeatures.createInput(OP.NewBodyFeatureOperation)
    for s in secs:
        li.loftSections.add(s)
    loft = duct.features.loftFeatures.add(li)
    faces = adsk.core.ObjectCollection.create()
    faces.add(loft.startFace); faces.add(loft.endFace)
    si = duct.features.shellFeatures.createInput(faces, False)
    si.insideThickness = V(DUCT_WALL / 10)
    duct.features.shellFeatures.add(si)
    db = duct.bRepBodies.item(0)
    db.name = "Duct"

    for b, mats in ((hs, ("Aluminum 6061",)), (hb, ("Stainless Steel",)), (noz, ("Stainless Steel",)),
                    (fan.bRepBodies.itemByName("FanFrame"), ("ABS Plastic", "Plastic")),
                    (fan.bRepBodies.itemByName("FanHub"), ("ABS Plastic", "Plastic")),
                    (db, ("ABS Plastic", "Plastic"))):
        bb = b.boundingBox
        print(b.name, material(b, *mats), [round(v * 10, 2) for v in (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z,
                                                                     bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)],
              "vol mm3", round(b.volume * 1000, 1))
    assert abs(hs.boundingBox.maxPoint.z * 10 - TOTAL) < 0.01 and abs(noz.boundingBox.minPoint.z) < 1e-6
    app.activeViewport.fit()
