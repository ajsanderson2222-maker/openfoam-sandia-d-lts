#!/usr/bin/env python3
"""Centerline and radial profile comparison against TNF Sandia D reference data."""

from __future__ import annotations

import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "case/sandiaD_LTS"
SAMPLE_DIR = CASE / "postProcessing/sampleDict/5000"
PMCDEF_ZIP = ROOT / ".tmp/sandia_ref/pmCDEF.zip"
TUD_ZIP    = ROOT / ".tmp/sandia_ref/TUD_LDV_DEF.zip"
IMG_DIR    = ROOT / "images"
D = 0.0072  # nozzle diameter [m]

# --- column indices in sample .xy files ---
# z/x  U_x  U_y  U_z  T  CH4  O2  CO2  H2O  CO  OH  H2  N2
SIM = dict(coord=0, Ux=1, Uy=2, Uz=3, T=4,
           CH4=5, O2=6, CO2=7, H2O=8, CO=9, OH=10, H2=11, N2=12)

# --- column indices in pmD.stat *.Yave files ---
# r/d  F  Frms  T  Trms  YO2  YO2rms  YN2  YN2rms  YH2  YH2rms
#  YH2O  YH2Orms  YCH4  YCH4rms  YCO  YCOrms  YCO2  YCO2rms  YOH ...
REF = dict(rd=0, T=3, O2=5, CH4=13, CO=15, CO2=17, H2O=11, OH=19)


def load_sample(name: str) -> np.ndarray:
    p = SAMPLE_DIR / name
    return np.loadtxt(p, comments="#")


def load_yave(zip_path: Path, member: str) -> np.ndarray:
    with zipfile.ZipFile(zip_path) as z:
        text = z.read(member).decode(errors="replace")
    rows = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s[0].isalpha() or s.startswith("#"):
            continue
        try:
            rows.append([float(v) for v in s.split()])
        except ValueError:
            continue
    return np.array(rows)


def load_tud(zip_path: Path, member: str) -> np.ndarray:
    with zipfile.ZipFile(zip_path) as z:
        text = z.read(member).decode(errors="replace")
    rows = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        try:
            rows.append([float(v) for v in s.split()])
        except ValueError:
            continue
    return np.array(rows)


# ── centerline plots ──────────────────────────────────────────────────────────

def plot_centerline() -> None:
    sim = load_sample("centerline.xy")
    xD_sim = sim[:, SIM["coord"]] / D

    ref_cl  = load_yave(PMCDEF_ZIP, "pmCDEFarchives/pmD.stat/DCL.Yave")
    ref_vel = load_tud(TUD_ZIP, "TUD_LDV_D.axial")

    quantities = [
        ("T [K]",          SIM["T"],   REF["T"],   None),
        ("Y$_{CH_4}$",     SIM["CH4"], REF["CH4"], None),
        ("Y$_{O_2}$",      SIM["O2"],  REF["O2"],  None),
        ("Y$_{CO_2}$",     SIM["CO2"], REF["CO2"], None),
        ("Y$_{H_2O}$",     SIM["H2O"], REF["H2O"], None),
        ("Y$_{CO}$",       SIM["CO"],  REF["CO"],  None),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(13, 7), constrained_layout=True)
    axes = axes.flatten()

    for ax, (label, sc, rc, _) in zip(axes, quantities):
        ax.plot(xD_sim, sim[:, sc], color="#1f77b4", lw=1.5, label="CFD")
        if ref_cl.size and ref_cl.shape[1] > rc:
            ax.plot(ref_cl[:, REF["rd"]], ref_cl[:, rc],
                    "o", ms=4, color="#d62728", mfc="none", label="Exp (TNF)")
        ax.set_xlabel("x/D")
        ax.set_ylabel(label)
        ax.set_xlim(0, 70)
        ax.grid(True, alpha=0.25)
        ax.legend(frameon=False, fontsize=8)

    # axial velocity panel — replace last subplot
    ax = axes[-1]
    ax.plot(xD_sim, sim[:, SIM["Uz"]], color="#1f77b4", lw=1.5, label="CFD")
    if ref_vel.size:
        ax.plot(ref_vel[:, 0], ref_vel[:, 1],
                "o", ms=4, color="#d62728", mfc="none", label="TUD LDV")
    ax.set_xlabel("x/D")
    ax.set_ylabel("U$_z$ [m/s]")
    ax.set_xlim(0, 70)
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False, fontsize=8)

    fig.suptitle("Sandia D — centerline profiles  (t = 5000)", fontsize=12)
    out = IMG_DIR / "centerline.png"
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out, dpi=200)
    print(f"wrote {out}")


# ── radial profile plots ──────────────────────────────────────────────────────

RADIAL_STATIONS = [
    ("xD15",  "D15.Yave",  "d15",  15),
    ("xD30",  "D30.Yave",  "d30",  30),
    ("xD45",  "D45.Yave",  "d45",  45),
    ("xD60",  "D60.Yave",  "d60",  60),
]

RADIAL_QTY = [
    ("T [K]",      SIM["T"],   REF["T"]),
    ("Y$_{CH_4}$", SIM["CH4"], REF["CH4"]),
    ("Y$_{O_2}$",  SIM["O2"],  REF["O2"]),
    ("Y$_{CO_2}$", SIM["CO2"], REF["CO2"]),
]


def plot_radial() -> None:
    n_sta = len(RADIAL_STATIONS)
    n_qty = len(RADIAL_QTY)
    fig, axes = plt.subplots(n_qty, n_sta,
                             figsize=(3.2 * n_sta, 3 * n_qty),
                             constrained_layout=True)

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

    for col, (tag, yave_name, tud_name, xD) in enumerate(RADIAL_STATIONS):
        sim = load_sample(f"radial_{tag}.xy")
        rD_sim = sim[:, SIM["coord"]] / D

        ref = load_yave(PMCDEF_ZIP, f"pmCDEFarchives/pmD.stat/{yave_name}")

        for row, (label, sc, rc) in enumerate(RADIAL_QTY):
            ax = axes[row, col]
            ax.plot(rD_sim, sim[:, sc], color=colors[row], lw=1.5)
            if ref.size and ref.shape[1] > rc:
                rD_ref = np.abs(ref[:, REF["rd"]])  # ref has ±r/d; take abs
                ax.plot(rD_ref, ref[:, rc],
                        "o", ms=4, color="k", mfc="none")
            ax.set_xlim(0, 20)
            ax.grid(True, alpha=0.25)
            if row == 0:
                ax.set_title(f"x/D = {xD}", fontsize=10)
            if col == 0:
                ax.set_ylabel(label)
            if row == n_qty - 1:
                ax.set_xlabel("r/D")

    fig.suptitle("Sandia D — radial profiles  (t = 5000)\n"
                 "lines: CFD    circles: Exp (TNF)", fontsize=11)
    out = IMG_DIR / "radial_profiles.png"
    fig.savefig(out, dpi=200)
    print(f"wrote {out}")


if __name__ == "__main__":
    plot_centerline()
    plot_radial()
