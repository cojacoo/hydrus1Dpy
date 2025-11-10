"""
Basic Usage Example - HYDRUS1D Python Wrapper Phase 1
======================================================

This example demonstrates:
1. Creating a model configuration from scratch
2. Writing input files
3. (Optional) Running the Fortran engine
4. Parsing and visualizing results
"""

import numpy as np
import sys
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hydrus1dpy import (
    ModelDomain, MaterialProperties, BoundaryCondition,
    TimeControl, InitialConditions, ModelConfiguration,
    Units, ProcessFlags, NumericalParameters
)
from hydrus1dpy.io.input_writer import InputWriter
from hydrus1dpy.utils.helpers import create_example_configuration
from hydrus1dpy.visualization import HydrusVisualizer


def example_1_create_configuration():
    """
    Example 1: Create a simple model configuration manually
    """
    print("=" * 70)
    print("Example 1: Creating Model Configuration")
    print("=" * 70)

    # Define spatial domain
    n_nodes = 101
    profile_depth = 100.0  # cm
    depths = np.linspace(0, -profile_depth, n_nodes)
    materials = np.ones(n_nodes, dtype=int)  # All nodes are material 1

    domain = ModelDomain(
        n_nodes=n_nodes,
        depths=depths,
        materials=materials,
        n_materials=1,
        observation_nodes=[25, 50, 75]  # Observation at 25%, 50%, 75% depth
    )

    print(f"Domain created: {n_nodes} nodes, {profile_depth} cm depth")
    print(f"Observation nodes: {domain.observation_nodes}")

    # Define soil hydraulic properties (Loam soil from Carsel & Parrish, 1988)
    materials_dict = {
        1: MaterialProperties(
            material_id=1,
            model_type=0,  # van Genuchten
            theta_r=0.078,  # Residual water content
            theta_s=0.430,  # Saturated water content
            alpha=0.036,    # Scale parameter [1/cm]
            n=1.56,         # Shape parameter
            Ks=24.96,       # Saturated hydraulic conductivity [cm/day]
            l=0.5           # Pore connectivity parameter
        )
    }

    print(f"\nMaterial properties (Loam soil):")
    mat = materials_dict[1]
    print(f"  θr = {mat.theta_r:.3f}")
    print(f"  θs = {mat.theta_s:.3f}")
    print(f"  α  = {mat.alpha:.4f} cm⁻¹")
    print(f"  n  = {mat.n:.2f}")
    print(f"  Ks = {mat.Ks:.2f} cm/day")
    print(f"  m  = {mat.m:.3f} (calculated)")

    # Define boundary conditions
    bc_top = BoundaryCondition.constant_flux(flux=-5.0)  # 5 cm/day infiltration (negative = downward)
    bc_bottom = BoundaryCondition.free_drainage()         # Free drainage at bottom

    print(f"\nBoundary conditions:")
    print(f"  Top: Constant flux = -5.0 cm/day (infiltration)")
    print(f"  Bottom: Free drainage")

    # Define time control
    time_control = TimeControl(
        t_init=0.0,
        t_max=10.0,        # 10 days simulation
        dt_init=0.001,     # Initial time step
        dt_min=0.00001,    # Minimum time step
        dt_max=0.5,        # Maximum time step
        print_times=np.linspace(0, 10, 21)  # Output at 21 times
    )

    print(f"\nTime control:")
    print(f"  Simulation time: {time_control.t_max} days")
    print(f"  Output times: {len(time_control.print_times)} snapshots")

    # Define initial conditions (hydrostatic equilibrium)
    h_init = depths - depths[0]  # Pressure head profile

    initial_conditions = InitialConditions(h_init=h_init)

    print(f"\nInitial conditions:")
    print(f"  h at surface: {h_init[-1]:.1f} cm")
    print(f"  h at bottom:  {h_init[0]:.1f} cm")

    # Create complete configuration
    config = ModelConfiguration(
        project_name='example_infiltration',
        units=Units(length='cm', time='days'),
        domain=domain,
        materials=materials_dict,
        bc_top=bc_top,
        bc_bottom=bc_bottom,
        time_control=time_control,
        initial_conditions=initial_conditions,
        processes=ProcessFlags(water=True),
        numerical=NumericalParameters(max_iter=10, tol_theta=0.001, tol_h=0.1)
    )

    print(f"\nConfiguration created successfully!")
    print(f"Project name: {config.project_name}")

    return config


