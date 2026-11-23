import adsk.core, adsk.fusion

# Bambu H2/P2S/X2D hotend, stock geometry. All values in mm, z = 0 at nozzle tip, Z up.
# Measured from Bambu's product photo scaled to the published 49.2 mm overall length.
# shortcut: heatsink depth (DEPTH) and internal bore are assumptions, replace with caliper values.
TOTAL = 49.2
HS_W, DEPTH = 17.7, 14.0           # heatsink width (measured), depth (assumed)
HS_Z0, HS_Z1 = 30.42, 46.75        # heatsink bottom/top
LIP_H, LIP_W, LIP_D = 0.86, 16.5, 12.8
BAND_TOP = 36.2                    # solid label band, fins above
N_FIN, FIN_T = 6, 0.9
CORE_R = 4.0                       # solid core around heat break left between fins
HB_R, BORE_R, BOSS_R = 2.4, 1.0, 2.25
NOZ_R, NOZ_TOP = 5.05, 26.99

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent
V = adsk.core.ValueInput.createByReal
P = lambda x, y, z=0: adsk.core.Point3D.create(x / 10, y / 10, z / 10)   # mm -> cm


def new_comp(name):
    # Part Design documents allow one component, so every part is a named body in root.
    return root


def revolve(comp, rz, name):
    """Revolve a closed (r, z) polyline about the Z axis."""
    sk = comp.sketches.add(comp.xZConstructionPlane)
    pts = [sk.modelToSketchSpace(P(r, 0, z)) for r, z in rz]
    lines = sk.sketchCurves.sketchLines
    for a, b in zip(pts, pts[1:] + pts[:1]):
        lines.addByTwoPoints(a, b)
    inp = comp.features.revolveFeatures.createInput(
        sk.profiles.item(0), comp.zConstructionAxis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    inp.setAngleExtent(False, V(6.283185307))
    body = comp.features.revolveFeatures.add(inp).bodies.item(0)
    body.name = name
    return body


def plane(comp, z):
    pi = comp.constructionPlanes.createInput()
    pi.setByOffset(comp.xYConstructionPlane, V(z / 10))
    return comp.constructionPlanes.add(pi)


def ring_profile(comp, z, w, d, r):
    """Sketch a w x d rectangle with a centred circle of radius r at height z; return the outer region."""
    sk = comp.sketches.add(plane(comp, z))
    sk.sketchCurves.sketchLines.addCenterPointRectangle(P(0, 0), P(w / 2, d / 2))
    sk.sketchCurves.sketchCircles.addByCenterRadius(P(0, 0), r / 10)
    return max((sk.profiles.item(i) for i in range(sk.profiles.count)),
               key=lambda p: p.profileLoops.count)


def extrude(comp, prof, h, op, bodies=None):
    inp = comp.features.extrudeFeatures.createInput(prof, op)
    inp.setDistanceExtent(False, V(h / 10))
    if bodies:
        inp.participantBodies = bodies
    return comp.features.extrudeFeatures.add(inp)


def run(_context: str):
    NEW = adsk.fusion.FeatureOperations
    # Nozzle: tip cone, taper, Ø10.1 body that sits in the heater; 2 mm bore down to a 0.4 mm orifice.
    noz = new_comp("Nozzle")
    noz_body = revolve(noz, [(0.2, 0), (0.5, 0), (1.15, 2.82), (NOZ_R, 4.91), (NOZ_R, NOZ_TOP),
                  (BORE_R, NOZ_TOP), (BORE_R, 3.0), (0.2, 2.0)], "Nozzle")

    # Heat break: Ø4.8 tube from nozzle top through the heatsink, Ø4.5 boss on top.
    hb = new_comp("HeatBreak")
    hb_body = revolve(hb, [(BORE_R, NOZ_TOP), (HB_R, NOZ_TOP), (HB_R, HS_Z1), (BOSS_R, HS_Z1),
                 (BOSS_R, TOTAL), (BORE_R, TOTAL)], "HeatBreak")

    # Heatsink: lip + block with Ø4.8 bore, then horizontal fins cut around a solid core.
    hs = new_comp("Heatsink")
    body = extrude(hs, ring_profile(hs, HS_Z0, LIP_W, LIP_D, HB_R), LIP_H, NEW.NewBodyFeatureOperation).bodies.item(0)
    extrude(hs, ring_profile(hs, HS_Z0 + LIP_H, HS_W, DEPTH, HB_R), HS_Z1 - HS_Z0 - LIP_H,
            NEW.JoinFeatureOperation, [body])
    body.name = "Heatsink"
    gap = (HS_Z1 - BAND_TOP - N_FIN * FIN_T) / (N_FIN - 1)
    for j in range(N_FIN - 1):
        z_top = HS_Z1 - (j + 1) * FIN_T - j * gap
        extrude(hs, ring_profile(hs, z_top - gap, HS_W + 2, DEPTH + 2, CORE_R), gap,
                NEW.CutFeatureOperation, [body])

    # Materials (names from the Fusion Material Library; skipped if not found).
    lib = app.materialLibraries.itemByName("Fusion Material Library")
    for b, mat in ((body, "Aluminum 6061"), (hb_body, "Stainless Steel"),
                   (noz_body, "Stainless Steel")):
        m = lib.materials.itemByName(mat) if lib else None
        if m:
            b.material = m
        print(b.name, "material:", m.name if m else "NOT FOUND " + mat)

    app.activeViewport.fit()
    for b in (noz_body, hb_body, body):
        bb = b.boundingBox
        print(b.name, "bbox mm", [round(v * 10, 2) for v in (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z,
                                                              bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)],
              "vol mm3", round(b.volume * 1000, 1), "faces", b.faces.count)
    assert abs(hb_body.boundingBox.maxPoint.z * 10 - TOTAL) < 0.01 and abs(noz_body.boundingBox.minPoint.z) < 1e-6
    assert root.bRepBodies.count == 3, root.bRepBodies.count
