"""
Setup file for HYDRUS1D Python Wrapper - Phase 1
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text() if readme_file.exists() else ''

setup(
    name='hydrus1dpy-phase1',
    version='0.1.0',
    author='HYDRUS1DPy Development Team',
    author_email='',
    description='Python wrapper for HYDRUS1D Fortran hydrological model - Phase 1',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/cojacoo/hydrus1Dpy',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Hydrology',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.8',
    install_requires=[
        'numpy>=1.20',
        'pandas>=1.3',
        'plotly>=5.0',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov',
            'black',
            'flake8',
        ],
    },
    entry_points={
        'console_scripts': [
            'hydrus1d-create-example=hydrus1dpy.utils.helpers:create_example_configuration',
        ],
    },
)
