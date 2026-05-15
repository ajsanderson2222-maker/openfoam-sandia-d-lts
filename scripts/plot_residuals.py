#!/usr/bin/env python3
"""Plot residuals from OpenFOAM postProcessing/residuals/*/residuals.dat."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

CASE = Path(__file__).resolve().parents[1] / "case/sandiaD_LTS"
RESIDUALS_DIR = CASE / "postProcessing/residuals"
OUT = Path(__file__).resolve().parents[1] / "images/residuals.png"

# subplot grouping: (panel title, field names in this panel)
GROUPS = [
    ("Pressure", ["p"]),
    ("Turbulence", ["k", "epsilon"]),
    ("Temperature & Species", ["T", "CH4", "O2", "CO2", "H2O", "CO", "OH"]),
]

COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#17becf",
]


def parse_residuals(path: Path) -> tuple[list[str], dict[str, list[tuple[float, float]]]]:
    """Return (field_names, {field: [(time, value), ...]}) skipping N/A entries."""
    lines = [l.strip() for l in path.read_text().splitlines() if l.strip()]
    header_idx = next(i for i, l in enumerate(lines) if l.startswith("# Time"))
    fields = lines[header_idx].lstrip("#").split()[1:]  # drop "Time"

    series: dict[str, list[tuple[float, float]]] = {f: [] for f in fields}
    for line in lines[header_idx + 1:]:
        if line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != len(fields) + 1:
            continue
        try:
            t = float(parts[0])
        except ValueError:
            continue
        for field, val_str in zip(fields, parts[1:]):
            if val_str == "N/A":
                continue
            try:
                series[field].append((t, float(val_str)))
            except ValueError:
                continue
    return fields, series


def merge_series(
    a: dict[str, list[tuple[float, float]]],
    b: dict[str, list[tuple[float, float]]],
) -> dict[str, list[tuple[float, float]]]:
    out = dict(a)
    for field, pts in b.items():
        out.setdefault(field, [])
        out[field] = out[field] + pts
    return out


def plot(
    series: dict[str, list[tuple[float, float]]],
    chemistry_start: float | None,
    out_path: Path,
) -> None:
    # only render groups that have at least one field with data
    active_groups = [
        (title, [f for f in fields if series.get(f)])
        for title, fields in GROUPS
    ]
    active_groups = [(t, fs) for t, fs in active_groups if fs]

    fig, axes = plt.subplots(
        len(active_groups), 1,
        figsize=(11, 3.5 * len(active_groups)),
        constrained_layout=True,
    )
    if len(active_groups) == 1:
        axes = [axes]

    for ax, (title, fields) in zip(axes, active_groups):
        for i, field in enumerate(fields):
            pts = series[field]
            times = [t for t, _ in pts]
            vals = [v for _, v in pts]
            ax.semilogy(times, vals, color=COLORS[i % len(COLORS)],
                        linewidth=1.2, label=field)

        if chemistry_start is not None:
            ax.axvline(chemistry_start, color="black", linestyle="--",
                       linewidth=0.8, alpha=0.6, label="chemistry on")

        ax.set_title(title)
        ax.set_ylabel("Residual")
        ax.yaxis.set_major_formatter(ticker.LogFormatterMathtext())
        ax.grid(True, which="both", alpha=0.25)
        ax.legend(frameon=False, ncol=4, fontsize=8)

    axes[-1].set_xlabel("Iteration")
    fig.suptitle("Sandia D LTS — solver residuals", fontsize=12)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    print(f"wrote {out_path}")


def find_phase_files(residuals_dir: Path) -> list[tuple[float, Path]]:
    """Return sorted [(start_time, path)] for all residuals.dat files found."""
    found = []
    for dat in sorted(residuals_dir.glob("*/residuals.dat")):
        try:
            t = float(dat.parent.name)
        except ValueError:
            continue
        found.append((t, dat))
    return sorted(found)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot residuals from postProcessing/residuals/*/residuals.dat"
    )
    parser.add_argument(
        "--residuals-dir", type=Path, default=RESIDUALS_DIR,
        help="directory containing timestep sub-dirs with residuals.dat",
    )
    parser.add_argument(
        "--out", type=Path, default=OUT,
        help="output PNG path",
    )
    args = parser.parse_args()

    phases = find_phase_files(args.residuals_dir)
    if not phases:
        raise SystemExit(f"no residuals.dat found under {args.residuals_dir}")

    combined: dict[str, list[tuple[float, float]]] = {}
    chemistry_start: float | None = None

    for i, (start_t, dat) in enumerate(phases):
        print(f"reading {dat}")
        _, series = parse_residuals(dat)
        combined = merge_series(combined, series)
        if i == 1:
            chemistry_start = start_t  # second phase = chemistry on

    plot(combined, chemistry_start, args.out)


if __name__ == "__main__":
    main()
