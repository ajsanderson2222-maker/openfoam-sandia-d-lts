#!/usr/bin/env python3
"""Temperature contour from binary OpenFOAM cell-centre fields at t=5000."""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as mtri

ROOT   = Path(__file__).resolve().parents[1]
CASE   = ROOT / "case/sandiaD_LTS"
T5000  = CASE / "5000"
IMG    = ROOT / "images/temperature_contour.png"
D      = 0.0072   # nozzle diameter [m]


def read_of_binary_scalar(path: Path) -> np.ndarray:
    raw = path.read_bytes()
    m = re.search(rb"internalField\s+nonuniform List<scalar>\s+(\d+)\s*\(", raw)
    if m is None:
        raise ValueError(f"could not find internalField in {path}")
    n = int(m.group(1))
    start = m.end()
    return np.frombuffer(raw[start: start + n * 8], dtype="<f8").copy()


def main() -> None:
    cx = read_of_binary_scalar(T5000 / "Ccx")   # radial [m]
    cz = read_of_binary_scalar(T5000 / "Ccz")   # axial  [m]
    T  = read_of_binary_scalar(T5000 / "T")

    # convert to x/D, z/D
    xD = cx / D
    zD = cz / D

    # build Delaunay triangulation of cell centres in the r-z plane
    triang = mtri.Triangulation(xD, zD)

    # remove very long triangles (boundary artefacts at large r)
    xm = xD[triang.triangles].mean(axis=1)
    zm = zD[triang.triangles].mean(axis=1)
    mask = (xm > 18) | (zm < 0)           # outside flame region of interest
    triang.set_mask(mask)

    levels = np.linspace(300, 2200, 32)

    fig, ax = plt.subplots(figsize=(5, 10), constrained_layout=True)
    cf = ax.tricontourf(triang, T, levels=levels, cmap="inferno", extend="both")
    ax.tricontour(triang, T, levels=[1000, 1500, 1800, 2000],
                  colors="white", linewidths=0.5, alpha=0.6)
    cb = fig.colorbar(cf, ax=ax, label="T [K]", pad=0.02)
    cb.set_ticks([300, 500, 1000, 1500, 2000, 2200])

    ax.set_xlabel("r/D")
    ax.set_ylabel("x/D")
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 70)
    ax.set_title("Sandia D — temperature  (t = 5000)", fontsize=11)

    # mark nozzle and pilot extents
    ax.axhline(0, color="white", lw=0.8, ls="--", alpha=0.5)
    ax.axvline(0.5, color="cyan", lw=0.6, ls=":", alpha=0.6, label="nozzle lip r/D=0.5")
    ax.axvline(9.1 / 7.2, color="cyan", lw=0.6, ls="--", alpha=0.6, label="pilot lip r/D=1.26")
    ax.legend(fontsize=7, frameon=False, loc="upper right")

    IMG.parent.mkdir(exist_ok=True)
    fig.savefig(IMG, dpi=200)
    print(f"wrote {IMG}")


if __name__ == "__main__":
    main()
