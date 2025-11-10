"""
Helper Functions
================

Utility functions for creating configurations and common operations
"""

import numpy as np
from typing import Optional

from ..io.data_structures import (
    ModelConfiguration, ModelDomain, MaterialProperties,
    BoundaryCondition, TimeControl, InitialConditions,
    Units, ProcessFlags, NumericalParameters
)


def create_example_configuration(
    profile_depth: float = 100.0,
    n_nodes: int = 101,
    simulation_time: float = 10.0,
    soil_type: str = 'loam'
) -> ModelConfiguration:
    """
    Create an example model configuration for testing

    Parameters
    ----------
    profile_depth : float
        Depth of soil profile [cm]
    n_nodes : int
        Number of nodes
    simulation_time : float
        Total simulation time [days]
    soil_type : str
        Soil type: 'sand', 'loam', 'clay'

    Returns
    -------
    config : ModelConfiguration
        Complete model configuration ready to run
    """
    # Create domain
    depths = np.linspace(0, -profile_depth, n_nodes)  # Surface at 0, bottom negative
    materials = np.ones(n_nodes, dtype=int)  # All material 1

    domain = ModelDomain(
        n_nodes=n_nodes,
        depths=depths,
        materials=materials,
        n_materials=1,
        observation_nodes=[int(n_nodes * 0.25), int(n_nodes * 0.5), int(n_nodes * 0.75)]
    )

    # Get soil hydraulic parameters
    soil_params = get_soil_parameters(soil_type)

    materials = {
        1: MaterialProperties(
            material_id=1,
            **soil_params
        )
    }

    # Boundary conditions
    bc_top = BoundaryCondition.constant_flux(flux=-5.0)  # 5 cm/day infiltration
    bc_bottom = BoundaryCondition.free_drainage()

    # Time control
    time_control = TimeControl(
        t_init=0.0,
        t_max=simulation_time,
        dt_init=0.001,
        dt_min=0.00001,
        dt_max=0.5,
        print_times=np.linspace(0, simulation_time, 21)
    )

    # Initial conditions (hydrostatic from bottom)
    h_init = depths - depths[0]  # Hydrostatic equilibrium

    initial_conditions = InitialConditions(h_init=h_init)

    # Complete configuration
    config = ModelConfiguration(
        project_name='example_simulation',
        units=Units(length='cm', time='days'),
        domain=domain,
        materials=materials,
        bc_top=bc_top,
        bc_bottom=bc_bottom,
        time_control=time_control,
        initial_conditions=initial_conditions,
        processes=ProcessFlags(water=True),
        numerical=NumericalParameters()
    )

    return config


def get_soil_parameters(soil_type: str) -> dict:
    """
    Get typical soil hydraulic parameters

    Parameters
    ----------
    soil_type : str
        Soil texture class

    Returns
    -------
    params : dict
        Dictionary of hydraulic parameters

    Notes
    -----
    Parameters from Carsel and Parrish (1988)
    Water Resources Research, 24(5), 755-769
    """
    # Parameters: theta_r, theta_s, alpha [1/cm], n [-], Ks [cm/day], l [-]
    soil_database = {
        'sand': {
            'theta_r': 0.045,
            'theta_s': 0.430,
            'alpha': 0.145,
            'n': 2.68,
            'Ks': 712.8,  # 29.70 cm/hr * 24
            'l': 0.5
        },
        'loamy_sand': {
            'theta_r': 0.057,
            'theta_s': 0.410,
            'alpha': 0.124,
            'n': 2.28,
            'Ks': 350.2,  # 14.59 cm/hr * 24
            'l': 0.5
        },
        'sandy_loam': {
            'theta_r': 0.065,
            'theta_s': 0.410,
            'alpha': 0.075,
            'n': 1.89,
            'Ks': 106.1,  # 4.42 cm/hr * 24
            'l': 0.5
        },
        'loam': {
            'theta_r': 0.078,
            'theta_s': 0.430,
            'alpha': 0.036,
            'n': 1.56,
            'Ks': 24.96,  # 1.04 cm/hr * 24
            'l': 0.5
        },
        'silt': {
            'theta_r': 0.034,
            'theta_s': 0.460,
            'alpha': 0.016,
            'n': 1.37,
            'Ks': 6.0,  # 0.25 cm/hr * 24
            'l': 0.5
        },
        'silt_loam': {
            'theta_r': 0.067,
            'theta_s': 0.450,
            'alpha': 0.020,
            'n': 1.41,
            'Ks': 10.8,  # 0.45 cm/hr * 24
            'l': 0.5
        },
        'sandy_clay_loam': {
            'theta_r': 0.100,
            'theta_s': 0.390,
            'alpha': 0.059,
            'n': 1.48,
            'Ks': 31.44,  # 1.31 cm/hr * 24
            'l': 0.5
        },
        'clay_loam': {
            'theta_r': 0.095,
            'theta_s': 0.410,
            'alpha': 0.019,
            'n': 1.31,
            'Ks': 6.24,  # 0.26 cm/hr * 24
            'l': 0.5
        },
        'silty_clay_loam': {
            'theta_r': 0.089,
            'theta_s': 0.430,
            'alpha': 0.010,
            'n': 1.23,
            'Ks': 1.68,  # 0.07 cm/hr * 24
            'l': 0.5
        },
        'sandy_clay': {
            'theta_r': 0.100,
            'theta_s': 0.380,
            'alpha': 0.027,
            'n': 1.23,
            'Ks': 2.88,  # 0.12 cm/hr * 24
            'l': 0.5
        },
        'silty_clay': {
            'theta_r': 0.070,
            'theta_s': 0.360,
            'alpha': 0.005,
            'n': 1.09,
            'Ks': 0.48,  # 0.02 cm/hr * 24
            'l': 0.5
        },
        'clay': {
            'theta_r': 0.068,
            'theta_s': 0.380,
            'alpha': 0.008,
            'n': 1.09,
            'Ks': 4.8,  # 0.20 cm/hr * 24
            'l': 0.5
        }
    }

    # Normalize soil type name
    soil_type_normalized = soil_type.lower().replace(' ', '_')

    if soil_type_normalized not in soil_database:
        print(f"Warning: Soil type '{soil_type}' not recognized. Using 'loam'.")
        print(f"Available types: {', '.join(soil_database.keys())}")
        soil_type_normalized = 'loam'

    return soil_database[soil_type_normalized]


