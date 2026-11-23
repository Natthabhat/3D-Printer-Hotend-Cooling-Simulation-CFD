import adsk.core, adsk.fusion, os

# Imports the assembled 1:1 X2D nozzle STLs (made from the 300% print files) into a new Fusion
# document and converts each mesh to a solid body. Nozzle tip at origin, Z up, latch side +Y,
# fin channels open along X (hotend fan blows -X).
DIR = r"C:\Users\natth\Documents\Asys Com aid\Ansys Project\X2D_Nozzle_assembled"
PARTS = (("obj_1_Hot-End.stl", "HotEnd", ("Stainless Steel",)),
         ("obj_3_Cold-End.stl", "ColdEnd_Heatsink", ("Aluminum 6061",)),
         ("obj_2_Magnet.stl", "Latch_Magnet", ("Steel",)))


def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = "X2D nozzle assembled (1-1)"
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent
    lib = app.materialLibraries.itemByName("Fusion Material Library")

    base = root.features.baseFeatures.add()
    base.startEdit()
    meshes = []
    for f, name, _ in PARTS:
        m = root.meshBodies.add(os.path.join(DIR, f), adsk.fusion.MeshUnits.MillimeterMeshUnit, base).item(0)
        m.name = name
        meshes.append(m)
    base.finishEdit()

    mcf = root.features.meshConvertFeatures
    for m, (_, name, mats) in zip(meshes, PARTS):
        T = adsk.fusion.MeshConvertMethodTypes
        try:  # prismatic gives clean planar/cylindrical faces but needs face groups; faceted always works
            inp = mcf.createInput([m])
            inp.meshConvertMethodType = T.PrismaticMeshConvertMethodType
            feat, method = mcf.add(inp), "prismatic"
        except RuntimeError:
            inp = mcf.createInput([m])
            inp.meshConvertMethodType = T.FacetedMeshConvertMethodType
            feat, method = mcf.add(inp), "faceted"
        print(name, "converted:", method)
        b = feat.bodies.item(0)
        b.name = name
        for mn in mats:
            mat = lib.materials.itemByName(mn)
            if mat:
                b.material = mat
                break
        bb = b.boundingBox
        print(name, "solid:", b.isSolid, "faces", b.faces.count, "vol mm3", round(b.volume * 1000, 1),
              "bbox", [round(v * 10, 2) for v in (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z,
                                                   bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)])
    for i in range(root.meshBodies.count):
        root.meshBodies.item(i).isLightBulbOn = False
    app.activeViewport.fit()
