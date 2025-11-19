"""
Input/Output module for HYDRUS1D
=================================

Handles reading and writing of HYDRUS1D input and output files.
"""

from .data_structures import (
    ModelDomain,
    TimeControl,
    ModelResults,
    BoundaryCondition,
    MaterialProperties
)
from .input_parser import InputParser
from .output_parser import OutputParser
from .input_writer import InputWriter

__all__ = [
    'ModelDomain',
    'TimeControl',
    'ModelResults',
    'BoundaryCondition',
    'MaterialProperties',
    'InputParser',
    'OutputParser',
    'InputWriter',
]
