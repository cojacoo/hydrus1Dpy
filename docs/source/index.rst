HYDRUS1DPy Documentation
========================

.. image:: https://img.shields.io/badge/python-3.9+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python Version

.. image:: https://img.shields.io/badge/license-MIT-green.svg
   :target: https://github.com/cojacoo/hydrus1Dpy/blob/main/LICENSE
   :alt: License

**HYDRUS1DPy** is a comprehensive Python implementation of the HYDRUS-1D hydrological model
for simulating one-dimensional variably saturated water flow in soils.

Features
--------

* **Richards Equation Solver**: Robust numerical solution with Picard iteration
* **Multiple Hydraulic Models**: van Genuchten, Brooks-Corey, and custom models
* **Flexible Boundary Conditions**: Constant head/flux, atmospheric, free drainage
* **Enhanced Atmospheric BC**: Penman-Monteith ET, stage 1/2 evaporation
* **Modern Data Handling**: xarray integration for labeled multi-dimensional data
* **Interactive Visualization**: Jupyter notebooks with spatiotemporal plots
* **HYDRUS-1D Compatible**: Read/write native HYDRUS-1D files

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   cd phase3
   pip install -r requirements.txt

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from hydrus1dpy import HydrusModel
   from hydrus1dpy.materials import VanGenuchten

   # Create soil model
   soil = VanGenuchten(
       theta_r=0.078,
       theta_s=0.430,
       alpha=0.036,
       n=1.56,
       Ks=24.96
   )

   # Setup and run simulation
   model = HydrusModel(depth=100.0, n_nodes=51, material=soil)
   model.set_top_bc('flux', flux=0.5)
   model.set_bottom_bc('free_drainage')
   model.set_initial_conditions('hydrostatic', h_bottom=-200)

   results = model.run(t_end=10.0, dt_init=0.01, dt_max=0.1)

   # Convert to xarray for easy analysis
   ds = model.to_xarray()
   ds.theta.plot(x='time', y='depth')

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   tutorials/installation
   tutorials/quickstart
   tutorials/atmospheric_bc
   tutorials/visualization
   guides/discretization
   guides/boundary_conditions
   guides/soil_models

.. toctree::
   :maxdepth: 2
   :caption: Examples

   examples/simple_infiltration
   examples/atmospheric_bc
   examples/xarray_usage
   examples/convergence_analysis

.. toctree::
   :maxdepth: 3
   :caption: API Reference

   api/core
   api/processes
   api/materials
   api/numerics
   api/io
   api/visualization
   api/utils

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
   changelog
   license

Project Phases
--------------

The project is organized in three phases:

**Phase 1**: HYDRUS-1D File I/O
   Read and write native HYDRUS-1D input/output files

**Phase 2**: Hydraulic Models
   Soil hydraulic property models (van Genuchten, Brooks-Corey, etc.)

**Phase 3**: Richards Equation Solver
   Full numerical implementation with advanced boundary conditions

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
