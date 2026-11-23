"""Read a mesh into the live Fluent window and apply the full hotend setup, finding zones by position.
Usage: python setup_case.py <mesh.msh.h5> <ambient °C> [ti]   (ti = titanium heat break)"""
import csv, math, os, sys
import numpy as np
from fl import connect, HERE
from zones import all_zones, bbox
from run_case import add_titanium, set_fan_table

MESH, T_AMB_C = sys.argv[1], float(sys.argv[2])
TI = len(sys.argv) > 3 and sys.argv[3] == "ti"
T_NOZZLE = 493.15
A_FAN = math.pi * (11.5 ** 2 - 6.5 ** 2) * 1e-6
CSV = os.path.join(HERE, "..", "fan_curve_2510.csv")

rows = [r for r in csv.reader(l for l in open(CSV, encoding="utf-8") if not l.startswith("#"))][1:]
q = np.array([float(r[1]) for r in rows]); dp = np.array([float(r[5]) for r in rows])
v = q / A_FAN
coef = np.polynomial.polynomial.polyfit(v, dp, 3)

s = connect()
s.settings.file.read_mesh(file_name=os.path.join(HERE, MESH))
st = s.settings.setup
bc = st.boundary_conditions

# --- zones by position (mm) ---
# meshing sometimes merges the two fan-air/main-air rings (x = 19.25 and 29.25) into one zone: split it
for typ, n in all_zones(s):
    if typ == "fan" and "air_main" in n:
        lo, hi = bbox(s, n)
        if hi[0] - lo[0] > 5:
            print("separating", n, "into connected regions")
            s.tui.mesh.modify_zones.sep_face_zone_region(n)
box = fan_face = None
fan_ring, fan_walls = [], []
for typ, n in all_zones(s):
    lo, hi = bbox(s, n)
    if typ == "wall" and np.allclose(lo, [-30, -30, -10], atol=0.01) and np.allclose(hi, [60, 30, 80], atol=0.01):
        box = n
    elif typ == "fan":
        if abs(lo[0] - 19.25) < 0.01 and abs(hi[0] - 19.25) < 0.01:
            fan_face = n
        elif abs(lo[0] - 29.25) < 0.01 and abs(hi[0] - 29.25) < 0.01:
            fan_ring.append(n)
        else:
            fan_walls.append(n)
print("box:", box, "| fan face:", fan_face, "| intake ring:", fan_ring, "| fan walls:", fan_walls)
assert box and fan_face and len(fan_ring) == 1, "zone mapping failed"
if fan_walls:
    bc.set_zone_type(zone_list=fan_walls, new_type="wall")
bc.set_zone_type(zone_list=fan_ring, new_type="interior")
bc.set_zone_type(zone_list=[box], new_type="pressure-outlet")

# --- physics ---
st.models.energy.enabled = True
st.models.viscous.model = "k-omega"
st.models.viscous.k_omega_model = "sst"
st.general.operating_conditions.gravity = {"enable": True, "components": [0.0, 0.0, -9.81]}
mat = st.materials
mat.fluid["air"].density.option = "incompressible-ideal-gas"
mat.database.copy_by_name(type="solid", name="steel")
al = mat.solid["aluminum"]
al.density.value, al.specific_heat.value, al.thermal_conductivity.value = 2700, 896, 167
if "abs" not in mat.solid.keys():
    mat.solid.create("abs")
ab = mat.solid["abs"]
ab.density.value, ab.specific_heat.value, ab.thermal_conductivity.value = 1050, 1400, 0.17
cz = st.cell_zone_conditions.solid
for z, m in (("heatsink", "aluminum"), ("nozzlebody", "steel"), ("heatbreak", "steel"), ("heatbreakstub", "steel"),
             ("duct", "abs"), ("fanframe", "abs"), ("fanhub", "abs")):
    cz[z].general.material = m
if TI:
    add_titanium(s)
cz["nozzlebody"].fixed_values = {"enable": True, "variables": {"Temperature": {"option": "value", "value": T_NOZZLE}}}

set_fan_table(s)                                       # tabulated curve (piecewise-linear) on the Ø23 face
bc.pressure_outlet[box].thermal.backflow_total_temperature.value = T_AMB_C + 273.15

# --- reports (same names as the stock case) ---
walls = list(bc.wall.keys())
hs = [n for n in walls if n == "air_main-heatsink"]
nz = [n for n in walls if n.startswith("air_main-nozzlebody") and not n.endswith("-shadow")]
assert hs and nz, ("wall names", walls[:20])
rd = s.settings.solution.report_definitions
rd.volume["t_stub_avg"] = {"report_type": "volume-average", "field": "temperature", "cell_zones": ["heatbreakstub"]}
rd.volume["t_heatsink_max"] = {"report_type": "volume-max", "field": "temperature", "cell_zones": ["heatsink"]}
rd.volume["t_heatsink_avg"] = {"report_type": "volume-average", "field": "temperature", "cell_zones": ["heatsink"]}
rd.volume["t_heatbreak_max"] = {"report_type": "volume-max", "field": "temperature", "cell_zones": ["heatbreak"]}
rd.flux["q_heatsink"] = {"report_type": "flux-heattransfer", "boundaries": hs}
rd.flux["q_nozzle"] = {"report_type": "flux-heattransfer", "boundaries": nz}
rd.surface["fan_vx"] = {"report_type": "surface-areaavg", "field": "x-velocity", "surface_names": [fan_face]}
rd.surface["fan_vol"] = {"report_type": "surface-volumeflowrate", "surface_names": [fan_face]}
rd.surface["fan_dp"] = {"report_type": "surface-areaavg", "field": "pressure", "surface_names": [fan_face]}
s.settings.solution.monitor.report_plots["temps"] = {"report_defs": ["t_stub_avg", "t_heatsink_max", "t_heatbreak_max"]}

s.settings.solution.initialization.hybrid_initialize()
print("setup done:", MESH, f"ambient {T_AMB_C} C", "titanium" if TI else "steel")
