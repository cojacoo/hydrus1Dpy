"""
Enhanced Atmospheric Boundary Condition Demo
=============================================

Demonstrates realistic atmospheric BC with:
- Penman-Monteith ET calculation
- Stage 1/2 evaporation
- Infiltration with ponding
- Surface runoff

This example shows how the enhanced atmospheric BC handles
evaporation and infiltration more realistically than simple flux BC.
"""

import numpy as np
import sys
from pathlib import Path

# Add packages to path
phase3_path = str(Path(__file__).parent.parent)
phase2_path = str(Path(__file__).parent.parent.parent / 'phase2')
sys.path.insert(0, phase2_path)
sys.path.insert(0, phase3_path)

from hydrus1dpy import HydrusModel
from hydrus1dpy.materials import VanGenuchten
from hydrus1dpy.processes.boundary_conditions import EnhancedAtmosphericBC
from hydrus1dpy.processes.evapotranspiration import WeatherData


def create_weather_generator_simple():
    """Create simple synthetic weather time series."""
    def weather_func(t):
        """
        Simple sinusoidal weather pattern.

        Parameters:
        - Temperature: 15°C + 10°C seasonal + 5°C diurnal
        - RH: 60% average
        - Wind: 2 m/s average
        - Solar radiation: seasonal variation
        """
        day_of_year = t % 365

        temperature = 15.0 + 10.0 * np.sin(2 * np.pi * day_of_year / 365)
        relative_humidity = 60.0 + 20.0 * np.sin(2 * np.pi * day_of_year / 365 + np.pi / 2)
        wind_speed = 2.0 + 1.0 * np.sin(2 * np.pi * day_of_year / 365)
        solar_radiation = 15.0 + 10.0 * np.sin(2 * np.pi * day_of_year / 365)

        return WeatherData(
            time=t,
            temperature=temperature,
            relative_humidity=relative_humidity,
            wind_speed=wind_speed,
            solar_radiation=solar_radiation
        )

    return weather_func


def create_precipitation_events():
    """Create realistic precipitation time series with events."""
    def precip_func(t):
        """
        Precipitation events: 10 mm rain every 7 days lasting 0.5 days.
        """
        # Rain events every 7 days
        t_in_week = t % 7
        if t_in_week < 0.5:  # Rain for first half day of week
            return 20.0  # mm/day (high rate during event)
        else:
            return 0.0  # No rain

    return precip_func