def example_2_use_helper():
    """
    Example 2: Create configuration using helper function
    """
    print("\n" + "=" * 70)
    print("Example 2: Using Helper Function")
    print("=" * 70)

    config = create_example_configuration(
        profile_depth=100.0,
        n_nodes=101,
        simulation_time=10.0,
        soil_type='loam'
    )

    print(f"Configuration created with helper function")
    print(f"  Nodes: {config.domain.n_nodes}")
    print(f"  Depth: {config.domain.profile_length} cm")
    print(f"  Soil: Loam")
    print(f"  Simulation time: {config.time_control.t_max} days")

    return config


def example_3_write_input_files(config):
    """
    Example 3: Write Fortran-compatible input files
    """
    print("\n" + "=" * 70)
    print("Example 3: Writing Input Files")
    print("=" * 70)

    output_dir = Path('./example_output')
    output_dir.mkdir(exist_ok=True)

    writer = InputWriter(config, output_dir)
    writer.write_all()

    print(f"Input files written to: {output_dir.absolute()}")
    print(f"Files created:")

    for file in output_dir.glob('*.in'):
        size_kb = file.stat().st_size / 1024
        print(f"  - {file.name:20s} ({size_kb:.1f} KB)")

    for file in output_dir.glob('*.dat'):
        size_kb = file.stat().st_size / 1024
        print(f"  - {file.name:20s} ({size_kb:.1f} KB)")

    return output_dir


def example_4_visualize_config(config):
    """
    Example 4: Visualize configuration
    """
    print("\n" + "=" * 70)
    print("Example 4: Visualizing Configuration")
    print("=" * 70)

    import plotly.graph_objects as go

    # Plot initial pressure head profile
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=config.initial_conditions.h_init,
        y=config.domain.depths,
        mode='lines+markers',
        name='Initial h',
        line=dict(color='blue', width=2),
        marker=dict(size=4)
    ))

    fig.update_layout(
        title='Initial Pressure Head Profile',
        xaxis_title='Pressure Head [cm]',
        yaxis_title='Depth [cm]',
        yaxis=dict(autorange='reversed'),
        template='plotly_white',
        width=600,
        height=500
    )

    # Save figure
    output_file = Path('./example_output/initial_profile.html')
    fig.write_html(output_file)
    print(f"Initial profile plot saved to: {output_file}")

    return fig


def example_5_layered_soil():
    """
    Example 5: Create layered soil profile
    """
    print("\n" + "=" * 70)
    print("Example 5: Layered Soil Profile")
    print("=" * 70)

    from hydrus1dpy.utils.helpers import create_layered_soil

    # Create 3-layer soil profile
    domain, materials = create_layered_soil(
        layer_depths=[0, 30, 60, 100],  # Layer boundaries [cm]
        soil_types=['loam', 'sandy_loam', 'sand'],
        n_nodes=101
    )

    print("Layered soil profile created:")
    print(f"  Layer 1 (0-30 cm):   Loam")
    print(f"  Layer 2 (30-60 cm):  Sandy Loam")
    print(f"  Layer 3 (60-100 cm): Sand")

    # Count nodes in each material
    for mat_id in [1, 2, 3]:
        n_nodes_mat = np.sum(domain.materials == mat_id)
        print(f"  Material {mat_id}: {n_nodes_mat} nodes")

    # Create configuration
    config = ModelConfiguration(
        project_name='layered_soil',
        units=Units(length='cm', time='days'),
        domain=domain,
        materials=materials,
        bc_top=BoundaryCondition.constant_flux(-5.0),
        bc_bottom=BoundaryCondition.free_drainage(),
        time_control=TimeControl(
            t_max=10.0,
            dt_init=0.01,
            dt_min=0.0001,
            dt_max=0.5,
            print_times=np.linspace(0, 10, 21)
        ),
        initial_conditions=InitialConditions(
            h_init=domain.depths - domain.depths[-1]
        )
    )

    return config


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("HYDRUS1D Python Wrapper - Phase 1 Examples")
    print("=" * 70 + "\n")

    # Example 1: Manual configuration
    config1 = example_1_create_configuration()

    # Example 2: Helper function
    config2 = example_2_use_helper()

    # Example 3: Write input files
    output_dir = example_3_write_input_files(config2)

    # Example 4: Visualize configuration
    fig = example_4_visualize_config(config2)

    # Example 5: Layered soil
    config_layered = example_5_layered_soil()
    output_dir_layered = Path('./example_output_layered')
    output_dir_layered.mkdir(exist_ok=True)
    writer = InputWriter(config_layered, output_dir_layered)
    writer.write_all()
    print(f"\nLayered soil input files written to: {output_dir_layered}")

    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Compile Fortran code (if not already done)")
    print("  2. Run HYDRUS1D with generated input files")
    print("  3. Use OutputParser to read results")
    print("  4. Use HydrusVisualizer to create plots")
    print("\nSee the README.md for more information.")


if __name__ == '__main__':
    main()
