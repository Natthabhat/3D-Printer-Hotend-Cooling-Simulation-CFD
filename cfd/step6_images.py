"""Report images with explicit cameras (Z up) on the converged stock case."""
import os
from fl import connect, HERE

OUT = os.path.join(HERE, "results")
s = connect()
g = s.settings.results.graphics
cam = s.tui.display.views.camera
K = lambda c: c + 273.15


def view(pos, target, width, height):
    cam.position(*pos)
    cam.target(*target)
    cam.up_vector(0, 0, 1)
    cam.field(width, height)


def contour(name, field, surfaces, rng, pos, target, fname, width=0.075, height=0.055):
    if name not in g.contour.keys():
        g.contour.create(name)
    c = g.contour[name]
    c.field = field
    c.surfaces_list = surfaces
    c.range_option = ({"option": "auto-range-off", "auto_range_off": {"minimum": rng[0], "maximum": rng[1], "clip_to_range": False}}
                      if rng else {"option": "auto-range-on"})
    c.display()
    view(pos, target, width, height)
    g.picture.save_picture(file_name=os.path.join(OUT, fname))
    print("saved", fname)


mid = (0.0, 0.0, 0.035)
cool = (K(25), K(60))                                  # shows heatsink gradients; nozzle (220 °C) saturates
contour("t_x0", "temperature", ["plane_x0"], cool, (0.3, 0.0, 0.035), mid, "temp_section_x0.png")
contour("t_y0", "temperature", ["plane_y0"], cool, (0.01, -0.3, 0.035), (0.01, 0.0, 0.035), "temp_section_y0.png",
        width=0.09, height=0.06)
contour("t_y0_full", "temperature", ["plane_y0"], (K(25), K(220)), (0.01, -0.3, 0.035), (0.01, 0.0, 0.035),
        "temp_section_y0_fullrange.png", width=0.09, height=0.06)
contour("vmag_y0", "velocity-magnitude", ["plane_y0"], None, (0.01, -0.3, 0.035), (0.01, 0.0, 0.035),
        "velocity_section_y0.png", width=0.09, height=0.06)
solids = ["air_main-heatsink", "air_main-heatbreak", "air_main-nozzlebody", "air_main-nozzlebody_1"]
contour("t_solids", "temperature", solids, cool, (-0.09, -0.12, 0.09), (0.0, 0.0, 0.03), "temp_solids_iso.png",
        width=0.07, height=0.06)
