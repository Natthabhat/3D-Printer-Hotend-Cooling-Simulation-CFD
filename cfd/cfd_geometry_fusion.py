import adsk.core, adsk.fusion

# CFD domain for the stock X2D hotend + 2510 fan + duct (run inside Fusion via the MCP script tool).
# Reuses the builders in x2d_hotend_fan_assembly.py (which reuses x2d_hotend_clean.py), then:
#  - splits the hot end at z = 27 mm: NozzleBody (held at 220 °C, stands in for the heater) / HeatBreak
#  - Air_fan: air annulus in the fan bore (Ø24 opening minus Ø13 hub); its face toward the duct = fan face
#  - Air_main: air box minus every part; fan frame, hub, duct and latch become voids (adiabatic walls)
# Exports STEP with 5 bodies: NozzleBody, HeatBreak, Heatsink, Air_fan, Air_main.
ASM = r"C:\Users\natth\Documents\Asys Com aid\Ansys Project\x2d_hotend_fan_assembly.py"
STEP = r"C:\Users\natth\Documents\Asys Com aid\Ansys Project\cfd\hotend_cfd_domain.step"

a = {}
exec(open(ASM, encoding="utf-8").read(), a)
cl = a["cl"]
cl["SOCKET_R"] = 1.46   # = stub radius: the STL's 0.01 mm clearance would leave an unmeshable air sliver
a["FAN_BORE_R"] = 11.5  # Ø23: a Ø24 opening is wider than the duct inlet inside (23.4) and leaves slivers
cl["TIP"] =[(0.0, 0.0), (0.46, 0.0), (1.46, 1.5), (1.46, 4.0), (0.0, 4.0)]   # no Ø0.38 orifice: too small to mesh
app, V, P, OP, plane = cl["app"], cl["V"], cl["P"], cl["OP"], cl["plane"]

SPLIT_Z = 27.0                                   # top of the nozzle body (heater contact zone ends here)
BOX = (-30.0, 60.0, -30.0, 30.0, -10.0, 80.0)    # air enclosure x0,x1,y0,y1,z0,z1 (mm)


