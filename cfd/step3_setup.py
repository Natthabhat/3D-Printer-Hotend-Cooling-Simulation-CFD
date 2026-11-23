"""Physics, materials, BCs, fan curve, reports; initialise and save hotend_stock.cas.h5 (live Fluent window)."""
import csv, math, os
import numpy as np
from fl import connect, HERE

FAN_FACE, BOX = "air_fan-air_main", "airmain-1-air_main:40909:49022"
T_NOZZLE, T_AMB = 493.15, 298.15                       # 220 °C heater contact, 25 °C ambient
A_FAN = math.pi * (11.5 ** 2 - 6.5 ** 2) * 1e-6        # Ø23 opening minus Ø13 hub (m2) = CFD fan face
CSV = os.path.join(HERE, "..", "fan_curve_2510.csv")

# fan curve -> cubic dp(v) on the CFD fan-face velocity
rows = [r for r in csv.reader(l for l in open(CSV, encoding="utf-8") if not l.startswith("#"))][1:]
q = np.array([float(r[1]) for r in rows]); dp = np.array([float(r[5]) for r in rows])
v = q / A_FAN
coef = np.polynomial.polynomial.polyfit(v, dp, 3)
print("fan v_max %.2f m/s, polynomial %s, max fit error %.1f Pa" % (
    v.max(), np.round(coef, 4), np.abs(np.polynomial.polynomial.polyval(v, coef) - dp).max()))

s = connect()
st = s.settings.setup
st.models.energy.enabled = True
st.models.viscous.model = "k-omega"
st.models.viscous.k_omega_model = "sst"
st.general.operating_conditions.gravity = {"enable": True, "components": [0.0, 0.0, -9.81]}

mat = st.materials
mat.fluid["air"].density.option = "incompressible-ideal-gas"      # buoyancy of the hot plume
mat.database.copy_by_name(type="solid", name="steel")
al = mat.solid["aluminum"]
al.density.value, al.specific_heat.value, al.thermal_conductivity.value = 2700, 896, 167   # 6061
if "abs" not in mat.solid.keys():
    mat.solid.create("abs")
ab = mat.solid["abs"]
ab.density.value, ab.specific_heat.value, ab.thermal_conductivity.value = 1050, 1400, 0.17

cz = st.cell_zone_conditions.solid
for z, m in (("heatsink", "aluminum"), ("nozzlebody", "steel"), ("heatbreak", "steel"), ("heatbreakstub", "steel"),
             ("duct", "abs"), ("fanframe", "abs"), ("fanhub", "abs")):
    cz[z].general.material = m
cz["nozzlebody"].fixed_values = {"enable": True, "variables": {"Temperature": {"option": "value", "value": T_NOZZLE}}}

bc = st.boundary_conditions
pj = bc.fan[FAN_FACE].pressure_jump_specification
pj.reverse_fan_direction = True                         # face normal is +X; the fan blows -X into the duct
pj.pressure_jump = {"option": "polynomial", "function_of": "normal-velocity",
                    "polynomial": {"function_of": "normal-velocity", "coefficients": [float(c) for c in coef]}}
pj.limit_polynomial_velocity_range = True
try:
    pj.min_velocity, pj.max_velocity = 0.0, float(v.max())
except Exception as e:
    print("velocity range fields:", str(e)[:150])
out = bc.pressure_outlet[BOX]
out.thermal.backflow_total_temperature.value = T_AMB
print("FAN:", bc.fan[FAN_FACE].pressure_jump_specification.get_state())

# reports
rd = s.settings.solution.report_definitions
rd.volume["t_stub_avg"] = {"report_type": "volume-average", "field": "temperature", "cell_zones": ["heatbreakstub"]}
rd.volume["t_heatsink_max"] = {"report_type": "volume-max", "field": "temperature", "cell_zones": ["heatsink"]}
rd.volume["t_heatsink_avg"] = {"report_type": "volume-average", "field": "temperature", "cell_zones": ["heatsink"]}
rd.volume["t_heatbreak_max"] = {"report_type": "volume-max", "field": "temperature", "cell_zones": ["heatbreak"]}
rd.flux["fan_mdot"] = {"report_type": "flux-massflow", "boundaries": [FAN_FACE]}
rd.flux["q_heatsink"] = {"report_type": "flux-heattransfer", "boundaries": ["air_main-heatsink"]}
rd.flux["q_nozzle"] = {"report_type": "flux-heattransfer", "boundaries": ["air_main-nozzlebody", "air_main-nozzlebody_1",
                                                                          "hotend-1-heatbreak-hotend-1-nozzlebody_1"]}
names = ["t_stub_avg", "t_heatsink_max", "t_heatsink_avg", "t_heatbreak_max", "fan_mdot", "q_heatsink", "q_nozzle"]
mon = s.settings.solution.monitor
mon.report_files["hotend-rfile"] = {"report_defs": names, "file_name": os.path.join(HERE, "hotend_reports.out")}
mon.report_plots["temps"] = {"report_defs": ["t_stub_avg", "t_heatsink_max", "t_heatbreak_max"]}

s.settings.solution.initialization.hybrid_initialize()
s.settings.file.write_case(file_name=os.path.join(HERE, "hotend_stock.cas.h5"))
print("setup done; case written")
