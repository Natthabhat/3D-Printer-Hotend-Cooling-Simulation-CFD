"""Read the mesh into the live Fluent window and print every boundary zone with its bounding box."""
import os
from fl import connect, HERE
from zones import table

s = connect()
s.settings.file.read_mesh(file_name=os.path.join(HERE, "hotend.msh.h5"))
s.settings.mesh.check()
cz = s.settings.setup.cell_zone_conditions
print("FLUID:", list(cz.fluid.keys()), "| SOLID:", list(cz.solid.keys()))
table(s)
