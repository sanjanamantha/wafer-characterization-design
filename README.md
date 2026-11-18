# wafer-characterization-design

# Wafer Characterization Design

Python-based wafer-scale microfabrication characterization layout developed during my research experience at Stanford.

## Project Overview

This project explores the design of geometric test structures for microfabrication characterization using Python and KLayout.

The layout consists of a reusable characterization die containing multiple test patterns, which is repeated across a 100 mm wafer.

## Design Features

- **Shape matrix:** Circles, squares, crosses, rings, and meshes across five feature sizes.
- **Line/space arrays:** Patterns with varying line widths and pitches.
- **Trench and square rulers:** Geometric structures with different dimensions.
- **Microloading arrays:** Test patterns with varying feature densities.
- **Alignment markers:** Cross-shaped reference structures.
- **Wafer placement:** Automated die placement using a staggered grid and geometric boundary checks.

## Technologies

- Python
- KLayout (pya)
- GDSII

## My Role

I developed the design requirements, selected geometric parameters, evaluated the generated layouts in KLayout, and refined the designs through iterative troubleshooting. Claude was used to assist with Python implementation.

## Project Files

- `wafer_matrix_design.py` — Python script that generates the characterization layout.

## Future Work

Further validation of the generated layout and analysis of experimental characterization results.
