"""Design 2: improved heatsink + Ti-6Al-4V heat break, 45 °C ambient. Run after setup_case.py hotend_d2.msh.h5 45 ti."""
from fl import connect
from run_case import solve_report

s = connect()
s.tui.solve.iterate(40)        # quick start so hybrid-initialised flow settles before the long run
solve_report(s, "design2_45C", n=700)
print("done design2")
