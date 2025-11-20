Visualization Module
====================

The visualization module provides interactive plotting capabilities.

HydrusVisualizer
----------------

.. autoclass:: hydrus1dpy.HydrusVisualizer
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   **Example:**

   .. code-block:: python

      from hydrus1dpy import HydrusVisualizer

      # Create visualizer from results
      viz = HydrusVisualizer(results)

      # Plot water content profile
      viz.plot_profile(variable='theta', time_index=-1)

      # Plot time series
      viz.plot_timeseries(variable='h', node_index=0)

xarray Integration
------------------

For modern spatiotemporal visualization, convert results to xarray:

.. code-block:: python

   # Convert to xarray Dataset
   ds = model.to_xarray()

   # Built-in plotting
   ds.theta.plot(x='time', y='depth', cmap='Blues')

   # Select and plot
   ds.theta.sel(depth=-50, method='nearest').plot()
   ds.theta.isel(time=-1).plot()

See :doc:`../tutorials/visualization` for detailed examples.
