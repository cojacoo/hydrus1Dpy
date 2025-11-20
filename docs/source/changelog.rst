Changelog
=========

All notable changes to HYDRUS1DPy are documented here.

Version 1.0.0 (2025-11-20)
--------------------------

Phase 3: Richards Equation Solver
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**New Features:**

* Complete Richards equation solver with Picard iteration
* Adaptive time stepping
* Multiple boundary condition types
* Enhanced atmospheric BC with Penman-Monteith ET
* Stage 1/2 evaporation (pF 4.5 threshold)
* xarray integration for modern data handling
* Interactive Jupyter notebooks
* Spatiotemporal visualization
* Comprehensive test suite
* Full documentation with ReadTheDocs

**Boundary Conditions:**

* Constant Head (Dirichlet)
* Constant Flux (Neumann)
* Free Drainage
* Atmospheric BC
* Enhanced Atmospheric BC with:

  * Penman-Monteith ET calculation
  * Simple ET fallback
  * Stage 1/2 evaporation
  * Infiltration with ponding
  * Surface runoff tracking

**Visualization:**

* xarray Dataset output
* Spatiotemporal heatmaps
* Profile and time series plots
* Mass balance analysis
* NetCDF file export

**Documentation:**

* Complete API reference
* User guides and tutorials
* Examples
* Discretization guidelines
* Atmospheric BC guide

Phase 2: Hydraulic Models
~~~~~~~~~~~~~~~~~~~~~~~~~~

**New Features:**

* van Genuchten (1980) model
* Modified van Genuchten
* Brooks-Corey (1964) model
* Dual Porosity model
* Log-Normal model
* Custom hydraulic models
* Pedotransfer functions
* Standard soil parameters (Carsel & Parrish, 1988)

Phase 1: File I/O
~~~~~~~~~~~~~~~~~

**New Features:**

* Read HYDRUS-1D input files
* Write HYDRUS-1D input files
* Parse HYDRUS-1D output files
* Data structure classes
* Configuration builders
* Fortran runner interface

Known Issues
------------

* Numba requires NumPy < 2.0
* Jupyter notebooks may have version conflicts
* Stage 2 evaporation validation test pending

Planned Features
----------------

* Root water uptake
* Heat transport
* Solute transport
* 2D/3D extensions
* GUI interface
* Cloud deployment

Contributors
------------

* HYDRUS1DPy Development Team
* Community contributors

License
-------

MIT License - see LICENSE file for details.
