"""Zone helpers: bounding boxes of boundary zones in the live Fluent session (mm)."""
import numpy as np
from ansys.fluent.core.fields.field_data.requests import SurfaceDataType, SurfaceFieldDataRequest

BC_TYPES = ("wall", "interior", "fan", "pressure_outlet", "velocity_inlet", "intake_fan", "symmetry")


def all_zones(s):
    bc = s.settings.setup.boundary_conditions
    out = []
    for typ in BC_TYPES:
        grp = getattr(bc, typ, None)
        if grp is not None:
            out += [(typ, n) for n in grp.keys()]
    return out


def bbox(s, name):
    d = s.fields.field_data.get_field_data(SurfaceFieldDataRequest(surfaces=[name], data_types=[SurfaceDataType.Vertices]))
    v = np.asarray(d[name].vertices).reshape(-1, 3) * 1000.0
    return v.min(0), v.max(0)


def table(s, skip_prefix="heatsink-1-heatsink:"):
    rows = []
    for typ, n in all_zones(s):
        if n.startswith(skip_prefix) and n.count(":") >= 2:
            continue
        lo, hi = bbox(s, n)
        rows.append((typ, n, lo, hi))
        print(f"{typ:15s} {n:50s} min={np.round(lo, 2)} max={np.round(hi, 2)}")
    return rows
