# Sandia D Flame

## Tutorial Baseline

This repository starts from the installed OpenFOAM `reactingFoam` RAS tutorial for the Sandia D flame:

- `case/sandiaD_LTS/`

The tutorial case is the source of truth for the baseline setup. It includes the chemistry, combustion, mesh, and solver files needed to run the standard Sandia D benchmark.

## What is in the repo

- `case/`: the copied tutorial case
- `scripts/`: place for run helpers, post-processing, and plotting
- `studies/`: place for future parameter sweeps and comparison runs
- `images/`: plots and figures for the writeup
- `docs/`: notes on the setup and future changes

## Why this case

Sandia D is a standard turbulent reacting-flow benchmark. It is useful for showing a transition from external-aero style work into reacting-flow physics with a classic dataset and well-known comparison points.

The initial focus here is to preserve the tutorial structure cleanly, document the baseline, and then build up the post-processing and comparison workflow around it.

## Next steps

The next useful additions are:

1. A baseline run script and convergence checks.
2. Sample extraction for centerline species, temperature, and mixture fraction.
3. Comparison plots against the classic Sandia D reference quantities.
