"""
Tests for Hydraulic Models
===========================

Unit tests for all hydraulic model implementations.
"""

import pytest
import numpy as np
from hydrus1dpy.materials import (
    VanGenuchten, ModifiedVanGenuchten, BrooksCorey,
    DualPorosity, LogNormal, CustomHydraulicModel
)


class TestVanGenuchten:
    """Test van Genuchten model"""

    def test_loam_soil(self):
        """Test with Carsel & Parrish (1988) loam parameters"""
        vg = VanGenuchten(
            theta_r=0.078,
            theta_s=0.430,
            alpha=0.036,
            n=1.56,
            Ks=24.96,
            l=0.5
        )

        # Test saturated conditions
        assert np.isclose(vg.water_content(0), vg.theta_s)
        assert np.isclose(vg.conductivity(0), vg.Ks)
        assert np.isclose(vg.capacity(0), 0.0)

        # Test unsaturated conditions
        h = -100.0
        theta = vg.water_content(h)
        assert vg.theta_r < theta < vg.theta_s

        K = vg.conductivity(h)
        assert 0 < K < vg.Ks

        C = vg.capacity(h)
        assert C > 0

    def test_inverse_function(self):
        """Test theta -> h -> theta round trip"""
        vg = VanGenuchten(
            theta_r=0.078, theta_s=0.430,
            alpha=0.036, n=1.56, Ks=24.96
        )

        # Test several theta values
        for theta_test in np.linspace(0.08, 0.42, 5):
            h = vg.pressure_head(theta_test)
            theta_back = vg.water_content(h)
            assert np.isclose(theta_test, theta_back, rtol=1e-3)

    def test_vectorization(self):
        """Test array inputs"""
        vg = VanGenuchten(
            theta_r=0.078, theta_s=0.430,
            alpha=0.036, n=1.56, Ks=24.96
        )

        h_array = np.array([-1000, -100, -10, 0])
        theta = vg.water_content(h_array)
        assert len(theta) == len(h_array)
        assert np.all(theta >= vg.theta_r)
        assert np.all(theta <= vg.theta_s)

    def test_monotonicity(self):
        """Test that theta and K increase with h"""
        vg = VanGenuchten(
            theta_r=0.078, theta_s=0.430,
            alpha=0.036, n=1.56, Ks=24.96
        )

        h = np.linspace(-1000, 0, 100)
        theta = vg.water_content(h)
        K = vg.conductivity(h)

        # Should be monotonically increasing
        assert np.all(np.diff(theta) >= -1e-10)
        assert np.all(np.diff(K) >= -1e-10)

    def test_validation(self):
        """Test model validation"""
        vg = VanGenuchten(
            theta_r=0.078, theta_s=0.430,
            alpha=0.036, n=1.56, Ks=24.96
        )

        assert vg.validate() is True

    def test_parameter_constraints(self):
        """Test that invalid parameters raise errors"""
        # theta_r >= theta_s should fail
        with pytest.raises(ValueError):
            VanGenuchten(
                theta_r=0.5, theta_s=0.4,
                alpha=0.036, n=1.56, Ks=24.96
            )

        # n <= 1 should fail
        with pytest.raises(ValueError):
            VanGenuchten(
                theta_r=0.078, theta_s=0.430,
                alpha=0.036, n=0.9, Ks=24.96
            )

        # alpha <= 0 should fail
        with pytest.raises(ValueError):
            VanGenuchten(
                theta_r=0.078, theta_s=0.430,
                alpha=-0.036, n=1.56, Ks=24.96
            )


class TestBrooksCorey:
    """Test Brooks-Corey model"""

    def test_basic_properties(self):
        """Test basic Brooks-Corey properties"""
        bc = BrooksCorey(
            theta_r=0.078, theta_s=0.430,
            hb=-20.0, lambda_=0.5,
            Ks=24.96
        )

        # At air-entry value
        assert np.isclose(bc.water_content(bc.hb), bc.theta_s, rtol=1e-3)

        # Below air-entry
        theta = bc.water_content(-100)
        assert bc.theta_r < theta < bc.theta_s

        # Above air-entry (saturated)
        assert np.isclose(bc.water_content(-10), bc.theta_s)

    def test_validation(self):
        """Test model validation"""
        bc = BrooksCorey(
            theta_r=0.078, theta_s=0.430,
            hb=-20.0, lambda_=0.5, Ks=24.96
        )

        assert bc.validate() is True


class TestDualPorosity:
    """Test dual-porosity model"""

    def test_basic_properties(self):
        """Test dual-porosity model"""
        dp = DualPorosity(
            theta_r=0.078, theta_s=0.430,
            alpha1=0.1, n1=2.0,    # Macro pores
            alpha2=0.01, n2=1.5,   # Micro pores
            w2=0.3,  # 30% weight to micro pores
            Ks=24.96
        )

        # Test water content
        theta = dp.water_content(-100)
        assert dp.theta_r < theta < dp.theta_s

        # Test conductivity
        K = dp.conductivity(-100)
        assert 0 < K < dp.Ks

    def test_validation(self):
        """Test model validation"""
        dp = DualPorosity(
            theta_r=0.078, theta_s=0.430,
            alpha1=0.1, n1=2.0,
            alpha2=0.01, n2=1.5,
            w2=0.3, Ks=24.96
        )

        assert dp.validate() is True


class TestCustomModel:
    """Test custom hydraulic model"""

    def test_custom_functions(self):
        """Test custom model with user functions"""
        def my_theta(h, a, b):
            if isinstance(h, np.ndarray):
                theta = np.full_like(h, 0.43)
                mask = h < 0
                theta[mask] = 0.078 + 0.352 * np.exp(a * h[mask] ** b)
                return theta
            else:
                if h >= 0:
                    return 0.43
                return 0.078 + 0.352 * np.exp(a * h ** b)

        def my_K(h, Ks, c):
            return Ks * np.exp(c * np.asarray(h))

        model = CustomHydraulicModel(
            theta_r=0.078, theta_s=0.43, Ks=24.96,
            theta_func=my_theta,
            K_func=my_K,
            a=0.001, b=0.8, c=0.01
        )

        # Test basic properties
        assert np.isclose(model.water_content(0), 0.43)
        theta = model.water_content(-100)
        assert 0.078 < theta < 0.43

        K = model.conductivity(-100)
        assert 0 < K < 24.96


class TestComparisons:
    """Test comparisons between models"""

    def test_vg_vs_bc_similar_soils(self):
        """Compare VG and BC for similar soils"""
        vg = VanGenuchten(
            theta_r=0.078, theta_s=0.430,
            alpha=0.036, n=1.56, Ks=24.96
        )

        bc = BrooksCorey(
            theta_r=0.078, theta_s=0.430,
            hb=-27.8, lambda_=0.36, Ks=24.96
        )

        # Both should give reasonable values
        h_test = np.array([-100, -50, -10])
        theta_vg = vg.water_content(h_test)
        theta_bc = bc.water_content(h_test)

        # Should be in same ballpark
        assert np.all(np.abs(theta_vg - theta_bc) < 0.1)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