def create_infiltration_scenario(
    infiltration_rate: float = 5.0,
    duration: float = 5.0,
    redistribution_time: float = 5.0,
    soil_type: str = 'loam'
) -> ModelConfiguration:
    """
    Create infiltration followed by redistribution scenario

    Parameters
    ----------
    infiltration_rate : float
        Infiltration rate [cm/day]
    duration : float
        Duration of infiltration [days]
    redistribution_time : float
        Duration of redistribution period [days]
    soil_type : str
        Soil type

    Returns
    -------
    config : ModelConfiguration
        Model configuration
    """
    import pandas as pd

    # Create base configuration
    config = create_example_configuration(
        simulation_time=duration + redistribution_time,
        soil_type=soil_type
    )

    # Create time-variable BC: infiltration then no flux
    atmosph_data = pd.DataFrame({
        'time': [0.0, duration, duration + redistribution_time],
        'Prec': [infiltration_rate, 0.0, 0.0],
        'rSoil': [0.0, 0.0, 0.0],
        'rRoot': [0.0, 0.0, 0.0],
        'hCritA': [-10000.0, -10000.0, -10000.0]
    })

    config.bc_top = BoundaryCondition.atmospheric(atmosph_data)

    return config


def create_layered_soil(
    layer_depths: list,
    soil_types: list,
    n_nodes: int = 101
) -> tuple:
    """
    Create layered soil configuration

    Parameters
    ----------
    layer_depths : list
        Depth of each layer boundary (from surface, positive) [cm]
    soil_types : list
        Soil type for each layer
    n_nodes : int
        Total number of nodes

    Returns
    -------
    domain : ModelDomain
        Domain with layered materials
    materials : dict
        Material properties for each layer

    Examples
    --------
    >>> domain, materials = create_layered_soil(
    ...     layer_depths=[0, 30, 60, 100],
    ...     soil_types=['loam', 'sandy_loam', 'sand']
    ... )
    """
    if len(soil_types) != len(layer_depths) - 1:
        raise ValueError("Number of soil types must be one less than layer_depths")

    # Create node depths
    total_depth = layer_depths[-1]
    depths = np.linspace(0, -total_depth, n_nodes)

    # Assign materials to nodes
    materials_array = np.zeros(n_nodes, dtype=int)
    material_props = {}

    for i, (top, bottom) in enumerate(zip(layer_depths[:-1], layer_depths[1:])):
        mat_id = i + 1
        # Find nodes in this layer
        mask = (depths >= -bottom) & (depths <= -top)
        materials_array[mask] = mat_id

        # Get soil parameters
        soil_params = get_soil_parameters(soil_types[i])
        material_props[mat_id] = MaterialProperties(
            material_id=mat_id,
            **soil_params
        )

    # Create domain
    domain = ModelDomain(
        n_nodes=n_nodes,
        depths=depths,
        materials=materials_array,
        n_materials=len(soil_types),
        observation_nodes=[int(n_nodes * 0.25), int(n_nodes * 0.5), int(n_nodes * 0.75)]
    )

    return domain, material_props
