"""
Tests for I/O functionality
============================

Unit tests for input/output parsing and writing
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path

from hydrus1dpy.io.data_structures import (
    Units, ModelDomain, MaterialProperties,
    BoundaryCondition, TimeControl, InitialConditions,
    ModelConfiguration, ProcessFlags, NumericalParameters
)
from hydrus1dpy.io.input_writer import InputWriter
from hydrus1dpy.io.input_parser import InputParser


class TestDataStructures:
    """Test data structure classes"""

    def test_units_valid(self):
        """Test valid unit creation"""
        units = Units(length='cm', time='days')
        assert units.length == 'cm'
        assert units.time == 'days'

    def test_units_invalid(self):
        """Test invalid units raise error"""
        with pytest.raises(ValueError):
            Units(length='invalid', time='days')

    def test_material_properties_valid(self):
        """Test valid material properties"""
        mat = MaterialProperties(
            material_id=1,
            theta_r=0.078,
            theta_s=0.43,
            alpha=0.036,
            n=1.56,
            Ks=24.96
        )
        assert mat.material_id == 1
        assert 0 < mat.m < 1  # m = 1 - 1/n

    def test_material_properties_invalid(self):
        """Test invalid material properties"""
        # theta_r >= theta_s should fail
        with pytest.raises(ValueError):
            MaterialProperties(
                material_id=1,
                theta_r=0.5,
                theta_s=0.4,
                alpha=0.036,
                n=1.56,
                Ks=24.96
            )

        # n <= 1 should fail for van Genuchten
        with pytest.raises(ValueError):
            MaterialProperties(
                material_id=1,
                theta_r=0.078,
                theta_s=0.43,
                alpha=0.036,
                n=0.9,
                Ks=24.96
            )

    def test_boundary_condition_constant_head(self):
        """Test constant head BC"""
        bc = BoundaryCondition.constant_head(-100.0)
        assert bc.bc_type == -1
        assert bc.value == -100.0
        assert not bc.time_variable

    def test_boundary_condition_free_drainage(self):
        """Test free drainage BC"""
        bc = BoundaryCondition.free_drainage()
        assert bc.bc_type == -5

    def test_model_domain_valid(self):
        """Test valid domain creation"""
        n_nodes = 101
        depths = np.linspace(0, -100, n_nodes)
        materials = np.ones(n_nodes, dtype=int)

        domain = ModelDomain(
            n_nodes=n_nodes,
            depths=depths,
            materials=materials
        )

        assert domain.n_nodes == n_nodes
        assert domain.profile_length == 100.0

    def test_model_domain_invalid_depths(self):
        """Test that increasing depths raise error"""
        n_nodes = 101
        depths = np.linspace(-100, 0, n_nodes)  # Wrong order
        materials = np.ones(n_nodes, dtype=int)

        with pytest.raises(ValueError):
            ModelDomain(
                n_nodes=n_nodes,
                depths=depths,
                materials=materials
            )


class TestInputWriter:
    """Test input file writing"""

    def test_write_selector(self, tmp_path):
        """Test writing Selector.in file"""
        # Create simple configuration
        config = self._create_test_config()

        # Write files
        writer = InputWriter(config, tmp_path)
        writer.write_selector()

        # Check file exists
        selector_file = tmp_path / 'Selector.in'
        assert selector_file.exists()

        # Check file content
        content = selector_file.read_text()
        assert 'BLOCK A' in content
        assert 'BLOCK B' in content
        assert config.units.length in content

    def test_write_profile(self, tmp_path):
        """Test writing Profile.dat file"""
        config = self._create_test_config()

        writer = InputWriter(config, tmp_path)
        writer.write_profile()

        profile_file = tmp_path / 'Profile.dat'
        assert profile_file.exists()

        content = profile_file.read_text()
        assert 'BLOCK G' in content
        assert str(config.domain.n_nodes) in content

    def test_roundtrip(self, tmp_path):
        """Test write then read produces same configuration"""
        # Create configuration
        config_original = self._create_test_config()

        # Write files
        writer = InputWriter(config_original, tmp_path)
        writer.write_all()

        # Read files back
        parser = InputParser(tmp_path)
        config_read = parser.parse_all()

        # Compare key values
        assert config_read.domain.n_nodes == config_original.domain.n_nodes
        assert config_read.units.length == config_original.units.length
        assert len(config_read.materials) == len(config_original.materials)

        # Compare material properties
        for mat_id in config_original.materials:
            mat_orig = config_original.materials[mat_id]
            mat_read = config_read.materials[mat_id]
            assert np.isclose(mat_orig.theta_r, mat_read.theta_r, rtol=1e-4)
            assert np.isclose(mat_orig.theta_s, mat_read.theta_s, rtol=1e-4)
            assert np.isclose(mat_orig.alpha, mat_read.alpha, rtol=1e-4)

    @staticmethod
    def _create_test_config():
        """Create a test configuration"""
        n_nodes = 51
        depths = np.linspace(0, -50, n_nodes)
        materials = np.ones(n_nodes, dtype=int)

        domain = ModelDomain(
            n_nodes=n_nodes,
            depths=depths,
            materials=materials,
            observation_nodes=[10, 25, 40]
        )

        materials_dict = {
            1: MaterialProperties(
                material_id=1,
                theta_r=0.078,
                theta_s=0.43,
                alpha=0.036,
                n=1.56,
                Ks=24.96,
                l=0.5
            )
        }

        bc_top = BoundaryCondition.constant_flux(-5.0)
        bc_bottom = BoundaryCondition.free_drainage()

        time_control = TimeControl(
            t_max=5.0,
            dt_init=0.01,
            dt_min=0.0001,
            dt_max=0.5,
            print_times=np.linspace(0, 5, 6)
        )

        h_init = np.linspace(0, -50, n_nodes)
        initial_conditions = InitialConditions(h_init=h_init)

        config = ModelConfiguration(
            project_name='test_project',
            units=Units(length='cm', time='days'),
            domain=domain,
            materials=materials_dict,
            bc_top=bc_top,
            bc_bottom=bc_bottom,
            time_control=time_control,
            initial_conditions=initial_conditions
        )

        return config


class TestHelpers:
    """Test helper functions"""

    def test_create_example_configuration(self):
        """Test example configuration creation"""
        from hydrus1dpy.utils.helpers import create_example_configuration

        config = create_example_configuration()

        assert config.domain.n_nodes > 0
        assert len(config.materials) > 0
        assert config.time_control.t_max > 0

    def test_get_soil_parameters(self):
        """Test soil parameter database"""
        from hydrus1dpy.utils.helpers import get_soil_parameters

        # Test valid soil type
        params = get_soil_parameters('loam')
        assert 0 < params['theta_r'] < params['theta_s'] < 1
        assert params['alpha'] > 0
        assert params['n'] > 1
        assert params['Ks'] > 0

        # Test all soil types
        soil_types = ['sand', 'loam', 'clay', 'silt']
        for soil in soil_types:
            params = get_soil_parameters(soil)
            assert 'theta_r' in params
            assert 'theta_s' in params

    def test_create_layered_soil(self):
        """Test layered soil creation"""
        from hydrus1dpy.utils.helpers import create_layered_soil

        domain, materials = create_layered_soil(
            layer_depths=[0, 30, 60, 100],
            soil_types=['loam', 'sandy_loam', 'sand'],
            n_nodes=101
        )

        assert domain.n_nodes == 101
        assert len(materials) == 3
        assert domain.n_materials == 3

        # Check materials are properly assigned
        assert np.all(domain.materials >= 1)
        assert np.all(domain.materials <= 3)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
