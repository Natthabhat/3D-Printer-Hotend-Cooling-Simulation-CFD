"""Export the ambient-run images only (the solve part of step7_ambient.py already ran). Usage: python step7_images.py 45"""
import os, sys
from fl import connect, HERE

T_AMB_C = float(sys.argv[1]) if len(sys.argv) > 1 else 45.0
TAG = f"{T_AMB_C:.0f}C"
s = connect()
res_dir = os.path.join(HERE, "results")
exec("# images" + open(os.path.join(HERE, "step7_ambient.py"), encoding="utf-8").read().split("# images", 1)[1])
