"""Convergence check (+50 iterations), final numbers, and contour/vector images on section planes."""
import json, os
from fl import connect, HERE

OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)
s = connect()
rd = s.settings.solution.report_definitions
NAMES = ["t_stub_avg", "t_heatsink_max", "t_heatsink_avg", "t_heatbreak_max", "q_heatsink", "q_nozzle",
         "fan_vol", "fan_vx", "fan_dp"]


def reports():
    out = {}
    for item in rd.compute(report_defs=NAMES):
        for k, v in item.items():
            out[k] = float(v[0] if isinstance(v, (list, tuple)) else v)
    return out


a = reports()
s.tui.solve.iterate(50)
b = reports()
print("CONVERGENCE (change over last 50 iterations):")
for k in NAMES:
    print(f"  {k:16s} {a[k]:12.5g} -> {b[k]:12.5g}  change {b[k] - a[k]:+.3g}")
json.dump(b, open(os.path.join(OUT, "stock_results.json"), "w"), indent=1)

# section planes through the nozzle axis (x = 0, y = 0)
srf = s.settings.results.surfaces.plane_surface
for name, method, key in (("plane_x0", "yz-plane", "x"), ("plane_y0", "zx-plane", "y")):
    if name not in srf.keys():
        srf.create(name)
    try:
        srf[name] = {"method": method, key: 0.0}
    except Exception as e:
        print(name, "plane fields:", json.dumps(srf[name].get_state(), default=str)[:400], "|", str(e)[:200])
        raise
print("planes:", {n: srf[n].get_state() for n in ("plane_x0", "plane_y0")})

g = s.settings.results.graphics
pic = g.picture
try:
    pic.x_resolution, pic.y_resolution = 1600, 1200
except Exception as e:
    print("picture size fields:", str(e)[:200])
solids = ["air_main-heatsink", "air_main-heatbreak", "air_main-nozzlebody", "air_main-nozzlebody_1"]


def shot(obj_type, name, settings, view, fname):
    grp = getattr(g, obj_type)
    if name not in grp.keys():
        grp.create(name)
    grp[name] = settings
    grp[name].display()
    g.views.restore_view(view_name=view)
    g.views.auto_scale()
    pic.save_picture(file_name=os.path.join(OUT, fname))
    print("saved", fname)


temp_range = {"option": "auto-range-off", "auto_range_off": {"minimum": 298.15, "maximum": 373.15}}
shot("contour", "t_x0", {"field": "temperature", "surfaces_list": ["plane_x0"], "range_option": temp_range},
     "right", "temp_section_x0.png")
shot("contour", "t_y0", {"field": "temperature", "surfaces_list": ["plane_y0"], "range_option": temp_range},
     "front", "temp_section_y0.png")
shot("contour", "t_solids", {"field": "temperature", "surfaces_list": solids, "range_option": temp_range},
     "isometric", "temp_solids_iso.png")
shot("vector", "v_y0", {"field": "velocity-magnitude", "surfaces_list": ["plane_y0"]}, "front", "velocity_section_y0.png")
s.settings.file.write_case_data(file_name=os.path.join(HERE, "hotend_stock.cas.h5"))
print("done")
