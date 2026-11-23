import adsk.core, adsk.fusion

# Assembly: clean X2D hotend (built by x2d_hotend_clean.py) + 2510 hotend fan + duct (layout from v2).
# mm, nozzle tip at origin, Z up, latch side +Y, fan on +X blowing -X through the fin channels.
# Fan spec (FAF021): 5 V, 15500 rpm, 2.96 CFM (5.03 m3/h); position measured from 009.png.
# shortcut: fan Z/Y position and duct wall are photo estimates; replace with caliper values.
CLEAN = r"C:\Users\natth\Documents\Asys Com aid\Ansys Project\x2d_hotend_clean.py"
OUT = r"C:\Users\natth\AppData\Local\Temp\claude\5b299854331cdbb0\4e4d068d-c5a2-4680-8b88-553b1334336a\scratchpad"

cl = {}
exec(open(CLEAN, encoding="utf-8").read(), cl)       # clean hotend builders + helpers, one source of truth
app, V, P, OP, plane, poly = cl["app"], cl["V"], cl["P"], cl["OP"], cl["plane"], cl["poly"]

HS_X = cl["HS_HALF_X"]                               # heatsink side face the duct mates to (+X)
HS_Y = 10.5                                          # heatsink half-depth (Y)
HS_Z0, HS_Z1 = 30.5, cl["HS_TOP"]                    # finger bottom .. top plate
FAN, FAN_T = 25.0, 10.0                              # 2510 fan
FAN_BORE_R = 12.0                                    # Ø24 rotor opening (CFD uses 11.5 to stay inside the duct)
FAN_ZC = HS_Z1 - 9.9                                 # fan centre 9.9 mm below heatsink top (009.png)
DUCT_L, DUCT_WALL = 10.5, 0.8
FAN_X0 = HS_X + DUCT_L                               # fan face toward the duct


def build_fan(comp):
    sk = comp.sketches.add(plane(comp, comp.yZConstructionPlane, FAN_X0))
    c = lambda y, z: sk.modelToSketchSpace(P(FAN_X0, y, z))
    sk.sketchCurves.sketchLines.addTwoPointRectangle(c(-FAN / 2, FAN_ZC - FAN / 2), c(FAN / 2, FAN_ZC + FAN / 2))
    circ = sk.sketchCurves.sketchCircles
    circ.addByCenterRadius(c(0, FAN_ZC), FAN_BORE_R / 10)   # rotor opening
    circ.addByCenterRadius(c(0, FAN_ZC), 0.65)       # Ø13 hub
    for y in (-10, 10):                              # two bottom mounting holes, 20 mm pitch
        circ.addByCenterRadius(c(y, FAN_ZC - 10), 0.12)
    profs = [sk.profiles.item(i) for i in range(sk.profiles.count)]
    frame = max(profs, key=lambda p: p.profileLoops.count)
    hub = min(profs, key=lambda p: abs(p.areaProperties().area - 3.14159265 * 0.65 ** 2))
    out = []
    for prof, name in ((frame, "FanFrame"), (hub, "FanHub")):
        b = comp.features.extrudeFeatures.addSimple(prof, V(FAN_T / 10), OP.NewBodyFeatureOperation).bodies.item(0)
        b.name = name
        out.append(b)
    assert abs(out[0].boundingBox.minPoint.x * 10 - FAN_X0) < 0.01, "fan extruded the wrong way"
    return out


def build_duct(comp):
    secs = []
    for x, (y0, y1, z0, z1) in ((FAN_X0, (-FAN / 2, FAN / 2, FAN_ZC - FAN / 2, FAN_ZC + FAN / 2)),
                                (HS_X, (-HS_Y, HS_Y, HS_Z0, HS_Z1))):
        sk = comp.sketches.add(plane(comp, comp.yZConstructionPlane, x))
        poly(sk, [P(x, y0, z0), P(x, y1, z0), P(x, y1, z1), P(x, y0, z1)])
        secs.append(sk.profiles.item(0))
    li = comp.features.loftFeatures.createInput(OP.NewBodyFeatureOperation)
    for s in secs:
        li.loftSections.add(s)
    loft = comp.features.loftFeatures.add(li)
    faces = adsk.core.ObjectCollection.create()
    faces.add(loft.startFace); faces.add(loft.endFace)
    si = comp.features.shellFeatures.createInput(faces, False)
    si.insideThickness = V(DUCT_WALL / 10)
    comp.features.shellFeatures.add(si)
    b = comp.bRepBodies.item(0)
    b.name = "Duct"
    return b


def run(_context: str):
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = "Bambu X2D hotend + fan assembly"
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent
    lib = app.materialLibraries.itemByName("Fusion Material Library")

    nc = cl["new_comp"]
    hot_c, cold_c, latch_c = nc(root, "HotEnd"), nc(root, "ColdEnd_Heatsink"), nc(root, "Latch")
    fan_c, duct_c = nc(root, "HotendFan_2510"), nc(root, "HotendDuct")
    hot = cl["build_hot_end"](hot_c)
    cold = cl["build_cold_end"](cold_c)
    cl["build_pin_hole"](cold_c, cold)
    latch = cl["build_latch"](latch_c)
    frame, hub = build_fan(fan_c)
    duct = build_duct(duct_c)

    mats = ((hot, "Stainless Steel"), (cold, "Aluminum 6061"), (latch, "Steel"),
            (frame, "ABS Plastic"), (hub, "ABS Plastic"), (duct, "ABS Plastic"))
    allb = adsk.core.ObjectCollection.create()
    for b, mat in mats:
        m = lib.materials.itemByName(mat)
        if m:
            b.material = m
        allb.add(b)
        bb = b.boundingBox
        print("%-17s %-15s vol %7.1f mm3 bbox %s" % (b.name, mat if m else "NO MATERIAL", b.volume * 1000,
              [round(v * 10, 2) for v in (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z,
                                          bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)]))
    res = design.analyzeInterference(design.createInterferenceInput(allb))
    print("interferences:", res.count)
    for i in range(res.count):
        r = res.item(i)
        print(" ", r.entityOne.name, "x", r.entityTwo.name, round(r.interferenceBody.volume * 1000, 4), "mm3")
    assert res.count == 0, "parts overlap"

    vp = app.activeViewport
    VO = adsk.core.ViewOrientations
    for name, view in (("asm_iso", VO.IsoTopRightViewOrientation), ("asm_front", VO.FrontViewOrientation),
                       ("asm_right", VO.RightViewOrientation)):
        cam = vp.camera
        cam.viewOrientation = view
        cam.isFitView = True
        vp.camera = cam
        vp.refresh()
        vp.saveAsImageFile(OUT + "\\" + name + ".png", 800, 800)
