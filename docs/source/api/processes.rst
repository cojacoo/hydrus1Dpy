Processes Module
================

The processes module contains boundary conditions and evapotranspiration calculations.

Boundary Conditions
-------------------

Base Class
~~~~~~~~~~

.. autoclass:: hydrus1dpy.BoundaryCondition
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Constant Head BC
~~~~~~~~~~~~~~~~

.. autoclass:: hydrus1dpy.ConstantHeadBC
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   **Examples:**

   .. code-block:: python

      # Constant head at surface
      bc = ConstantHeadBC('top', head=-100.0)

      # Time-varying head
      bc = ConstantHeadBC('bottom', head=lambda t: -50 * (1 + 0.1*np.sin(2*np.pi*t)))

Constant Flux BC
~~~~~~~~~~~~~~~~

.. autoclass:: hydrus1dpy.ConstantFluxBC
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   **Examples:**

   .. code-block:: python

      # Constant infiltration
      bc = ConstantFluxBC('top', flux=0.5)  # 0.5 cm/day

      # Time-varying evaporation
      bc = ConstantFluxBC('top', flux=lambda t: -0.3 * np.sin(2*np.pi*t/365))

Free Drainage BC
~~~~~~~~~~~~~~~~

.. autoclass:: hydrus1dpy.FreeDrainageBC
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   **Examples:**

   .. code-block:: python

      # Typical bottom boundary
      bc = FreeDrainageBC('bottom')

Atmospheric BC
~~~~~~~~~~~~~~

.. autoclass:: hydrus1dpy.AtmosphericBC
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   **Examples:**

   .. code-block:: python

      # Simple atmospheric BC
      def atm_flux(t):
          return 0.5 * np.sin(2*np.pi*t/365)  # Seasonal pattern

      bc = AtmosphericBC('top', flux=atm_flux, h_min=-15000, h_surface=0.0)

Enhanced Atmospheric BC
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: hydrus1dpy.EnhancedAtmosphericBC
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   **Features:**

   * Penman-Monteith or simple ET calculation
   * Stage 1/2 evaporation (switches at pF 4.5)
   * Infiltration as thin water film
   * Surface runoff tracking

   **Examples:**

   .. code-block:: python

      # Simple ET with rainfall
      def precip(t):
          if t % 7 < 0.5:  # Rain every 7 days
              return 20.0  # mm/day
          return 0.0

      bc = EnhancedAtmosphericBC(
          'top',
          precipitation=precip,
          et_method='simple',
          et_default=4.0  # mm/day
      )

      # Penman-Monteith ET
      def get_weather(t):
          return WeatherData(
              time=t,
              temperature=20.0,
              relative_humidity=60.0,
              wind_speed=2.0,
              solar_radiation=15.0
          )

      bc = EnhancedAtmosphericBC(
          'top',
          et_method='penman_monteith',
          weather_func=get_weather,
          latitude=52.0,
          elevation=100.0
      )

Evapotranspiration
------------------

Weather Data
~~~~~~~~~~~~

.. autoclass:: hydrus1dpy.WeatherData
   :members:
   :undoc-members:
   :show-inheritance:

   **Example:**

   .. code-block:: python

      from hydrus1dpy import WeatherData

      weather = WeatherData(
          time=180.0,             # Day of year
          temperature=20.0,       # °C
          relative_humidity=60.0, # %
          wind_speed=2.0,         # m/s
          solar_radiation=15.0    # MJ/m²/day
      )

Penman-Monteith ET
~~~~~~~~~~~~~~~~~~

.. autoclass:: hydrus1dpy.PenmanMonteith
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   **FAO-56 Penman-Monteith Equation:**

   .. math::

      ET_0 = \\frac{0.408 \\Delta(R_n - G) + \\gamma\\frac{900}{T+273}u_2(e_s - e_a)}{\\Delta + \\gamma(1 + 0.34u_2)}

   Where:

   * :math:`\\Delta` = slope of saturation vapor pressure curve [kPa/°C]
   * :math:`R_n` = net radiation [MJ/m²/day]
   * :math:`G` = soil heat flux [MJ/m²/day]
   * :math:`\\gamma` = psychrometric constant [kPa/°C]
   * :math:`T` = air temperature [°C]
   * :math:`u_2` = wind speed at 2m [m/s]
   * :math:`e_s` = saturation vapor pressure [kPa]
   * :math:`e_a` = actual vapor pressure [kPa]

   **Example:**

   .. code-block:: python

      from hydrus1dpy import PenmanMonteith, WeatherData

      pm = PenmanMonteith(latitude=52.0, elevation=100.0)
      weather = WeatherData(0, 20.0, 60.0, 2.0, 15.0)
      et0 = pm.calculate_et0(weather)
      print(f"ET₀ = {et0:.2f} mm/day")

Simple ET
~~~~~~~~~

.. autoclass:: hydrus1dpy.SimpleET
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

ET Calculator
~~~~~~~~~~~~~

.. autoclass:: hydrus1dpy.ETCalculator
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Utility Functions
~~~~~~~~~~~~~~~~~

.. autofunction:: hydrus1dpy.pf_to_head

   Convert pF value to pressure head.

   **Example:**

   .. code-block:: python

      from hydrus1dpy import pf_to_head

      h_wilting = pf_to_head(4.2)  # Wilting point
      h_stage2 = pf_to_head(4.5)   # Stage 2 evaporation

.. autofunction:: hydrus1dpy.head_to_pf

   Convert pressure head to pF value.

   **Example:**

   .. code-block:: python

      from hydrus1dpy import head_to_pf

      pf = head_to_pf(-15849)  # pF = 4.2
