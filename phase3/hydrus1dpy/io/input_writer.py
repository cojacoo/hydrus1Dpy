"""
HYDRUS1D Input File Writer
===========================

Write Python data structures to HYDRUS1D Fortran-compatible input files.
Allows creating new simulations or modifying existing ones from Python.
"""

from pathlib import Path
from typing import Optional
import numpy as np

from .data_structures import ModelConfiguration


class InputWriter:
    """
    Write HYDRUS1D input files from Python data structures

    Creates Fortran-compatible input files from ModelConfiguration object.
    """

    def __init__(self, config: ModelConfiguration, output_path: str):
        """
        Initialize writer

        Parameters
        ----------
        config : ModelConfiguration
            Complete model configuration
        output_path : str
            Directory where input files will be written
        """
        self.config = config
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)

    def write_all(self):
        """Write all input files"""
        self.write_selector()
        self.write_profile()

        # Write atmospheric BC if time-variable
        if self.config.bc_top.time_variable and self.config.bc_top.data is not None:
            self.write_atmosph()

    def write_selector(self):
        """
        Write Selector.in file

        Based on INPUT.FOR BasInf reading format (inverse operation)
        """
        selector_file = self.output_path / 'Selector.in'

        with open(selector_file, 'w') as f:
            # Header
            f.write("Pcp_File_Version=4\n")
            f.write("*** BLOCK A: BASIC INFORMATION *****************************************\n")
            f.write(f"{self.config.project_name}\n")

            # Units
            f.write("*** BLOCK B: UNITS ******************************************************\n")
            f.write(f"{self.config.units.length:5s}\n")
            f.write(f"{self.config.units.time:5s}\n")
            f.write(f"{self.config.units.mass:5s}\n")

            # Process flags
            f.write("*** BLOCK C: PROCESSES **************************************************\n")
            p = self.config.processes
            f.write(f"{'t' if p.water else 'f':5s}")
            f.write(f"{'t' if p.solute else 'f':5s}")
            f.write(f"{'t' if p.heat else 'f':5s}")
            f.write(f"{'t' if p.root else 'f':5s}")  # SinkF
            f.write(f"{'t' if p.root else 'f':5s}")  # lRoot
            f.write(f"{'f':5s}")  # ShortO
            f.write(f"{'f':5s}")  # lWDep
            f.write(f"{'f':5s}")  # lScreen
            f.write(f"{'t' if self.config.bc_top.bc_type == -4 else 'f':5s}")  # AtmBC
            f.write(f"{'f':5s}\n")  # lEquil

            # Additional process flags
            f.write(f"{'t' if p.snow else 'f':5s}")
            f.write(f"{'f':5s}")  # dummy
            f.write(f"{'t' if p.meteo else 'f':5s}")
            f.write(f"{'t' if p.vapor else 'f':5s}")
            f.write(f"{'f':5s}")  # lActRSU
            f.write(f"{'f':5s}\n")  # lFlux

            # Materials and geometry
            f.write("*** BLOCK D: GEOMETRY **************************************************\n")
            f.write(f"{self.config.domain.n_materials:5d}")
            f.write(f"{self.config.domain.n_layers:5d}")
            f.write(f"{self.config.numerical.cos_alpha:8.3f}\n")

            # Numerical parameters
            f.write("*** BLOCK E: ITERATION *************************************************\n")
            f.write(f"{self.config.numerical.max_iter:5d}")
            f.write(f"{self.config.numerical.tol_theta:8.3f}")
            f.write(f"{self.config.numerical.tol_h:8.5f}\n")

            # Top boundary condition
            f.write("*** BLOCK F: BOUNDARY CONDITIONS ***************************************\n")
            bc_top = self.config.bc_top
            f.write(f"{'t' if bc_top.time_variable else 'f':5s}")  # TopInF
            f.write(f"{'f':5s}")  # WLayer
            f.write(f"{bc_top.bc_type:5d}")  # KodTop
            f.write(f"{'f':5s}\n")  # lInitW

            # Bottom boundary condition
            bc_bot = self.config.bc_bottom
            is_free_drain = (bc_bot.bc_type == -5)
            is_gwl = (bc_bot.bc_type == -7)
            is_seep = (bc_bot.bc_type == -2)

            f.write(f"{'t' if bc_bot.time_variable else 'f':5s}")  # BotInF
            f.write(f"{'t' if is_gwl else 'f':5s}")  # qGWLF
            f.write(f"{'t' if is_free_drain else 'f':5s}")  # FreeD
            f.write(f"{'t' if is_seep else 'f':5s}")  # SeepF
            f.write(f"{bc_bot.bc_type:5d}")  # KodBot
            f.write(f"{'f':5s}")  # qDrain
            f.write(f"{0.0:8.3f}\n")  # hSeep

            # Constant BC values if not time-variable
            if not bc_top.time_variable or not bc_bot.time_variable:
                rTop = bc_top.value if bc_top.value is not None else 0.0
                rBot = bc_bot.value if bc_bot.value is not None else 0.0
                rRoot = 0.0
                f.write(f"{rTop:12.6e}  {rBot:12.6e}  {rRoot:12.6e}\n")

    def write_profile(self):
        """
        Write Profile.dat file

        Based on INPUT.FOR NodInf and MatIn reading format (inverse operation)
        """
        profile_file = self.output_path / 'Profile.dat'

        with open(profile_file, 'w') as f:
            # Header
            f.write("Pcp_File_Version=4\n")
            f.write("*** BLOCK G: WATER FLOW INFORMATION ************************************\n")

            # Number of nodes and observations
            n_obs = len(self.config.domain.observation_nodes) if self.config.domain.observation_nodes else 0
            f.write(f"{self.config.domain.n_nodes:5d}  {n_obs:5d}\n")

            # Node information header
            f.write("*** BLOCK H: NODAL INFORMATION *****************************************\n")
            f.write("    n        x           h      Mat    Lay     Beta      Axz       Bxz       Dxz\n")

            # Write nodes
            for i in range(self.config.domain.n_nodes):
                node_num = i + 1
                depth = self.config.domain.depths[i]
                h = self.config.initial_conditions.h_init[i]
                mat = self.config.domain.materials[i]
                lay = self.config.domain.layer_numbers[i] if self.config.domain.layer_numbers is not None else 1
                beta = 0.0  # No root uptake distribution by default
                axz = 1.0   # No anisotropy by default
                bxz = 1.0
                dxz = 1.0

                f.write(f"{node_num:5d}  {depth:10.4f}  {h:10.4f}  {mat:4d}  {lay:4d}  "
                       f"{beta:8.5f}  {axz:8.5f}  {bxz:8.5f}  {dxz:8.5f}\n")

            # Observation nodes
            if n_obs > 0:
                f.write("*** BLOCK I: OBSERVATION NODES ******************************************\n")
                obs_str = "  ".join([f"{n:5d}" for n in self.config.domain.observation_nodes])
                f.write(f"{obs_str}\n")

            # Material properties
            f.write("*** BLOCK J: MATERIAL INFORMATION **************************************\n")
            f.write("  hTab1   hTabN\n")
            f.write(f"{-0.0001:8.4f}  {-100.0:8.2f}\n")

            # Model type
            model_type = 0  # Default to van Genuchten
            if self.config.materials:
                first_mat = list(self.config.materials.values())[0]
                model_type = first_mat.model_type

            f.write(f"{model_type:5d}  {0:5d}\n")  # iModel, iHyst

            # Material parameters
            f.write("   Mat     Qr      Qs         Alfa         n          Ks       l\n")

            for mat_id in sorted(self.config.materials.keys()):
                mat = self.config.materials[mat_id]
                f.write(f"{mat.material_id:5d}  ")
                f.write(f"{mat.theta_r:7.4f}  ")
                f.write(f"{mat.theta_s:7.4f}  ")
                f.write(f"{mat.alpha:12.6e}  ")
                f.write(f"{mat.n:12.6e}  ")
                f.write(f"{mat.Ks:12.6e}  ")
                f.write(f"{mat.l:7.4f}\n")

    def write_atmosph(self):
        """
        Write ATMOSPH.IN file for time-variable boundary conditions

        Based on TIME.FOR SetBC reading format (inverse operation)
        """
        if self.config.bc_top.data is None:
            return

        atmosph_file = self.output_path / 'ATMOSPH.IN'
        data = self.config.bc_top.data

        with open(atmosph_file, 'w') as f:
            # Header
            f.write("Pcp_File_Version=4\n")
            f.write("*** BLOCK K: ATMOSPHERIC INFORMATION ***********************************\n")

            # Number of records
            n_records = len(data)
            f.write(f"{n_records:5d}\n")

            # Column headers
            f.write("       tAtm         Prec         rSoil        rRoot        hCritA\n")

            # Write data
            for idx, row in data.iterrows():
                f.write(f"{row['time']:12.6e}  ")
                f.write(f"{row['Prec']:12.6e}  ")
                f.write(f"{row['rSoil']:12.6e}  ")
                f.write(f"{row['rRoot']:12.6e}  ")
                f.write(f"{row['hCritA']:12.6e}\n")

            # End marker
            f.write("end\n")

    def write_level_01_dir(self):
        """
        Write LEVEL_01.DIR file that points to the project directory

        This file tells HYDRUS where to find input files
        """
        level_file = self.output_path / 'LEVEL_01.DIR'

        with open(level_file, 'w') as f:
            # Write absolute path to output directory
            f.write(f"{self.output_path.absolute()}\n")
