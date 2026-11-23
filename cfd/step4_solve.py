"""Iterate the live case N times, then print the reports and the mean x-velocity on the fan face (should be < 0)."""
import os, sys
from fl import connect, HERE

N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
SAVE = len(sys.argv) > 2 and sys.argv[2] == "save"
s = connect()
# default residual criteria (1e-3) stop the run at ~60 iterations while solid temperatures are still drifting;
# judge convergence from the temperature reports instead
s.settings.solution.monitor.residual.options.criterion_type = "none"
s.tui.solve.iterate(N)      # TUI iterate blocks until done; settings iterate returned early and the run stopped
rd = s.settings.solution.report_definitions
names = ["t_stub_avg", "t_heatsink_max", "t_heatsink_avg", "t_heatbreak_max", "fan_mdot", "q_heatsink", "q_nozzle"]
vals = rd.compute(report_defs=names)
for item in vals:
    for k, v in item.items():
        val = v[0] if isinstance(v, (list, tuple)) else v
        if k.startswith("t_"):
            print(f"{k:16s} {val:10.3f} K = {val - 273.15:7.2f} C")
        elif k == "fan_mdot":
            print(f"{k:16s} {val:10.3e} kg/s = {val / 1.18 * 3600:6.2f} m3/h")
        else:
            print(f"{k:16s} {val:10.3f} W")
si = s.settings.results.report.surface_integrals
print("fan-face mean x-velocity:", si.get(report_type="area-weighted-avg", surface_names=["air_fan-air_main"],
                                           report_of="x-velocity") if hasattr(si, "get") else "n/a")
if SAVE:
    s.settings.file.write_case_data(file_name=os.path.join(HERE, "hotend_stock.cas.h5"))
    print("case+data saved")
