"""
Material Model Comparison Example
==================================

Compare different hydraulic models and visualize their properties.
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hydrus1dpy.materials import (
    VanGenuchten, BrooksCorey, DualPorosity,
    LogNormal, CustomHydraulicModel
)


def create_soil_models():
    """Create different hydraulic models for comparison"""
    # Loam soil - van Genuchten
    vg_loam = VanGenuchten(
        theta_r=0.078, theta_s=0.430,
        alpha=0.036, n=1.56, Ks=24.96,
        l=0.5
    )

    # Loam soil - Brooks-Corey (approximately equivalent)
    bc_loam = BrooksCorey(
        theta_r=0.078, theta_s=0.430,
        hb=-27.8, lambda_=0.36, Ks=24.96,
        l=2.0
    )

    # Structured soil - Dual porosity
    dp_structured = DualPorosity(
        theta_r=0.05, theta_s=0.45,
        alpha1=0.15, n1=2.5,   # Macro pores
        alpha2=0.01, n2=1.4,   # Micro pores
        w2=0.7, Ks=50.0
    )

    # Sand - van Genuchten
    vg_sand = VanGenuchten(
        theta_r=0.045, theta_s=0.430,
        alpha=0.145, n=2.68, Ks=712.8,
        l=0.5
    )

    # Clay - van Genuchten
    vg_clay = VanGenuchten(
        theta_r=0.068, theta_s=0.380,
        alpha=0.008, n=1.09, Ks=4.8,
        l=0.5
    )

    return {
        'VG Loam': vg_loam,
        'BC Loam': bc_loam,
        'Dual-P Structured': dp_structured,
        'VG Sand': vg_sand,
        'VG Clay': vg_clay
    }


def compare_retention_curves(models, h_range=None):
    """
    Compare water retention curves

    Parameters
    ----------
    models : dict
        Dictionary of {name: HydraulicModel}
    h_range : tuple, optional
        (h_min, h_max) in cm
    """
    if h_range is None:
        h_range = (-10000, 0)

    h = np.logspace(np.log10(-h_range[0]), np.log10(0.1), 1000)
    h = -h  # Make negative

    fig = go.Figure()

    for name, model in models.items():
        theta = model.water_content(h)

        fig.add_trace(go.Scatter(
            x=-h,  # Plot |h| on log scale
            y=theta,
            mode='lines',
            name=name,
            line=dict(width=2),
            hovertemplate='|h|: %{x:.1f} cm<br>θ: %{y:.4f}<extra></extra>'
        ))

    fig.update_layout(
        title='Water Retention Curves',
        xaxis_title='|Pressure Head| [cm]',
        yaxis_title='Water Content [-]',
        xaxis_type='log',
        template='plotly_white',
        width=800,
        height=600,
        font=dict(size=12),
        legend=dict(x=0.02, y=0.98)
    )

    return fig


def compare_conductivity_functions(models):
    """Compare hydraulic conductivity functions"""
    h = np.logspace(np.log10(0.1), np.log10(10000), 1000)
    h = -h

    fig = go.Figure()

    for name, model in models.items():
        K = model.conductivity(h)

        fig.add_trace(go.Scatter(
            x=-h,
            y=K,
            mode='lines',
            name=name,
            line=dict(width=2),
            hovertemplate='|h|: %{x:.1f} cm<br>K: %{y:.4e} cm/day<extra></extra>'
        ))

    fig.update_layout(
        title='Hydraulic Conductivity Functions',
        xaxis_title='|Pressure Head| [cm]',
        yaxis_title='Hydraulic Conductivity [cm/day]',
        xaxis_type='log',
        yaxis_type='log',
        template='plotly_white',
        width=800,
        height=600,
        font=dict(size=12),
        legend=dict(x=0.02, y=0.02)
    )

    return fig


def compare_water_capacity(models):
    """Compare water capacity functions"""
    h = np.logspace(np.log10(0.1), np.log10(10000), 1000)
    h = -h

    fig = go.Figure()

    for name, model in models.items():
        C = model.capacity(h)

        fig.add_trace(go.Scatter(
            x=-h,
            y=C,
            mode='lines',
            name=name,
            line=dict(width=2),
            hovertemplate='|h|: %{x:.1f} cm<br>C: %{y:.4e} 1/cm<extra></extra>'
        ))

    fig.update_layout(
        title='Water Capacity (dθ/dh)',
        xaxis_title='|Pressure Head| [cm]',
        yaxis_title='Water Capacity [1/cm]',
        xaxis_type='log',
        yaxis_type='log',
        template='plotly_white',
        width=800,
        height=600,
        font=dict(size=12),
        legend=dict(x=0.98, y=0.98, xanchor='right')
    )

    return fig


def create_dashboard(models):
    """Create comprehensive dashboard with all comparisons"""
    h = np.logspace(np.log10(0.1), np.log10(10000), 1000)
    h = -h

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Water Retention Curve',
            'Hydraulic Conductivity',
            'Water Capacity',
            'Relative Conductivity'
        ),
        specs=[
            [{'type': 'scatter'}, {'type': 'scatter'}],
            [{'type': 'scatter'}, {'type': 'scatter'}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.10
    )

    for name, model in models.items():
        theta = model.water_content(h)
        K = model.conductivity(h)
        C = model.capacity(h)
        Kr = model.relative_conductivity(h)

        # Retention curve
        fig.add_trace(
            go.Scatter(x=-h, y=theta, mode='lines', name=name,
                      showlegend=True, line=dict(width=2)),
            row=1, col=1
        )

        # Conductivity
        fig.add_trace(
            go.Scatter(x=-h, y=K, mode='lines', name=name,
                      showlegend=False, line=dict(width=2)),
            row=1, col=2
        )

        # Capacity
        fig.add_trace(
            go.Scatter(x=-h, y=C, mode='lines', name=name,
                      showlegend=False, line=dict(width=2)),
            row=2, col=1
        )

        # Relative conductivity
        fig.add_trace(
            go.Scatter(x=-h, y=Kr, mode='lines', name=name,
                      showlegend=False, line=dict(width=2)),
            row=2, col=2
        )

    # Update axes
    fig.update_xaxes(type='log', title_text='|h| [cm]', row=1, col=1)
    fig.update_xaxes(type='log', title_text='|h| [cm]', row=1, col=2)
    fig.update_xaxes(type='log', title_text='|h| [cm]', row=2, col=1)
    fig.update_xaxes(type='log', title_text='|h| [cm]', row=2, col=2)

    fig.update_yaxes(title_text='θ [-]', row=1, col=1)
    fig.update_yaxes(type='log', title_text='K [cm/day]', row=1, col=2)
    fig.update_yaxes(type='log', title_text='C [1/cm]', row=2, col=1)
    fig.update_yaxes(type='log', title_text='Kr [-]', row=2, col=2)

    fig.update_layout(
        title_text='Soil Hydraulic Properties Comparison',
        height=900,
        width=1200,
        template='plotly_white',
        font=dict(size=10)
    )

    return fig


def example_model_validation():
    """Example: Validate a hydraulic model"""
    print("=" * 70)
    print("Model Validation Example")
    print("=" * 70)

    vg = VanGenuchten(
        theta_r=0.078, theta_s=0.430,
        alpha=0.036, n=1.56, Ks=24.96
    )

    print(f"\nModel: {vg}")
    print(f"\nCalculated m parameter: {vg.m:.4f}")
    print(f"Air-entry value (approx): {vg.air_entry_value():.2f} cm")

    h_inf, theta_inf, C_max = vg.inflection_point()
    print(f"\nInflection point:")
    print(f"  h = {h_inf:.2f} cm")
    print(f"  θ = {theta_inf:.4f}")
    print(f"  C_max = {C_max:.4e} 1/cm")

    print(f"\nValidating model...")
    try:
        vg.validate()
        print("✓ Model passed all validation checks")
    except AssertionError as e:
        print(f"✗ Validation failed: {e}")

    print(f"\nTesting inverse function:")
    for theta_test in [0.1, 0.2, 0.3, 0.4]:
        if vg.theta_r <= theta_test <= vg.theta_s:
            h = vg.pressure_head(theta_test)
            theta_back = vg.water_content(h)
            error = abs(theta_test - theta_back)
            print(f"  θ={theta_test:.3f} → h={h:.2f} → θ={theta_back:.3f} (error={error:.2e})")


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("HYDRUS1D Phase 2: Material Model Comparison")
    print("=" * 70 + "\n")

    # Create models
    models = create_soil_models()

    print(f"Created {len(models)} hydraulic models:")
    for name, model in models.items():
        print(f"  - {name}")

    # Model validation
    example_model_validation()

    # Create comparison plots
    print("\n" + "=" * 70)
    print("Creating Comparison Plots")
    print("=" * 70)

    fig1 = compare_retention_curves(models)
    fig1.write_html('./retention_curves.html')
    print("✓ Retention curves saved to: retention_curves.html")

    fig2 = compare_conductivity_functions(models)
    fig2.write_html('./conductivity_functions.html')
    print("✓ Conductivity functions saved to: conductivity_functions.html")

    fig3 = compare_water_capacity(models)
    fig3.write_html('./water_capacity.html')
    print("✓ Water capacity saved to: water_capacity.html")

    fig4 = create_dashboard(models)
    fig4.write_html('./hydraulic_properties_dashboard.html')
    print("✓ Dashboard saved to: hydraulic_properties_dashboard.html")

    print("\n" + "=" * 70)
    print("Examples completed successfully!")
    print("=" * 70)
    print("\nOpen the HTML files in a web browser to view interactive plots.")


if __name__ == '__main__':
    main()
