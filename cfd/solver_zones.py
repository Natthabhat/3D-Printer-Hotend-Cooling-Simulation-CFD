"""Read hotend.msh.h5 in the Fluent solver and list cell zones, face zones (type, area, x-range) so BCs can be mapped."""
import os
import ansys.fluent.core as pf

HERE = os.path.dirname(os.path.abspath(__file__))
s = pf.launch_fluent(mode="solver", dimension=3, precision="double", processor_count=4, ui_mode="no_gui",
                     cwd=HERE, start_timeout=300)
s.settings.file.read_mesh(file_name=os.path.join(HERE, "hotend.msh.h5"))
s.tui.mesh.check()
bc = s.settings.setup.boundary_conditions
cz = s.settings.setup.cell_zone_conditions
print("CELL ZONES fluid:", list(cz.fluid.keys()), "| solid:", list(cz.solid.keys()))
names = []
for typ in ("wall", "interior", "pressure_outlet", "velocity_inlet", "fan", "symmetry"):
    grp = getattr(bc, typ, None)
    if grp is not None and grp.keys():
        print(f"BC {typ}: {list(grp.keys())}")
        names += list(grp.keys())
print("BC types available:", [t for t in dir(bc) if not t.startswith("_")][:80])
s.settings.setup.models.energy.enabled = True              # solid thermal options appear only with energy on
print("SOLID nozzlebody state:", cz.solid["nozzlebody"].get_state())
print("FLUID air_fan state keys:", list(cz.fluid["air_fan"].get_state().keys()))
for typ in ("wall", "interior"):
    grp = getattr(bc, typ)
    for n in list(grp.keys())[:3]:
        print(f"{typ} {n} state:", grp[n].get_state())
s.exit()
