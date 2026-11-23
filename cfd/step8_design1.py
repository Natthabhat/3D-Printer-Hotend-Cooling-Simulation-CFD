"""Design 1: stock heatsink, Ti-6Al-4V heat break, 45 °C ambient (warm start from the stock 45 °C solution)."""
from fl import connect
from run_case import add_titanium, solve_report

s = connect()
assert abs(s.settings.setup.boundary_conditions.pressure_outlet["airmain-1-air_main:40909:49022"]
           .thermal.backflow_total_temperature.value() - 318.15) < 0.01, "expected the 45 °C stock case to be loaded"
add_titanium(s)
print({z: s.settings.setup.cell_zone_conditions.solid[z].general.material() for z in ("heatbreak", "heatbreakstub", "heatsink")})
solve_report(s, "design1_45C")
print("done design1")
