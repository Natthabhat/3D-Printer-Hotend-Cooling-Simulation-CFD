import adsk.core, adsk.fusion, os

# Clean renders of the stock hotend + fan + duct assembly for the labelled diagram (run inside Fusion via MCP).
ASM = r"C:\Users\natth\Documents\Asys Com aid\Ansys Project\x2d_hotend_fan_assembly.py"
OUT = r"C:\Users\natth\Documents\Asys Com aid\Ansys Project\diagram"
a = {}
exec(open(ASM, encoding="utf-8").read(), a)


def shot(vp, view, name, size=1600):
    cam = vp.camera
    cam.viewOrientation = view
    cam.isFitView = True
    vp.camera = cam
    vp.refresh()
    opts = adsk.core.SaveImageFileOptions.create(os.path.join(OUT, name))
    opts.width = opts.height = size
    opts.isBackgroundTransparent = True
    opts.isAntiAliased = True
    print(name, vp.saveAsImageFileWithOptions(opts))


def run(_context: str):
    a["run"](_context)                                   # builds "Bambu X2D hotend + fan assembly"
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    for c in [root] + [o.component for o in root.occurrences]:
        c.isSketchFolderLightBulbOn = False
        c.isConstructionFolderLightBulbOn = False
    occ = {o.component.name: o for o in root.occurrences}
    vp = app.activeViewport
    vp.visualStyle = adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
    VO = adsk.core.ViewOrientations
    shot(vp, VO.FrontViewOrientation, "view_front.png")
    for n in ("HotendDuct", "HotendFan_2510"):
        occ[n].isLightBulbOn = False
    shot(vp, VO.RightViewOrientation, "view_side_hotend.png")
    shot(vp, VO.IsoTopLeftViewOrientation, "view_iso_hotend.png")
    for n in ("HotendDuct", "HotendFan_2510"):
        occ[n].isLightBulbOn = True
    for b in occ["HotendDuct"].component.bRepBodies:
        b.opacity = 0.35
    shot(vp, VO.IsoTopRightViewOrientation, "view_iso_assembly.png")
