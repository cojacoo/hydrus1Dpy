Utilities Module
================

The utilities module provides helper functions and configuration builders.

Helper Functions
----------------

.. autofunction:: hydrus1dpy.create_example_configuration

.. autofunction:: hydrus1dpy.create_infiltration_scenario

.. autofunction:: hydrus1dpy.create_layered_soil

.. autofunction:: hydrus1dpy.get_soil_parameters

Fortran Runner
--------------

.. autoclass:: hydrus1dpy.FortranRunner
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   **Example:**

   .. code-block:: python

      from hydrus1dpy import FortranRunner

      # Run HYDRUS-1D executable
      runner = FortranRunner(working_dir='./simulation')
      runner.run()
