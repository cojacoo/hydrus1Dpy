"""
Setup script for HYDRUS1D Python Solver - Phase 3
"""

from setuptools import setup, find_packages

setup(
    name="hydrus1dpy-phase3",
    version="0.3.0",
    description="Pure Python/Numba implementation of Richards equation solver",
    author="HYDRUS1DPy Development Team",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.20",
        "scipy>=1.7",
        "numba>=0.55",
        "plotly>=5.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Hydrology",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
