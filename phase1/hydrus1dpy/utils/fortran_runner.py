"""
Fortran Engine Runner
======================

Interface to run the compiled HYDRUS1D Fortran executable
"""

from pathlib import Path
import subprocess
import shutil
from typing import Optional
import tempfile

from ..io.data_structures import ModelConfiguration, ModelResults
from ..io.input_writer import InputWriter
from ..io.output_parser import OutputParser


class FortranRunner:
    """
    Run HYDRUS1D Fortran engine from Python

    This class handles:
    - Writing Python configuration to Fortran input files
    - Executing the Fortran binary
    - Parsing output files
    - Cleanup

    Examples
    --------
    >>> runner = FortranRunner(config, hydrus_exe='./hydrus1d.exe')
    >>> results = runner.run()
    """

    def __init__(self,
                 config: ModelConfiguration,
                 hydrus_exe: Optional[str] = None,
                 work_dir: Optional[str] = None,
                 keep_files: bool = False):
        """
        Initialize Fortran runner

        Parameters
        ----------
        config : ModelConfiguration
            Complete model configuration
        hydrus_exe : str, optional
            Path to HYDRUS1D executable
            If None, searches in standard locations
        work_dir : str, optional
            Working directory for simulation
            If None, creates temporary directory
        keep_files : bool
            Keep input/output files after run (default: False)
        """
        self.config = config
        self.keep_files = keep_files

        # Find Fortran executable
        if hydrus_exe is None:
            self.hydrus_exe = self._find_hydrus_executable()
        else:
            self.hydrus_exe = Path(hydrus_exe)
            if not self.hydrus_exe.exists():
                raise FileNotFoundError(f"HYDRUS executable not found: {hydrus_exe}")

        # Set up working directory
        if work_dir is None:
            self.work_dir = Path(tempfile.mkdtemp(prefix='hydrus1d_'))
            self._temp_dir = True
        else:
            self.work_dir = Path(work_dir)
            self.work_dir.mkdir(parents=True, exist_ok=True)
            self._temp_dir = False

    def _find_hydrus_executable(self) -> Optional[Path]:
        """
        Search for HYDRUS1D executable in standard locations

        Returns
        -------
        exe_path : Path or None
            Path to executable if found
        """
        # Search locations
        search_paths = [
            Path('./hydrus1d'),
            Path('./hydrus1d.exe'),
            Path('./HYDRUS'),
            Path('./HYDRUS.EXE'),
            Path('../src/hydrus1d'),
            Path('../fortran_build/hydrus1d'),
        ]

        for path in search_paths:
            if path.exists():
                return path.absolute()

        # Not found - return None and warn
        print("Warning: HYDRUS1D executable not found.")
        print("Please compile Fortran code or specify hydrus_exe parameter.")
        return None

    def run(self) -> ModelResults:
        """
        Run HYDRUS1D simulation

        Returns
        -------
        results : ModelResults
            Simulation results
        """
        try:
            # Write input files
            print(f"Writing input files to {self.work_dir}")
            self._write_input_files()

            # Run Fortran executable
            print("Running HYDRUS1D Fortran engine...")
            success, message = self._execute_fortran()

            if not success:
                return ModelResults(
                    project_name=self.config.project_name,
                    success=False,
                    message=message
                )

            # Parse output files
            print("Parsing output files...")
            results = self._parse_output_files()
            results.success = True
            results.message = "Simulation completed successfully"

            return results

        except Exception as e:
            return ModelResults(
                project_name=self.config.project_name,
                success=False,
                message=f"Error during simulation: {str(e)}"
            )

        finally:
            # Cleanup if requested
            if not self.keep_files and self._temp_dir:
                print(f"Cleaning up temporary directory {self.work_dir}")
                shutil.rmtree(self.work_dir, ignore_errors=True)

    def _write_input_files(self):
        """Write input files from configuration"""
        writer = InputWriter(self.config, self.work_dir)
        writer.write_all()
        writer.write_level_01_dir()

    def _execute_fortran(self) -> tuple:
        """
        Execute HYDRUS1D Fortran binary

        Returns
        -------
        success : bool
            True if execution succeeded
        message : str
            Error message if failed
        """
        if self.hydrus_exe is None:
            return False, "HYDRUS1D executable not found"

        try:
            # Run executable with working directory as argument
            result = subprocess.run(
                [str(self.hydrus_exe), str(self.work_dir)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=self.work_dir
            )

            # Check for errors
            if result.returncode != 0:
                error_msg = f"Fortran execution failed with code {result.returncode}\n"
                error_msg += f"stdout: {result.stdout}\n"
                error_msg += f"stderr: {result.stderr}"
                return False, error_msg

            # Check if output files were created
            if not (self.work_dir / 'T_LEVEL.OUT').exists():
                return False, "No output files created - simulation may have failed"

            return True, "Success"

        except subprocess.TimeoutExpired:
            return False, "Simulation timed out (>5 minutes)"

        except Exception as e:
            return False, f"Error executing Fortran: {str(e)}"

    def _parse_output_files(self) -> ModelResults:
        """Parse output files and return results"""
        parser = OutputParser(self.work_dir)
        results = parser.parse_all()
        results.project_name = self.config.project_name
        return results

    def compile_fortran(self, source_dir: str, output_exe: Optional[str] = None):
        """
        Compile Fortran source code (helper method)

        Parameters
        ----------
        source_dir : str
            Directory containing Fortran source files (*.FOR)
        output_exe : str, optional
            Output executable name (default: hydrus1d)

        Notes
        -----
        Requires gfortran compiler to be installed
        """
        source_dir = Path(source_dir)
        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")

        # Find all Fortran files
        fortran_files = list(source_dir.glob('*.FOR')) + list(source_dir.glob('*.for'))
        if not fortran_files:
            raise FileNotFoundError(f"No Fortran files found in {source_dir}")

        # Output executable name
        if output_exe is None:
            output_exe = 'hydrus1d.exe' if shutil.which('gfortran.exe') else 'hydrus1d'

        output_path = self.work_dir / output_exe

        # Compile command
        cmd = [
            'gfortran',
            '-O2',  # Optimization
            '-o', str(output_path),
        ] + [str(f) for f in fortran_files]

        print(f"Compiling Fortran code...")
        print(f"Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                print("Compilation failed:")
                print(result.stdout)
                print(result.stderr)
                return False

            print(f"Successfully compiled to {output_path}")
            self.hydrus_exe = output_path
            return True

        except FileNotFoundError:
            print("Error: gfortran compiler not found.")
            print("Please install gfortran to compile Fortran code.")
            return False

        except Exception as e:
            print(f"Error during compilation: {e}")
            return False
