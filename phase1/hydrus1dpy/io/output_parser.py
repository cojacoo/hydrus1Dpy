"""
HYDRUS1D Output File Parser
============================

Parse HYDRUS1D Fortran output files into Python data structures.
Based on OUTPUT.FOR subroutines.

Output files:
- T_LEVEL.OUT: Time-level information (mass balance)
- NOD_INF.OUT: Node information at print times
- OBS_NODE.OUT: Time series at observation nodes
- BALANCE.OUT: Detailed mass balance
"""

from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import re

from .data_structures import ModelResults


class OutputParser:
    """
    Parse HYDRUS1D output files

    Reads standard HYDRUS1D output file format and converts to pandas DataFrames
    """

    def __init__(self, project_path: str):
        """
        Initialize parser for HYDRUS1D output

        Parameters
        ----------
        project_path : str
            Path to directory containing HYDRUS1D output files
        """
        self.project_path = Path(project_path)
        if not self.project_path.exists():
            raise FileNotFoundError(f"Project path does not exist: {project_path}")

        self.tlevel_file = self.project_path / 'T_LEVEL.OUT'
        self.nod_inf_file = self.project_path / 'NOD_INF.OUT'
        self.obs_node_file = self.project_path / 'OBS_NODE.OUT'
        self.balance_file = self.project_path / 'BALANCE.OUT'
        self.run_inf_file = self.project_path / 'RUN_INF.OUT'

    def parse_all(self) -> ModelResults:
        """
        Parse all available output files

        Returns
        -------
        results : ModelResults
            Complete model results
        """
        results = ModelResults(
            project_name=self.project_path.name,
            success=True
        )

        # Parse time-level information
        if self.tlevel_file.exists():
            try:
                results.mass_balance = self.parse_tlevel()
            except Exception as e:
                print(f"Warning: Could not parse T_LEVEL.OUT: {e}")

        # Parse observation node data
        if self.obs_node_file.exists():
            try:
                results.obs_node_data = self.parse_obs_node()
            except Exception as e:
                print(f"Warning: Could not parse OBS_NODE.OUT: {e}")

        # Parse node information (profiles)
        if self.nod_inf_file.exists():
            try:
                profiles = self.parse_nod_inf()
                for time, profile in profiles.items():
                    results.add_profile(time, profile)
            except Exception as e:
                print(f"Warning: Could not parse NOD_INF.OUT: {e}")

        # Parse run information
        if self.run_inf_file.exists():
            try:
                results.run_info = self.parse_run_inf()
            except Exception as e:
                print(f"Warning: Could not parse RUN_INF.OUT: {e}")

        return results

    def parse_tlevel(self) -> pd.DataFrame:
        """
        Parse T_LEVEL.OUT file (time-level mass balance)

        Based on OUTPUT.FOR TLInf subroutine

        Returns
        -------
        data : pd.DataFrame
            Time series of mass balance components
        """
        if not self.tlevel_file.exists():
            raise FileNotFoundError(f"T_LEVEL.OUT not found: {self.tlevel_file}")

        data_lines = []

        with open(self.tlevel_file, 'r') as f:
            # Skip header lines until we find 'Time'
            for line in f:
                if 'Time' in line and 'rTop' in line:
                    break

            # Read data lines
            for line in f:
                line = line.strip()
                if not line or line == 'end':
                    break

                # Try to parse as numbers
                try:
                    values = [float(x) for x in line.split()]
                    if len(values) > 0:
                        data_lines.append(values)
                except ValueError:
                    continue

        if not data_lines:
            raise ValueError("No data found in T_LEVEL.OUT")

        # Convert to DataFrame
        # Typical columns: Time, rTop, rRoot, vTop, vRoot, vBot, sum(rTop), sum(rRoot), sum(vTop), sum(vRoot), sum(vBot), ...
        df = pd.DataFrame(data_lines)

        # Standard column names (may vary by version)
        if len(df.columns) >= 11:
            df.columns = [
                'time', 'rTop', 'rRoot', 'vTop', 'vRoot', 'vBot',
                'cum_rTop', 'cum_rRoot', 'cum_vTop', 'cum_vRoot', 'cum_vBot'
            ] + [f'col_{i}' for i in range(11, len(df.columns))]
        else:
            # Generic names if structure unknown
            df.columns = [f'col_{i}' for i in range(len(df.columns))]
            if len(df.columns) > 0:
                df.rename(columns={'col_0': 'time'}, inplace=True)

        return df

    def parse_obs_node(self) -> pd.DataFrame:
        """
        Parse OBS_NODE.OUT file (time series at observation nodes)

        Based on OUTPUT.FOR ObsNod subroutine

        Returns
        -------
        data : pd.DataFrame
            Time series at observation nodes
        """
        if not self.obs_node_file.exists():
            raise FileNotFoundError(f"OBS_NODE.OUT not found: {self.obs_node_file}")

        data_lines = []
        header_line = None

        with open(self.obs_node_file, 'r') as f:
            # Find header
            for line in f:
                if 'time' in line.lower() or 'Time' in line:
                    header_line = line.strip()
                    break

            # Read data
            for line in f:
                line = line.strip()
                if not line or line == 'end':
                    break

                try:
                    values = [float(x) for x in line.split()]
                    if len(values) > 0:
                        data_lines.append(values)
                except ValueError:
                    continue

        if not data_lines:
            raise ValueError("No data found in OBS_NODE.OUT")

        df = pd.DataFrame(data_lines)

        # Parse header for column names
        if header_line:
            # Extract column names from header
            col_names = self._parse_obs_node_header(header_line, df.shape[1])
            df.columns = col_names
        else:
            # Default names
            df.columns = ['time'] + [f'var_{i}' for i in range(1, len(df.columns))]

        return df

    def _parse_obs_node_header(self, header: str, n_cols: int) -> List[str]:
        """
        Parse OBS_NODE.OUT header line to extract column names

        Typical format: time  h1  h2  h3  theta1  theta2  theta3  ...
        """
        # Clean up header
        header = header.replace('time', ' time ')

        # Extract variable names
        parts = header.split()

        # If we don't have enough column names, generate them
        if len(parts) < n_cols:
            col_names = parts + [f'col_{i}' for i in range(len(parts), n_cols)]
        else:
            col_names = parts[:n_cols]

        return col_names

    def parse_nod_inf(self) -> Dict[float, pd.DataFrame]:
        """
        Parse NOD_INF.OUT file (profiles at print times)

        Based on OUTPUT.FOR NodOut subroutine

        Returns
        -------
        profiles : dict
            Dictionary mapping time to profile DataFrame
        """
        if not self.nod_inf_file.exists():
            raise FileNotFoundError(f"NOD_INF.OUT not found: {self.nod_inf_file}")

        profiles = {}
        current_time = None
        current_data = []

        with open(self.nod_inf_file, 'r') as f:
            for line in f:
                line = line.strip()

                # Check for time marker
                if 'Time:' in line or 'time:' in line:
                    # Save previous profile if exists
                    if current_time is not None and current_data:
                        profiles[current_time] = self._create_profile_dataframe(current_data)

                    # Extract new time
                    time_match = re.search(r'[Tt]ime:\s*([0-9.Ee+-]+)', line)
                    if time_match:
                        current_time = float(time_match.group(1))
                        current_data = []

                # Check for end marker
                elif line == 'end':
                    break

                # Try to parse as data line
                else:
                    try:
                        values = [float(x) for x in line.split()]
                        if len(values) >= 3:  # At least node, depth, and one variable
                            current_data.append(values)
                    except ValueError:
                        continue

        # Save last profile
        if current_time is not None and current_data:
            profiles[current_time] = self._create_profile_dataframe(current_data)

        return profiles

    def _create_profile_dataframe(self, data: List[List[float]]) -> pd.DataFrame:
        """
        Create profile DataFrame from parsed data

        Typical columns: Node, Depth, h, theta, K, C, Flux, Sink, ...
        """
        df = pd.DataFrame(data)

        # Standard column names for water flow
        if len(df.columns) >= 6:
            df.columns = [
                'node', 'depth', 'h', 'theta', 'K', 'C'
            ] + [f'var_{i}' for i in range(6, len(df.columns))]
        else:
            df.columns = [f'col_{i}' for i in range(len(df.columns))]

        return df

    def parse_balance(self) -> pd.DataFrame:
        """
        Parse BALANCE.OUT file (detailed mass balance)

        Returns
        -------
        data : pd.DataFrame
            Detailed mass balance information
        """
        if not self.balance_file.exists():
            raise FileNotFoundError(f"BALANCE.OUT not found: {self.balance_file}")

        # BALANCE.OUT has a complex format with multiple sections
        # For simplicity, extract key cumulative values

        balance_data = {
            'total_infiltration': None,
            'total_evaporation': None,
            'total_drainage': None,
            'total_root_uptake': None,
            'storage_change': None,
            'balance_error': None
        }

        with open(self.balance_file, 'r') as f:
            content = f.read()

            # Extract cumulative values using regex
            patterns = {
                'total_infiltration': r'Infiltration\s*[=:]\s*([0-9.Ee+-]+)',
                'total_evaporation': r'Evaporation\s*[=:]\s*([0-9.Ee+-]+)',
                'total_drainage': r'Bottom Flux\s*[=:]\s*([0-9.Ee+-]+)',
                'total_root_uptake': r'Root Uptake\s*[=:]\s*([0-9.Ee+-]+)',
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    balance_data[key] = float(match.group(1))

        return pd.DataFrame([balance_data])

    def parse_run_inf(self) -> Dict:
        """
        Parse RUN_INF.OUT file (run information)

        Returns
        -------
        info : dict
            Run information and statistics
        """
        if not self.run_inf_file.exists():
            return {}

        info = {}

        with open(self.run_inf_file, 'r') as f:
            content = f.read()

            # Extract key information
            # Number of iterations
            match = re.search(r'Number of iterations\s*[=:]\s*([0-9]+)', content, re.IGNORECASE)
            if match:
                info['total_iterations'] = int(match.group(1))

            # Convergence status
            if 'converged' in content.lower():
                info['converged'] = True
            elif 'not converged' in content.lower():
                info['converged'] = False

        return info

    @staticmethod
    def read_fortran_output(file_path: Path) -> str:
        """
        Read a Fortran output file, handling common format issues

        Parameters
        ----------
        file_path : Path
            Path to output file

        Returns
        -------
        content : str
            File content
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
