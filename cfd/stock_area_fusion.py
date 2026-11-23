import adsk.core, adsk.fusion

# Surface area / volume of the stock heatsink as used in the CFD (socket closed, no pin hole), for comparison.
ASM = r"C:\Users\natth\Documents\Asys Com aid\Ansys Project\x2d_hotend_fan_assembly.py"
a = {}
exec(open(ASM, encoding="utf-8").read(), a)
cl = a["cl"]
cl["SOCKET_R"] = 1.46


def run(_context: str):
    app = cl["app"]
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    comp = cl["new_comp"](design.rootComponent, "Heatsink")
    b = cl["build_cold_end"](comp)
    print("stock heatsink: area %.0f mm2, vol %.0f mm3" % (b.area * 100, b.volume * 1000))
    doc.close(False)
