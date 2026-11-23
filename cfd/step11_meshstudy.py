"""Solve the case just set up by setup_case.py (fresh hybrid initialisation) for the mesh study. Usage: python step11_meshstudy.py <tag>"""
import sys
from fl import connect
from run_case import solve_report

s = connect()
s.tui.solve.iterate(40)
solve_report(s, sys.argv[1], n=800, with_images=False)
print("done", sys.argv[1])
