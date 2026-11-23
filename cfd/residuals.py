"""Residual histories parsed from Fluent's iteration printout in solve logs -> one small-multiples figure.
Usage: python residuals.py out.png log1:tag1[:title1] [log2:tag2[:title2] ...]
A log may hold several runs separated by '===== RUN <tag>' lines; tag picks one (or '*' = whole file)."""
import re, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROW = re.compile(r"^\s*(\d+)((?:\s+\d\.\d+e[+-]\d+)+)\s+\d+:\d+:\d+\s+\d+\s*$")
HEAD = re.compile(r"^\s*iter\s+continuity")
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]   # fixed order


def parse(path, tag):
    text = open(path, encoding="utf-8", errors="ignore").read().replace("\x00", "")
    if tag != "*":
        parts = re.split(r"===== RUN (\S+)", text)
        text = dict(zip(parts[1::2], parts[2::2])).get(tag, "")
    names, rows = None, {}
    for line in text.splitlines():
        if HEAD.match(line):
            names = line.split()[1:-1]                 # drop 'iter' and 'time/iter'
            continue
        m = ROW.match(line)
        if m and names:
            vals = [float(x) for x in m.group(2).split()]
            rows[int(m.group(1))] = dict(zip(names, vals))   # last print of an iteration wins
    its = sorted(rows)
    assert its, f"no residual rows for {tag} in {path}"
    return its, {n: [rows[i].get(n) for i in its] for n in names}


def main():
    out, specs = sys.argv[1], sys.argv[2:]
    fig, axes = plt.subplots(1, len(specs), figsize=(4.6 * len(specs), 3.6), dpi=170, sharey=True, squeeze=False)
    for ax, spec in zip(axes[0], specs):
        path, tag, *title = spec.split(":")
        its, res = parse(path, tag)
        for color, (name, vals) in zip(PALETTE, res.items()):
            ax.semilogy(its, vals, color=color, linewidth=1.6, label=name)
        ax.set_title(title[0] if title else tag, fontsize=11, loc="left")
        ax.set_xlabel("Iteration")
        ax.grid(True, color="#e4e3df", linewidth=0.8)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        print(f"{tag}: iterations {its[0]}-{its[-1]}, final", {k: f"{v[-1]:.1e}" for k, v in res.items()})
    axes[0][0].set_ylabel("Scaled residual")
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=len(labels), fontsize=9, frameon=False)
    fig.tight_layout(rect=(0, 0.08, 1, 1))              # room for the shared legend below the panels
    fig.savefig(out, facecolor="white")
    print("saved", out)


if __name__ == "__main__":
    main()
