"""Shared: fan curve, solve the live case, check convergence and balances, save case/data + json + images."""
import csv, json, math, os
from fl import HERE

NAMES = ["t_stub_avg", "t_heatsink_max", "t_heatsink_avg", "t_heatbreak_max", "q_heatsink", "q_nozzle",
         "fan_vol", "fan_vx", "fan_dp"]
TI64 = {"density": 4430, "specific_heat": 526, "thermal_conductivity": 6.7}   # Ti-6Al-4V
A_FAN = math.pi * (11.5 ** 2 - 6.5 ** 2) * 1e-6        # CFD fan face: Ø23 opening minus Ø13 hub (m2)
CSV = os.path.join(HERE, "..", "fan_curve_2510.csv")


def fan_table():
    """(face velocity m/s, pressure jump Pa) from the tabulated curve, velocities recomputed for the Ø23 face."""
    rows = [r for r in csv.reader(l for l in open(CSV, encoding="utf-8") if not l.startswith("#"))][1:]
    return [(float(r[1]) / A_FAN, float(r[5])) for r in rows]


def set_fan_table(s):
    """Piecewise-linear pressure jump = the tabulated curve itself (the cubic fit overshot the stall plateau)."""
    bc = s.settings.setup.boundary_conditions
    (fan,) = list(bc.fan.keys())
    pj = bc.fan[fan].pressure_jump_specification
    pj.reverse_fan_direction = True                     # fan face normal is +X; the fan blows -X into the duct
    pj.pressure_jump.option = "piecewise-linear"
    pj.pressure_jump.piecewise_linear = {"function_of": "normal-velocity",
                                         "data_points": [{"item": v, "value": p} for v, p in fan_table()]}
    return fan


def add_titanium(s, zones=("heatbreak", "heatbreakstub")):
    mat = s.settings.setup.materials.solid
    if "ti-6al-4v" not in mat.keys():
        mat.create("ti-6al-4v")
    m = mat["ti-6al-4v"]
    m.density.value, m.specific_heat.value, m.thermal_conductivity.value = (
        TI64["density"], TI64["specific_heat"], TI64["thermal_conductivity"])
    for z in zones:
        s.settings.setup.cell_zone_conditions.solid[z].general.material = "ti-6al-4v"


def _compute(s, names):
    out = {}
    for item in s.settings.solution.report_definitions.compute(report_defs=names):
        for k, v in item.items():
            out[k] = float(v[0] if isinstance(v, (list, tuple)) else v)
    return out


def reports(s):
    return _compute(s, NAMES)


def balance(s):
    """Mass: net flow through the outer box vs the fan flow. Energy: heat leaving the 220 °C nozzle body
    (sum over its interfaces) vs net energy leaving through the box. Both residuals should be ~0."""
    bc = s.settings.setup.boundary_conditions
    rd = s.settings.solution.report_definitions
    (box,) = list(bc.pressure_outlet.keys())
    noz = [n for n in bc.wall.keys() if "nozzlebody" in n]
    rd.flux["bal_m_box"] = {"report_type": "flux-massflow", "boundaries": [box]}
    rd.flux["bal_q_box"] = {"report_type": "flux-heattransfer", "boundaries": [box]}
    names = ["bal_m_box", "bal_q_box", "fan_vol"]
    for i, n in enumerate(noz):
        rd.flux[f"bal_qn{i}"] = {"report_type": "flux-heattransfer", "boundaries": [n]}
        names.append(f"bal_qn{i}")
    v = _compute(s, names)
    pairs = {}
    for i, n in enumerate(noz):                         # wall and shadow carry equal and opposite heat
        pairs.setdefault(n.replace("-shadow", ""), []).append(v[f"bal_qn{i}"])
    q_nozzle_out = sum(max(abs(x) for x in p) for p in pairs.values())
    m_fan = v["fan_vol"] * 1.11                         # air density at ~45 °C
    out = {"mass_net_box": v["bal_m_box"], "mass_fan": m_fan, "mass_imbalance_pct": 100 * abs(v["bal_m_box"]) / m_fan,
           "q_box": v["bal_q_box"], "q_nozzle_out": q_nozzle_out,
           "energy_imbalance_pct": 100 * abs(abs(v["bal_q_box"]) - q_nozzle_out) / q_nozzle_out}
    print("BALANCE:", {k: round(x, 6) for k, x in out.items()})
    return out


