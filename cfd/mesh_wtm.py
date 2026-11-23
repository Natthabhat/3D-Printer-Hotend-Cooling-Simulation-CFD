"""Mesh hotend_cfd_domain.step with the Fluent Watertight Geometry workflow (PyFluent) and write hotend.msh.h5.
Bodies: NozzleBody, HeatBreak, Heatsink (solids); Air_main, Air_fan (fluids). Run from PowerShell."""
import os, sys, time
import ansys.fluent.core as pf

HERE = os.path.dirname(os.path.abspath(__file__))
STEP = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else "hotend_cfd_domain.step")
MESH = os.path.join(HERE, sys.argv[2] if len(sys.argv) > 2 else "hotend.msh.h5")
MAX_CELLS = 1_000_000                        # Fluent Student limit is about 1M cells
# mesh-study presets (sizes in mm); "medium" is the mesh used for all design results
PRESETS = {"coarse": dict(MinSize=0.42, MaxSize=5.0, CellsPerGap=2, HexMax=5.0),   # 0.5 failed: 0.2 mm gap at fan face
           "medium": dict(MinSize=0.35, MaxSize=4.0, CellsPerGap=3, HexMax=4.0),
           "fine": dict(MinSize=0.27, MaxSize=3.1, CellsPerGap=4, HexMax=3.1)}
PS = PRESETS[sys.argv[3] if len(sys.argv) > 3 else "medium"]

t0 = time.time()
m = pf.launch_fluent(mode="meshing", precision="double", processor_count=1, ui_mode="no_gui", cwd=HERE,  # serial: the parallel join crashed
                     start_timeout=300)
wf = m.workflow
wf.InitializeWorkflow(WorkflowType="Watertight Geometry")
T = wf.TaskObject


def run(name, args=None):
    t = T[name]
    if args:
        t.Arguments.set_state(args)
    print(f"[{time.time() - t0:5.0f}s] {name}", flush=True)
    t.Execute()


run("Import Geometry", {"FileName": STEP, "LengthUnit": "mm"})

# no local sizing: global proximity (4 cells per gap) refines the 1 mm fin gaps to ~0.25 mm
run("Generate the Surface Mesh", {"CFDSurfaceMeshControls": {
    # coarse enough for the Student ~1M-cell limit (554k surface faces at 0.2/3.0/4-per-gap was too many)
    "MinSize": PS["MinSize"], "MaxSize": PS["MaxSize"], "GrowthRate": 1.3, "CurvatureNormalAngle": 24,
    "CellsPerGap": PS["CellsPerGap"], "ScopeProximityTo": "faces"}})

T["Describe Geometry"].Arguments.set_state({
    "SetupType": "The geometry consists of both fluid and solid regions and/or voids",
    "WallToInternal": "No", "InvokeShareTopology": "Yes", "Multizone": "No"})
T["Describe Geometry"].UpdateChildTasks(SetupTypeChanged=True)
run("Describe Geometry")
for attempt in range(3):     # the join step crashes intermittently (SIGSEGV in Fluent); a re-run usually passes
    try:
        run("Apply Share Topology")
        break
    except RuntimeError as e:
        if "task update" not in str(e) or attempt == 2:
            raise
        print(f"Share Topology failed (attempt {attempt + 1}); retrying", flush=True)
run("Update Boundaries")

# region types: Air_* are fluid, the rest solid
# region names = object names printed at import ("origin-<component>:1-<body>")
names = ["airmain-1-air_main", "hotend-1-nozzlebody", "heatsink-1-heatsink", "hotend-1-heatbreak",
         "hotend-1-heatbreakstub",
         "fanair-1-air_fan", "fan-1-fanframe", "fan-1-fanhub", "duct-1-duct"]   # <component>-1-<body>
short = [n.split("-")[-1] for n in names]
types = ["fluid" if s.startswith("air") else "solid" for s in short]
try:
    run("Update Regions", {"OldRegionNameList": names, "OldRegionTypeList": ["solid"] * len(names),
                           "RegionNameList": short, "RegionTypeList": types})
except Exception as e:                       # fall back to defaults; zone types can be switched in the solver
    print("Update Regions with names failed:", str(e)[:200], flush=True)
    print("task attrs:", [a for a in dir(T["Update Regions"]) if not a.startswith("_")], flush=True)
    T["Update Regions"].Arguments.set_state({})
    run("Update Regions")
m.tui.objects.volumetric_regions.list("*", "*")

run("Add Boundary Layers", {"NumberOfLayers": 3, "TransitionRatio": 0.35, "BLControlName": "smooth-transition_1"})
run("Generate the Volume Mesh", {"VolumeFill": "poly-hexcore", "VolumeFillControls": {"HexMaxCellLength": PS["HexMax"]}})

m.tui.mesh.check_mesh()
m.meshing.File.WriteMesh(FileName=MESH)        # TUI write_mesh splits a path with spaces and then waits forever
print(f"[{time.time() - t0:5.0f}s] wrote {MESH}", flush=True)
m.exit()
assert os.path.getsize(MESH) > 0, "mesh file not written"
