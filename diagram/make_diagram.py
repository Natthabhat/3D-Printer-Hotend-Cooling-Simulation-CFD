"""Labelled component diagram of the stock Bambu X2D hotend + 2510 fan + duct (from the Fusion renders)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
INK, LEADER, AIR = "#0b0b0b", "#52514e", "#2a78d6"


def load(name):
    """Render on white (Fusion saved a transparent background)."""
    im = Image.open(os.path.join(HERE, name)).convert("RGBA")
    bg = Image.new("RGBA", im.size, "white")
    bg.alpha_composite(im)
    return bg.convert("RGB")


def label(ax, text, xy, xytext, ha):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=16, color=INK, ha=ha, va="center",   # readable at page width
                arrowprops=dict(arrowstyle="-", color=LEADER, linewidth=1.1, shrinkA=4, shrinkB=0))
    ax.plot(*xy, "o", color=INK, markersize=5, markeredgecolor="white", markeredgewidth=1.2, zorder=5)


fig, (a, b) = plt.subplots(1, 2, figsize=(17, 10.5), dpi=150, gridspec_kw={"width_ratios": [1.15, 1]})
for ax in (a, b):
    ax.set_axis_off()

# (a) front view: whole assembly + airflow (pixel coordinates measured on the 1600x1600 render)
a.imshow(load("view_front.png"))
a.set_xlim(-330, 1900); a.set_ylim(1640, -60)
a.set_title("(a) Front view – hotend, duct and fan", loc="left", fontsize=19, color=INK, pad=10)
L, R = -310, 1880
label(a, "Filament inlet", (487, 95), (L, 40), "left")
label(a, "Heatsink fins", (330, 250), (L, 160), "left")
label(a, "Bottom fingers", (330, 540), (L, 560), "left")
label(a, "Heat break", (487, 670), (L, 680), "left")
label(a, "Nozzle body\n(heater zone,\n220 °C)", (380, 1000), (L, 1000), "left")
label(a, "Nozzle tip", (487, 1500), (L, 1500), "left")
label(a, "Air duct", (915, 600), (R, 940), "right")
label(a, "Hotend fan 2510\n(25×25×10 mm)", (1230, 700), (R, 1120), "right")
for x0, x1, y in ((1760, 1395, 450), (205, -60, 370)):       # air enters the fan, leaves through the fins
    a.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>", mutation_scale=28, color=AIR, linewidth=3))
a.text(1580, 395, "air in", color=AIR, fontsize=17, ha="center")
a.text(70, 445, "air out", color=AIR, fontsize=17, ha="center")
a.add_patch(FancyArrowPatch((1060, 330), (770, 330), arrowstyle="-|>", mutation_scale=22, color=AIR, linewidth=2,
                            linestyle="--"))

# (b) side view: hotend alone (fan and duct hidden)
b.imshow(load("view_side_hotend.png"))
b.set_xlim(150, 1820); b.set_ylim(1640, -20)
b.set_title("(b) Side view – hotend only", loc="left", fontsize=19, color=INK, pad=10)
L, R = 170, 1800
label(b, "Filament inlet", (800, 90), (L, 60), "left")
label(b, "Fins", (560, 213), (L, 250), "left")
label(b, "Central spine", (800, 330), (L, 420), "left")
label(b, "Bottom fingers", (491, 580), (L, 640), "left")
label(b, "Heat break\n(stub in socket)", (815, 505), (L, 800), "left")
label(b, "Nozzle body\n(heater zone)", (760, 1000), (L, 1060), "left")
label(b, "Nozzle tip", (800, 1560), (L, 1560), "left")
label(b, "Top fin plate", (1080, 152), (R, 152), "right")
label(b, "Latch plate", (1047, 380), (R, 380), "right")
label(b, "Latch web", (995, 395), (R, 520), "right")
label(b, "Latch tab", (930, 740), (R, 740), "right")
label(b, "Side rail", (865, 1050), (R, 1050), "right")

fig.text(0.01, 0.015, "Bambu Lab X2D / P2S hotend (stock) – CAD rebuilt from the 1:1 STL; heater block and silicone sock not modelled.",
         fontsize=13, color=LEADER)
fig.tight_layout(rect=(0, 0.03, 1, 1))
out = os.path.join(HERE, "hotend_components_diagram.png")
fig.savefig(out, facecolor="white")
print("saved", out)
