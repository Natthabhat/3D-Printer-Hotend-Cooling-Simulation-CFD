"""Re-solve the stock case at a new ambient temperature (warm start), check convergence, save results + images.
Usage: python step7_ambient.py 45"""
import json, os, sys
from fl import connect, HERE

T_AMB_C = float(sys.argv[1]) if len(sys.argv) > 1 else 45.0
TAG = f"{T_AMB_C:.0f}C"
N = 600
s = connect()
s.settings.setup.boundary_conditions.pressure_outlet["airmain-1-air_main:40909:49022"].thermal.backflow_total_temperature.value = T_AMB_C + 273.15
s.settings.solution.monitor.residual.options.criterion_type = "none"
s.tui.solve.iterate(N)

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
b["t_ambient_C"] = T_AMB_C
res_dir = os.path.join(HERE, "results")
json.dump(b, open(os.path.join(res_dir, f"stock_results_{TAG}.json"), "w"), indent=1)
s.settings.file.write_case_data(file_name=os.path.join(HERE, f"hotend_stock_{TAG}.cas.h5"))

# images (same cameras as step6), colour range ambient .. ambient + 35 °C
exec(open(os.path.join(HERE, "step6_images.py"), encoding="utf-8").read().split("mid = ")[0])
OUT = os.path.join(res_dir, TAG)
os.makedirs(OUT, exist_ok=True)
rng = (T_AMB_C + 273.15, T_AMB_C + 35 + 273.15)
contour("t_ym6", "temperature", ["plane_ym6"], rng, (0.01, -0.3, 0.035), (0.01, -0.006, 0.035), "temp_section_fins.png",
        width=0.09, height=0.06)
contour("vmag_ym6", "velocity-magnitude", ["plane_ym6"], None, (0.01, -0.3, 0.035), (0.01, -0.006, 0.035),
        "velocity_section_fins.png", width=0.09, height=0.06)
solids = ["air_main-heatsink", "air_main-heatbreak", "air_main-nozzlebody", "air_main-nozzlebody_1"]
contour("t_solids", "temperature", solids, rng, (-0.09, -0.12, 0.09), (0.0, 0.0, 0.03), "temp_solids_iso.png",
        width=0.07, height=0.06)
contour("t_x0", "temperature", ["plane_x0"], rng, (0.3, 0.0, 0.035), (0.0, 0.0, 0.035), "temp_section_x0.png")
print("done", TAG)
