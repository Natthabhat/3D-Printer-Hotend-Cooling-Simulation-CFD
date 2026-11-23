"""Re-solve stock, D1, D2 with the tabulated (piecewise-linear) fan curve, warm-started from the polynomial-fan
solutions, then D2 with laminar flow as a turbulence-model sensitivity. All at 45 °C ambient."""
import os, time
from fl import connect, HERE
from run_case import set_fan_table, solve_report

s = connect()
RUNS = [("stock_45C_pl", "hotend_stock_45C.cas.h5"),
        ("design1_45C_pl", "hotend_design1_45C.cas.h5"),
        ("design2_45C_pl", "hotend_design2_45C.cas.h5")]
for tag, case in RUNS:
    t0 = time.time()
    print(f"===== RUN {tag} from {case}", flush=True)
    s.settings.file.read_case_data(file_name=os.path.join(HERE, case))
    set_fan_table(s)
    solve_report(s, tag, n=500, with_images=False)
    print(f"===== END {tag} {time.time() - t0:.0f}s", flush=True)

t0 = time.time()
print("===== RUN design2_45C_pl_laminar (continues from design2_45C_pl)", flush=True)
s.settings.setup.models.viscous.model = "laminar"
solve_report(s, "design2_45C_pl_laminar", n=600, with_images=False)
print(f"===== END design2_45C_pl_laminar {time.time() - t0:.0f}s", flush=True)
