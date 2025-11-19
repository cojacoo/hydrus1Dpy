"""
HYDRUS1D Input File Parser
===========================

Parse HYDRUS1D Fortran input files into Python data structures.
Based on INPUT.FOR subroutines: BasInf, NodInf, MatIn, TmIn, etc.

References:
- HYDRUS.FOR lines 136-194 (file opening)
- INPUT.FOR lines 3-178 (BasInf subroutine)
- INPUT.FOR lines 208-471 (NodInf subroutine)
- INPUT.FOR lines 536-728 (MatIn subroutine)
"""

from pathlib import Path
from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd
import re

from .data_structures import (
    Units, ProcessFlags, NumericalParameters,
    BoundaryCondition, MaterialProperties, ModelDomain,
    TimeControl, InitialConditions, ModelConfiguration
)


class InputParser:
    """
    Parse HYDRUS1D input files

    Reads the standard HYDRUS1D input file format:
    - Selector.in: Main control file
    - Profile.dat: Spatial domain and initial conditions
    - ATMOSPH.IN: Time-variable boundary conditions (optional)
    - Meteo.in: Meteorological data (optional)
    """

    def __init__(self, project_path: str):
        """
        Initialize parser for a HYDRUS1D project

        Parameters
        ----------
        project_path : str
            Path to directory containing HYDRUS1D input files
        """
        self.project_path = Path(project_path)
        if not self.project_path.exists():
            raise FileNotFoundError(f"Project path does not exist: {project_path}")

        self.selector_file = self.project_path / 'Selector.in'
        self.profile_file = self.project_path / 'Profile.dat'
        self.atmosph_file = self.project_path / 'ATMOSPH.IN'
        self.meteo_file = self.project_path / 'Meteo.in'

    def parse_all(self) -> ModelConfiguration:
        """
        Parse all input files and return complete model configuration

        Returns
        -------
        config : ModelConfiguration
            Complete model configuration
        """
        # Parse main files
        selector_data = self.parse_selector()
        profile_data = self.parse_profile(selector_data['n_materials'])

        # Parse optional atmospheric BC
        bc_top = selector_data['bc_top']
        if selector_data['top_time_variable'] and self.atmosph_file.exists():
            atmosph_data = self.parse_atmosph()
            bc_top = BoundaryCondition.atmospheric(atmosph_data)

        # Build configuration
        config = ModelConfiguration(
            project_name=self.project_path.name,
            units=selector_data['units'],
            domain=profile_data['domain'],
            materials=profile_data['materials'],
            bc_top=bc_top,
            bc_bottom=selector_data['bc_bottom'],
            time_control=selector_data['time_control'],
            initial_conditions=profile_data['initial_conditions'],
            processes=selector_data['processes'],
            numerical=selector_data['numerical']
        )

        return config

    def parse_selector(self) -> Dict:
        """
        Parse Selector.in file

        Based on INPUT.FOR BasInf subroutine (lines 3-178)

        Returns
        -------
        data : dict
            Dictionary containing all selector file data
        """
        if not self.selector_file.exists():
            raise FileNotFoundError(f"Selector.in not found: {self.selector_file}")

        with open(self.selector_file, 'r') as f:
            lines = f.readlines()

        idx = 0

        def skip_to_next_data(lines, start_idx):
            """Skip comment and blank lines, return index of next data line"""
            i = start_idx
            while i < len(lines):
                line = lines[i].strip()
                if line and not line.startswith('*') and not line.startswith('!'):
                    return i
                i += 1
            raise ValueError("Unexpected end of file")

        # Header (skip)
        idx = skip_to_next_data(lines, 0)
        header = lines[idx].strip()
        idx += 1

        # Units
        idx = skip_to_next_data(lines, idx)
        length_unit = lines[idx].strip()
        idx += 1
        idx = skip_to_next_data(lines, idx)
        time_unit = lines[idx].strip()
        idx += 1
        idx = skip_to_next_data(lines, idx)
        mass_unit = lines[idx].strip()
        idx += 1

        units = Units(length=length_unit, time=time_unit, mass=mass_unit)

        # Process flags
        idx = skip_to_next_data(lines, idx)
        process_line = lines[idx].strip().split()
        lWat = process_line[0].lower() in ['t', 'true', '1']
        lChem = process_line[1].lower() in ['t', 'true', '1']
        lTemp = process_line[2].lower() in ['t', 'true', '1']
        SinkF = process_line[3].lower() in ['t', 'true', '1']
        lRoot = process_line[4].lower() in ['t', 'true', '1']
        ShortO = process_line[5].lower() in ['t', 'true', '1']
        lWDep = process_line[6].lower() in ['t', 'true', '1']
        lScreen = process_line[7].lower() in ['t', 'true', '1']
        AtmBC = process_line[8].lower() in ['t', 'true', '1']
        lEquil = process_line[9].lower() in ['t', 'true', '1']
        idx += 1

        # Additional process flags (version dependent)
        idx = skip_to_next_data(lines, idx)
        extra_process = lines[idx].strip().split()
        lSnow = extra_process[0].lower() in ['t', 'true', '1'] if len(extra_process) > 0 else False
        lMeteo = extra_process[2].lower() in ['t', 'true', '1'] if len(extra_process) > 2 else False
        lVapor = extra_process[3].lower() in ['t', 'true', '1'] if len(extra_process) > 3 else False
        idx += 1

        processes = ProcessFlags(
            water=lWat,
            solute=lChem,
            heat=lTemp,
            root=lRoot or SinkF,
            snow=lSnow and lTemp,
            vapor=lVapor,
            meteo=lMeteo
        )

        # Material and layer information
        idx = skip_to_next_data(lines, idx)
        mat_line = lines[idx].strip().split()
        n_materials = int(mat_line[0])
        n_layers = int(mat_line[1])
        cos_alpha = float(mat_line[2])
        idx += 1

        # Numerical parameters
        idx = skip_to_next_data(lines, idx)
        num_line = lines[idx].strip().split()
        max_iter = int(num_line[0])
        tol_theta = float(num_line[1])
        tol_h = float(num_line[2])
        idx += 1

        numerical = NumericalParameters(
            max_iter=max_iter,
            tol_theta=tol_theta,
            tol_h=tol_h,
            cos_alpha=cos_alpha
        )

        # Top boundary condition
        idx = skip_to_next_data(lines, idx)
        top_bc_line = lines[idx].strip().split()
        TopInF = top_bc_line[0].lower() in ['t', 'true', '1']
        WLayer = top_bc_line[1].lower() in ['t', 'true', '1']
        KodTop = int(top_bc_line[2])
        lInitW = top_bc_line[3].lower() in ['t', 'true', '1']
        idx += 1

        # Bottom boundary condition
        idx = skip_to_next_data(lines, idx)
        bot_bc_line = lines[idx].strip().split()
        BotInF = bot_bc_line[0].lower() in ['t', 'true', '1']
        qGWLF = bot_bc_line[1].lower() in ['t', 'true', '1']
        FreeD = bot_bc_line[2].lower() in ['t', 'true', '1']
        SeepF = bot_bc_line[3].lower() in ['t', 'true', '1']
        KodBot = int(bot_bc_line[4])
        qDrain = bot_bc_line[5].lower() in ['t', 'true', '1']
        hSeep = float(bot_bc_line[6]) if len(bot_bc_line) > 6 else 0.0
        idx += 1

        # Determine final BC codes based on flags (from INPUT.FOR lines 104-115)
        if TopInF:
            KodTop = int(np.sign(KodTop)) * 3
        if WLayer:
            KodTop = -abs(KodTop)
        if AtmBC and KodTop < 0:
            KodTop = -4

        if BotInF:
            KodBot = int(np.sign(KodBot)) * 3
        if qGWLF:
            KodBot = -7
        if FreeD:
            KodBot = -5
        if SeepF:
            KodBot = -2

        # Parse rTop, rBot, rRoot if needed
        rTop = None
        rBot = None
        rRoot = None
        if (not TopInF and KodTop == -1) or (not BotInF and KodBot == -1 and not qGWLF and not FreeD and not SeepF and not qDrain):
            idx = skip_to_next_data(lines, idx)
            r_line = lines[idx].strip().split()
            rTop = float(r_line[0])
            rBot = float(r_line[1])
            rRoot = float(r_line[2])
            idx += 1

        # Create boundary conditions
        bc_top = BoundaryCondition(bc_type=KodTop, time_variable=TopInF, value=rTop)
        bc_bottom = BoundaryCondition(bc_type=KodBot, time_variable=BotInF, value=rBot)

        # Time information - we'll get this from profile.dat or use defaults
        time_control = TimeControl(
            t_init=0.0,
            t_max=10.0,  # Will be updated from profile if available
            dt_init=0.01,
            dt_min=0.0001,
            dt_max=1.0
        )

        return {
            'header': header,
            'units': units,
            'processes': processes,
            'numerical': numerical,
            'n_materials': n_materials,
            'n_layers': n_layers,
            'bc_top': bc_top,
            'bc_bottom': bc_bottom,
            'top_time_variable': TopInF or AtmBC,
            'time_control': time_control
        }

    def parse_profile(self, n_materials: int) -> Dict:
        """
        Parse Profile.dat file

        Based on INPUT.FOR NodInf and MatIn subroutines

        Parameters
        ----------
        n_materials : int
            Number of materials (from Selector.in)

        Returns
        -------
        data : dict
            Dictionary containing domain, materials, and initial conditions
        """
        if not self.profile_file.exists():
            raise FileNotFoundError(f"Profile.dat not found: {self.profile_file}")

        with open(self.profile_file, 'r') as f:
            lines = f.readlines()

        idx = 0

        def skip_to_next_data(lines, start_idx):
            """Skip comment and blank lines"""
            i = start_idx
            while i < len(lines):
                line = lines[i].strip()
                if line and not line.startswith('*') and not line.startswith('!'):
                    return i
                i += 1
            raise ValueError("Unexpected end of file")

        # Skip header
        idx = skip_to_next_data(lines, 0)
        idx += 1

        # Number of nodes and observations
        idx = skip_to_next_data(lines, idx)
        node_line = lines[idx].strip().split()
        n_nodes = int(node_line[0])
        n_obs = int(node_line[1]) if len(node_line) > 1 else 0
        idx += 1

        # Read node information
        depths = np.zeros(n_nodes)
        h_init = np.zeros(n_nodes)
        materials = np.zeros(n_nodes, dtype=int)

        # Skip header
        idx = skip_to_next_data(lines, idx)
        idx += 1

        # Read nodes (depth, h, Mat)
        for i in range(n_nodes):
            idx = skip_to_next_data(lines, idx)
            node_data = lines[idx].strip().split()
            # Format: n  x  h  Mat  Lay  Beta  Axz  Bxz  Dxz
            depths[i] = float(node_data[1])      # x (depth)
            h_init[i] = float(node_data[2])       # h (pressure head)
            materials[i] = int(node_data[3])      # Mat (material number)
            idx += 1

        # Observation nodes
        observation_nodes = None
        if n_obs > 0:
            idx = skip_to_next_data(lines, idx)
            idx += 1  # Skip header
            idx = skip_to_next_data(lines, idx)
            obs_line = lines[idx].strip().split()
            observation_nodes = [int(x) for x in obs_line[:n_obs]]
            idx += 1

        # Material properties
        idx = skip_to_next_data(lines, idx)
        idx += 1  # Skip header for hTab1, hTabN

        idx = skip_to_next_data(lines, idx)
        htab_line = lines[idx].strip().split()
        hTab1 = float(htab_line[0])
        hTabN = float(htab_line[1])
        idx += 1

        # Model type and hysteresis
        idx = skip_to_next_data(lines, idx)
        idx += 1  # Skip header
        idx = skip_to_next_data(lines, idx)
        model_line = lines[idx].strip().split()
        iModel = int(model_line[0])
        iHyst = int(model_line[1])
        idx += 1

        # Skip hysteresis info if present
        if iHyst > 0:
            idx = skip_to_next_data(lines, idx)
            idx += 1
            idx = skip_to_next_data(lines, idx)
            idx += 1

        # Material parameters
        idx = skip_to_next_data(lines, idx)
        idx += 1  # Skip header

        material_props = {}
        for mat_id in range(1, n_materials + 1):
            idx = skip_to_next_data(lines, idx)
            mat_line = lines[idx].strip().split()

            # Basic van Genuchten parameters: theta_r, theta_s, alpha, n, Ks, l
            material_props[mat_id] = MaterialProperties(
                material_id=mat_id,
                model_type=iModel,
                theta_r=float(mat_line[0]),
                theta_s=float(mat_line[1]),
                alpha=float(mat_line[2]),
                n=float(mat_line[3]),
                Ks=float(mat_line[4]),
                l=float(mat_line[5]) if len(mat_line) > 5 else 0.5
            )
            idx += 1

        # Create domain
        domain = ModelDomain(
            n_nodes=n_nodes,
            depths=depths,
            materials=materials,
            n_materials=n_materials,
            observation_nodes=observation_nodes
        )

        # Create initial conditions
        initial_conditions = InitialConditions(h_init=h_init)

        return {
            'domain': domain,
            'materials': material_props,
            'initial_conditions': initial_conditions,
            'model_type': iModel,
            'hysteresis': iHyst
        }

    def parse_atmosph(self) -> pd.DataFrame:
        """
        Parse ATMOSPH.IN file for time-variable boundary conditions

        Based on TIME.FOR SetBC subroutine (lines 59-185)

        Returns
        -------
        data : pd.DataFrame
            Time series of atmospheric boundary conditions
        """
        if not self.atmosph_file.exists():
            raise FileNotFoundError(f"ATMOSPH.IN not found: {self.atmosph_file}")

        with open(self.atmosph_file, 'r') as f:
            lines = f.readlines()

        idx = 0

        def skip_to_next_data(lines, start_idx):
            """Skip comment and blank lines"""
            i = start_idx
            while i < len(lines):
                line = lines[i].strip()
                if line and not line.startswith('*') and not line.startswith('!'):
                    return i
                i += 1
            return len(lines)

        # Skip header
        idx = skip_to_next_data(lines, 0)
        idx += 1

        # Number of atmospheric data records
        idx = skip_to_next_data(lines, idx)
        n_records = int(lines[idx].strip().split()[0])
        idx += 1

        # Skip header line
        idx = skip_to_next_data(lines, idx)
        idx += 1

        # Read data
        data_records = []
        for i in range(n_records):
            idx = skip_to_next_data(lines, idx)
            if idx >= len(lines):
                break

            data_line = lines[idx].strip().split()

            # Format: tAtm Prec rSoil rRoot hCritA [rBot] [hCritS] [temp] [...solute conc]
            record = {
                'time': float(data_line[0]),        # tAtm
                'Prec': float(data_line[1]),        # Precipitation
                'rSoil': float(data_line[2]),       # Potential evaporation
                'rRoot': float(data_line[3]),       # Potential transpiration
                'hCritA': float(data_line[4])       # Critical pressure head
            }

            # Optional fields
            if len(data_line) > 5:
                record['rBot'] = float(data_line[5])
            if len(data_line) > 6:
                record['hCritS'] = float(data_line[6])
            if len(data_line) > 7:
                record['Temp'] = float(data_line[7])

            data_records.append(record)
            idx += 1

        return pd.DataFrame(data_records)

    def parse_meteo(self) -> Optional[pd.DataFrame]:
        """
        Parse Meteo.in file for meteorological data (optional)

        Returns
        -------
        data : pd.DataFrame or None
            Meteorological time series if file exists
        """
        if not self.meteo_file.exists():
            return None

        # Meteo file format is more complex - implement if needed
        # For now, return None
        return None