def main():
    print("\n" + "=" * 70)
    print("HYDRUS1D Phase 3: Enhanced Atmospheric Boundary Condition Demo")
    print("=" * 70 + "\n")

    # Create soil material (loam)
    vg_loam = VanGenuchten(
        theta_r=0.078,
        theta_s=0.430,
        alpha=0.036,
        n=1.56,
        Ks=24.96,
        l=0.5
    )

    print("Soil Properties (Loam):")
    print(f"  θr = {vg_loam.theta_r:.3f}")
    print(f"  θs = {vg_loam.theta_s:.3f}")
    print(f"  Ks = {vg_loam.Ks:.2f} cm/day")
    print()

    # =========================================================================
    # SCENARIO 1: Simple ET (constant 4 mm/day) with rainfall events
    # =========================================================================
    print("=" * 70)
    print("SCENARIO 1: Simple ET with Rainfall Events")
    print("=" * 70)
    print()

    model1 = HydrusModel(
        depth=100.0,
        n_nodes=51,
        material=vg_loam
    )

    # Create enhanced atmospheric BC with simple ET
    precip_func = create_precipitation_events()
    bc_atm1 = EnhancedAtmosphericBC(
        location='top',
        precipitation=precip_func,
        et_method='simple',
        et_default=4.0,  # mm/day
        h_ponding=0.05,  # Small positive head for infiltration (0.5 mm film)
        h_stage2=None    # Use default pF 4.5
    )

    model1.bc_top = bc_atm1
    model1.set_bottom_bc('free_drainage')
    model1.set_initial_conditions('hydrostatic', h_bottom=-200)

    print("Setup:")
    print(f"  ET method: Simple (4 mm/day)")
    print(f"  Precipitation: 20 mm/day events every 7 days (0.5 day duration)")
    print(f"  Total simulation: 30 days")
    print(f"  Infiltration: Ponding with h = {bc_atm1.h_ponding} cm")
    print(f"  Stage 2 ET threshold: pF = {bc_atm1.get_diagnostics()['pf_stage2_threshold']:.1f}")
    print()

    print("Running simulation...")
    results1 = model1.run(
        t_end=30.0,
        dt_init=0.001,
        dt_min=1e-6,
        dt_max=0.1,
        verbose=False
    )

    # Print results
    print("\n" + "-" * 70)
    print("Results:")
    print("-" * 70)

    diag1 = bc_atm1.get_diagnostics()
    print(f"\nBoundary Condition Statistics:")
    print(f"  Current BC type: {diag1['current_type']}")
    print(f"  Current ET stage: {diag1['et_stage']}")
    print(f"  Switches to flux BC: {diag1['n_switches_to_flux']}")
    print(f"  Switches to infiltration: {diag1['n_switches_to_infiltration']}")
    print(f"  Switches to stage 2 ET: {diag1['n_switches_to_stage2_et']}")
    print(f"  Cumulative runoff: {diag1['cumulative_runoff']:.2f} cm")

    # Mass balance
    mb1 = results1['mass_balance']
    print(f"\nMass Balance:")
    print(f"  Water in (top): {mb1['flux_top'][-1]:.2f} cm")
    print(f"  Water out (bottom): {-mb1['flux_bottom'][-1]:.2f} cm")
    print(f"  Storage change: {mb1['storage'][-1] - mb1['storage'][0]:.2f} cm")
    print(f"  Error: {mb1['error'][-1]:.4f} cm")

    # Water content changes
    theta1_init = results1['theta'][0]
    theta1_final = results1['theta'][-1]
    print(f"\nWater Content Changes:")
    print(f"  Surface: {theta1_init[0]:.3f} → {theta1_final[0]:.3f} (Δ = {theta1_final[0]-theta1_init[0]:+.3f})")
    print(f"  Middle:  {theta1_init[25]:.3f} → {theta1_final[25]:.3f} (Δ = {theta1_final[25]-theta1_init[25]:+.3f})")
    print(f"  Bottom:  {theta1_init[-1]:.3f} → {theta1_final[-1]:.3f} (Δ = {theta1_final[-1]-theta1_init[-1]:+.3f})")

    # =========================================================================
    # SCENARIO 2: Penman-Monteith ET with seasonal variation
    # =========================================================================
    print("\n\n" + "=" * 70)
    print("SCENARIO 2: Penman-Monteith ET (Seasonal Variation)")
    print("=" * 70)
    print()

    model2 = HydrusModel(
        depth=100.0,
        n_nodes=51,
        material=vg_loam
    )

    # Create weather generator
    weather_func = create_weather_generator_simple()

    # Create enhanced atmospheric BC with Penman-Monteith
    bc_atm2 = EnhancedAtmosphericBC(
        location='top',
        precipitation=0.0,  # No rain in this scenario (pure evaporation)
        et_method='penman_monteith',
        weather_func=weather_func,
        latitude=52.0,  # Northern Europe
        elevation=100.0,  # m
        h_ponding=0.05
    )

    model2.bc_top = bc_atm2
    model2.set_bottom_bc('free_drainage')
    model2.set_initial_conditions('uniform', h=-50)  # Start wetter

    print("Setup:")
    print(f"  ET method: Penman-Monteith")
    print(f"  Latitude: 52° N")
    print(f"  Elevation: 100 m")
    print(f"  Weather: Sinusoidal seasonal pattern")
    print(f"  Precipitation: None (pure evaporation test)")
    print(f"  Total simulation: 60 days")
    print()

    # Sample weather data
    sample_weather = weather_func(0)
    print("Sample Weather Data (t=0):")
    print(f"  Temperature: {sample_weather.temperature:.1f}°C")
    print(f"  RH: {sample_weather.relative_humidity:.0f}%")
    print(f"  Wind: {sample_weather.wind_speed:.1f} m/s")
    print(f"  Solar radiation: {sample_weather.solar_radiation:.1f} MJ/m²/day")
    print()

    print("Running simulation...")
    results2 = model2.run(
        t_end=60.0,
        dt_init=0.001,
        dt_min=1e-6,
        dt_max=0.1,
        verbose=False
    )

    # Print results
    print("\n" + "-" * 70)
    print("Results:")
    print("-" * 70)

    diag2 = bc_atm2.get_diagnostics()
    print(f"\nBoundary Condition Statistics:")
    print(f"  Final BC type: {diag2['current_type']}")
    print(f"  Final ET stage: {diag2['et_stage']}")
    print(f"  Switches to stage 2 ET: {diag2['n_switches_to_stage2_et']}")

    # Mass balance
    mb2 = results2['mass_balance']
    total_et = -mb2['flux_top'][-1]
    print(f"\nMass Balance:")
    print(f"  Total ET: {total_et:.2f} cm ({total_et*10:.1f} mm)")
    print(f"  Average ET: {total_et/60*10:.2f} mm/day")
    print(f"  Storage change: {mb2['storage'][-1] - mb2['storage'][0]:.2f} cm")

    # Surface drying
    h2_init = results2['h'][0, 0]
    h2_final = results2['h'][-1, 0]
    print(f"\nSurface Drying:")
    print(f"  Initial h: {h2_init:.1f} cm")
    print(f"  Final h: {h2_final:.1f} cm")
    print(f"  Stage 2 threshold: {diag2['h_stage2_threshold']:.1f} cm (pF {diag2['pf_stage2_threshold']:.1f})")
    if h2_final < diag2['h_stage2_threshold']:
        print(f"  ✓ Surface reached stage 2 evaporation (soil-limited)")
    else:
        print(f"  Surface still in stage 1 evaporation (potential ET)")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n\n" + "=" * 70)
    print("SUMMARY: Key Features Demonstrated")
    print("=" * 70)
    print()

    print("1. EVAPOTRANSPIRATION:")
    print("   - Simple ET: Constant rate (4 mm/day)")
    print("   - Penman-Monteith: Weather-based ET calculation")
    print("   - Stage 1: Potential ET (flux-controlled)")
    print("   - Stage 2: Soil-limited ET (when surface dries to pF 4.5)")
    print()

    print("2. INFILTRATION:")
    print("   - Modeled as thin water film (h = +0.05 cm)")
    print("   - Richards equation determines actual infiltration rate")
    print("   - More realistic than prescribed flux")
    print("   - Automatically handles infiltration capacity")
    print()

    print("3. AUTOMATIC BC SWITCHING:")
    print("   - Flux BC for evaporation (stage 1)")
    print("   - Head BC for infiltration (ponding)")
    print("   - Head BC for stage 2 evaporation (dry surface)")
    print("   - Tracks switches and diagnostics")
    print()

    print("4. PHYSICAL REALISM:")
    print("   - pF 4.5 threshold for stage 2 evaporation")
    print("   - Ponding depth limited (with runoff tracking)")
    print("   - Weather-based ET when data available")
    print("   - Sensible fallback to simple ET when no weather data")
    print()

    print("=" * 70)
    print("Demo completed successfully!")
    print("=" * 70 + "\n")

    return results1, results2


if __name__ == '__main__':
    results1, results2 = main()