def run(_context: str):
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = "Hotend CFD domain"
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent
    nc = cl["new_comp"]

    hot_c, cold_c, latch_c = nc(root, "HotEnd"), nc(root, "Heatsink"), nc(root, "Latch")
    fan_c, duct_c = nc(root, "Fan"), nc(root, "Duct")
    hot = cl["build_hot_end"](hot_c)
    cold = cl["build_cold_end"](cold_c)
    # no latch-pin hole: with the bump in it the air left is a 0.05 mm sliver that breaks share topology
    cl["build_latch"](latch_c)
    a["build_fan"](fan_c)
    a["build_duct"](duct_c)
    cold.name = "Heatsink"

    # split the hot end into the heated nozzle body and the heat break
    si = hot_c.features.splitBodyFeatures.createInput(hot, plane(hot_c, hot_c.xYConstructionPlane, SPLIT_Z), True)
    hot_c.features.splitBodyFeatures.add(si)
    hb = max((hot_c.bRepBodies.item(i) for i in range(hot_c.bRepBodies.count)), key=lambda b: b.boundingBox.minPoint.z)
    # split again at the socket rim (z = 35) so the stub's cylinder matches the socket face edge-to-edge
    si = hot_c.features.splitBodyFeatures.createInput(hb, plane(hot_c, hot_c.xYConstructionPlane, cl["SOCKET_Z0"]), True)
    hot_c.features.splitBodyFeatures.add(si)
    parts = sorted((hot_c.bRepBodies.item(i) for i in range(hot_c.bRepBodies.count)), key=lambda b: b.boundingBox.minPoint.z)
    assert len(parts) == 3, "split gave %d bodies" % len(parts)
    parts[0].name, parts[1].name, parts[2].name = "NozzleBody", "HeatBreak", "HeatBreakStub"

    # fan air annulus (same circles as the fan frame/hub sketch)
    fz = nc(root, "FanAir")
    sk = fz.sketches.add(plane(fz, fz.yZConstructionPlane, a["FAN_X0"]))
    c = lambda y, z: sk.modelToSketchSpace(P(a["FAN_X0"], y, z))
    sk.sketchCurves.sketchCircles.addByCenterRadius(c(0, a["FAN_ZC"]), a["FAN_BORE_R"] / 10)
    sk.sketchCurves.sketchCircles.addByCenterRadius(c(0, a["FAN_ZC"]), 0.65)
    ring = max((sk.profiles.item(i) for i in range(sk.profiles.count)), key=lambda p: p.profileLoops.count)
    air_fan = fz.features.extrudeFeatures.addSimple(ring, V(a["FAN_T"] / 10), OP.NewBodyFeatureOperation).bodies.item(0)
    air_fan.name = "Air_fan"
    assert abs(air_fan.boundingBox.minPoint.x * 10 - a["FAN_X0"]) < 0.01, "fan air extruded the wrong way"

    # air box minus everything (tools kept), built in its own component
    ac = nc(root, "AirMain")
    x0, x1, y0, y1, z0, z1 = BOX
    air = cl["box"](ac, x0, x1, y0, y1, z0, z1, OP.NewBodyFeatureOperation).item(0) if "box" in cl else None
    if air is None:
        sk = ac.sketches.add(plane(ac, ac.xYConstructionPlane, z0))
        sk.sketchCurves.sketchLines.addTwoPointRectangle(P(x0, y0), P(x1, y1))
        ei = ac.features.extrudeFeatures.createInput(sk.profiles.item(0), OP.NewBodyFeatureOperation)
        ei.setDistanceExtent(False, V((z1 - z0) / 10))
        air = ac.features.extrudeFeatures.add(ei).bodies.item(0)
    air.name = "Air_main"
    occ_of = {o.component.name: o for o in root.occurrences}
    tools = adsk.core.ObjectCollection.create()
    for occ in root.occurrences:
        if occ.component.name in ("AirMain", "Latch"):   # latch slot stays air: avoids 0.2 mm slivers
            continue
        for i in range(occ.bRepBodies.count):
            tools.add(occ.bRepBodies.item(i))            # body proxies in assembly context
    air_proxy = occ_of["AirMain"].bRepBodies.item(0)
    ci = root.features.combineFeatures.createInput(air_proxy, tools)
    ci.operation = OP.CutFeatureOperation
    ci.isKeepToolBodies = True
    root.features.combineFeatures.add(ci)

    # drop the latch (its slot stays air). Fan frame/hub and duct stay as solids: as empty voids the duct
    # cavity touched the heatsink and Fluent's region detection swapped them (heatsink became a void).
    for name in ("Latch",):
        comp = occ_of[name].component
        for i in range(comp.bRepBodies.count - 1, -1, -1):
            comp.features.removeFeatures.add(comp.bRepBodies.item(i))

    keep = []
    for occ in root.occurrences:
        for i in range(occ.bRepBodies.count):
            b = occ.bRepBodies.item(i)
            bb = b.boundingBox
            keep.append(b.name)
            print("%-11s solid=%s lumps=%d faces=%4d vol=%10.1f mm3 bbox=%s" % (
                b.name, b.isSolid, b.lumps.count, b.faces.count, b.volume * 1000,
                [round(v * 10, 2) for v in (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z,
                                            bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)]))
    assert sorted(keep) == sorted(["NozzleBody", "HeatBreak", "HeatBreakStub", "Heatsink", "FanFrame", "FanHub", "Duct",
                                   "Air_fan", "Air_main"]), keep
    em = design.exportManager
    print("STEP:", em.execute(em.createSTEPExportOptions(STEP, root)), STEP)
    app.activeViewport.fit()
