"""Print type, vertex bounding box and face count of every boundary zone (heatsink sub-zones summarised)."""
import os
import numpy as np
import ansys.fluent.core as pf

HERE = os.path.dirname(os.path.abspath(__file__))
s = pf.launch_fluent(mode="solver", dimension=3, precision="double", processor_count=4, ui_mode="no_gui",
                     cwd=HERE, start_timeout=300)
s.settings.file.read_mesh(file_name=os.path.join(HERE, "hotend.msh.h5"))
bc = s.settings.setup.boundary_conditions
fd = s.fields.field_data
from ansys.fluent.core.fields.field_data.requests import SurfaceDataType, SurfaceFieldDataRequest

zones = []
for typ in ("wall", "interior", "fan", "pressure_outlet", "velocity_inlet", "intake_fan", "symmetry"):
    grp = getattr(bc, typ, None)
    if grp is not None:
        zones += [(typ, n) for n in grp.keys()]
print("total zones:", len(zones))
small = [n for t, n in zones if n.startswith("heatsink-1-heatsink:") and n.count(":") >= 2]
print("heatsink sub-zones:", len(small))
for typ, n in zones:
    if n in small:
        continue
    try:
        d = fd.get_field_data(SurfaceFieldDataRequest(surfaces=[n], data_types=[SurfaceDataType.Vertices]))
        v = np.asarray(d[n].vertices).reshape(-1, 3) * 1000
        print(f"{typ:15s} {n:45s} nverts={len(v):6d} min={np.round(v.min(0), 2)} max={np.round(v.max(0), 2)}")
    except Exception as e:
        print(f"{typ:15s} {n:45s} err {str(e)[:120]}")
s.exit()