def solve_report(s, tag, t_amb_c=45.0, n=600, with_images=True):
    s.settings.solution.monitor.residual.options.criterion_type = "none"   # default 1e-3 stops too early
    s.tui.solve.iterate(n)
    a = reports(s)
    s.tui.solve.iterate(50)
    b = reports(s)
    print(f"CONVERGENCE {tag} (change over last 50 iterations):")
    for k in NAMES:
        print(f"  {k:16s} {a[k]:12.5g} -> {b[k]:12.5g}  change {b[k] - a[k]:+.3g}")
    b["t_ambient_C"] = t_amb_c
    b["change_last50"] = {k: b[k] - a[k] for k in NAMES}
    b["balance"] = balance(s)
    res = os.path.join(HERE, "results")
    json.dump(b, open(os.path.join(res, f"{tag}.json"), "w"), indent=1)
    s.settings.file.write_case_data(file_name=os.path.join(HERE, f"hotend_{tag}.cas.h5"))
    if with_images:      # picture export has stalled inside long background runs; batch runs export afterwards
        images(s, tag, t_amb_c)
    return b


V_RANGE = (0.0, 8.0)                                   # m/s, same scale for every design


def add_legend(png, vmin, vmax, label):
    """Fluent ignores the legend font size in saved pictures, so its legend is hidden and this large one is
    attached instead, drawn with Fluent's own colour scale (sampled into fluent_colormap.json)."""
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, Normalize
    from PIL import Image
    cmap = ListedColormap([[c / 255 for c in rgb] for rgb in json.load(open(os.path.join(HERE, "fluent_colormap.json")))])
    im = Image.open(png).convert("RGB")
    h = im.size[1]
    fig = plt.figure(figsize=(2.0, h / 100), dpi=100)
    ax = fig.add_axes([0.12, 0.08, 0.18, 0.84])
    cb = fig.colorbar(plt.cm.ScalarMappable(Normalize(vmin, vmax), cmap), cax=ax)
    cb.ax.tick_params(labelsize=17)
    cb.set_label(label, fontsize=19)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor="white")
    plt.close(fig)
    leg = Image.open(buf).convert("RGB")
    out = Image.new("RGB", (im.size[0] + leg.size[0], h), "white")
    out.paste(im, (0, 0)); out.paste(leg, (im.size[0], 0))
    out.save(png)


def images(s, tag, t_amb_c=45.0):
    """Standard pictures with fixed ranges and a large °C / m/s legend."""
    g = s.settings.results.graphics
    cam = s.tui.display.views.camera
    out = os.path.join(HERE, "results", tag)
    os.makedirs(out, exist_ok=True)
    srf = s.settings.results.surfaces.plane_surface
    for name, method, key, val in (("plane_ym6", "zx-plane", "y", -0.006), ("plane_x0", "yz-plane", "x", 0.0)):
        if name not in srf.keys():
            srf.create(name)
            srf[name] = {"method": method, key: val}
    pic = g.picture
    pic.use_window_resolution = False
    pic.x_resolution, pic.y_resolution = 1000, 700

    def shot(name, field, surfaces, rng_si, pos, target, fname, width, height, legend):
        if name not in g.contour.keys():
            g.contour.create(name)
        c = g.contour[name]
        c.field, c.surfaces_list = field, surfaces
        c.range_option = {"option": "auto-range-off",          # range is always given in SI (K, m/s)
                          "auto_range_off": {"minimum": rng_si[0], "maximum": rng_si[1], "clip_to_range": False}}
        c.color_map = {"visible": False}
        c.display()
        cam.position(*pos); cam.target(*target); cam.up_vector(0, 0, 1); cam.field(width, height)
        path = os.path.join(out, fname)
        pic.save_picture(file_name=path)
        add_legend(path, *legend)
        print("saved", fname)

    t_si = (t_amb_c + 273.15, t_amb_c + 15 + 273.15)    # 45–60 °C: resolves the 50 °C limit; nozzle saturates
    t_leg = (t_amb_c, t_amb_c + 15, "Temperature (°C)")
    v_leg = (*V_RANGE, "Velocity (m/s)")
    fins_cam = ((0.01, -0.3, 0.035), (0.01, -0.006, 0.035), 0.09, 0.06)
    shot("t_ym6", "temperature", ["plane_ym6"], t_si, *fins_cam[:2], "temp_section_fins.png", *fins_cam[2:], t_leg)
    shot("vmag_ym6", "velocity-magnitude", ["plane_ym6"], V_RANGE, *fins_cam[:2], "velocity_section_fins.png",
         *fins_cam[2:], v_leg)
    walls = [n for n in s.settings.setup.boundary_conditions.wall.keys()
             if n.startswith("air_main-") and not n.endswith("-shadow") and
             any(z in n for z in ("heatsink", "heatbreak", "nozzlebody"))]
    shot("t_solids", "temperature", walls, t_si, (-0.09, -0.12, 0.09), (0.0, 0.0, 0.03), "temp_solids_iso.png",
         0.07, 0.06, t_leg)
    shot("t_x0", "temperature", ["plane_x0"], t_si, (0.3, 0.0, 0.035), (0.0, 0.0, 0.035), "temp_section_x0.png",
         0.075, 0.055, t_leg)
    print("images saved:", out)
