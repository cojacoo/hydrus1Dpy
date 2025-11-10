"""
Plotly visualization for HYDRUS1D results
==========================================

Interactive plots for profiles, time series, and mass balance
"""

from typing import List, Optional, Union
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..io.data_structures import ModelResults


class HydrusVisualizer:
    """
    Create interactive visualizations of HYDRUS results using Plotly

    Examples
    --------
    >>> viz = HydrusVisualizer(results)
    >>> fig = viz.plot_profile([0, 1, 5, 10], variable='theta')
    >>> fig.show()
    """

    def __init__(self, results: ModelResults):
        """
        Initialize visualizer

        Parameters
        ----------
        results : ModelResults
            HYDRUS1D simulation results
        """
        self.results = results

    def plot_profile(self,
                    times: Union[List[float], float],
                    variable: str = 'h',
                    title: Optional[str] = None) -> go.Figure:
        """
        Plot vertical profiles at specified times

        Parameters
        ----------
        times : list of float or float
            Times to plot (can be single value or list)
        variable : str
            Variable to plot ('h', 'theta', 'K', 'C', 'v')
        title : str, optional
            Plot title (auto-generated if None)

        Returns
        -------
        fig : plotly.graph_objects.Figure
            Interactive Plotly figure
        """
        if isinstance(times, (int, float)):
            times = [times]

        fig = go.Figure()

        # Variable labels
        labels = {
            'h': 'Pressure Head [cm]',
            'theta': 'Water Content [-]',
            'K': 'Hydraulic Conductivity [cm/day]',
            'C': 'Water Capacity [1/cm]',
            'v': 'Water Flux [cm/day]',
            'Temp': 'Temperature [°C]'
        }

        # Plot each time
        for t in times:
            try:
                profile = self.results.get_profile(t, variable)
                profile_data = self.results.profiles[t]
                depths = profile_data['depth'].values

                fig.add_trace(go.Scatter(
                    x=profile.values,
                    y=depths,
                    mode='lines+markers',
                    name=f't = {t:.2f}',
                    hovertemplate='Depth: %{y:.1f} cm<br>' + f'{variable}: %{{x:.4f}}<extra></extra>',
                    line=dict(width=2),
                    marker=dict(size=6)
                ))
            except (KeyError, ValueError) as e:
                print(f"Warning: Could not plot time {t}: {e}")
                continue

        # Formatting
        if title is None:
            title = f'Vertical Profile: {labels.get(variable, variable)}'

        fig.update_layout(
            title=title,
            xaxis_title=labels.get(variable, variable),
            yaxis_title='Depth [cm]',
            yaxis=dict(autorange='reversed'),  # Depth increases downward
            hovermode='closest',
            template='plotly_white',
            font=dict(size=12),
            width=700,
            height=600,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            )
        )

        # Add zero line for pressure head
        if variable == 'h':
            fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)

        return fig

    def plot_timeseries(self,
                       nodes: Optional[List[int]] = None,
                       variable: str = 'h',
                       title: Optional[str] = None) -> go.Figure:
        """
        Plot time series at observation nodes

        Parameters
        ----------
        nodes : list of int, optional
            Observation node numbers (uses all if None)
        variable : str
            Variable to plot ('h', 'theta', etc.)
        title : str, optional
            Plot title

        Returns
        -------
        fig : plotly.graph_objects.Figure
            Interactive Plotly figure
        """
        if self.results.obs_node_data is None:
            raise ValueError("No observation node data available")

        fig = go.Figure()

        # Variable labels
        labels = {
            'h': 'Pressure Head [cm]',
            'theta': 'Water Content [-]',
            'K': 'Hydraulic Conductivity [cm/day]',
            'Temp': 'Temperature [°C]'
        }

        # Get available observation nodes
        if nodes is None:
            # Find all columns for this variable
            nodes = []
            for col in self.results.obs_node_data.columns:
                if col.startswith(variable) and col[len(variable):].isdigit():
                    nodes.append(int(col[len(variable):]))

        # Get time column
        time_col = 'time' if 'time' in self.results.obs_node_data.columns else self.results.obs_node_data.columns[0]
        time = self.results.obs_node_data[time_col].values

        # Plot each node
        for node in nodes:
            col_name = f'{variable}{node}'
            if col_name in self.results.obs_node_data.columns:
                values = self.results.obs_node_data[col_name].values

                fig.add_trace(go.Scatter(
                    x=time,
                    y=values,
                    mode='lines',
                    name=f'Node {node}',
                    hovertemplate='Time: %{x:.2f}<br>' + f'{variable}: %{{y:.4f}}<extra></extra>',
                    line=dict(width=2)
                ))

        # Formatting
        if title is None:
            title = f'Time Series: {labels.get(variable, variable)}'

        fig.update_layout(
            title=title,
            xaxis_title='Time [days]',
            yaxis_title=labels.get(variable, variable),
            hovermode='x unified',
            template='plotly_white',
            font=dict(size=12),
            width=800,
            height=500,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            )
        )

        return fig

    def plot_mass_balance(self, title: Optional[str] = None) -> go.Figure:
        """
        Plot cumulative mass balance components

        Returns
        -------
        fig : plotly.graph_objects.Figure
            Interactive Plotly figure
        """
        if self.results.mass_balance is None:
            raise ValueError("No mass balance data available")

        df = self.results.mass_balance

        fig = go.Figure()

        # Define components to plot (cumulative values)
        components = {
            'cum_vTop': ('Top Flux', 'blue'),
            'cum_vBot': ('Bottom Flux', 'green'),
            'cum_rRoot': ('Root Uptake', 'orange'),
        }

        # Plot each component if available
        for col_name, (label, color) in components.items():
            if col_name in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['time'],
                    y=df[col_name],
                    mode='lines',
                    name=label,
                    line=dict(color=color, width=2),
                    hovertemplate='Time: %{x:.2f}<br>Cum. flux: %{y:.4f} cm<extra></extra>'
                ))

        # Formatting
        if title is None:
            title = 'Cumulative Mass Balance'

        fig.update_layout(
            title=title,
            xaxis_title='Time [days]',
            yaxis_title='Cumulative Water [cm]',
            hovermode='x unified',
            template='plotly_white',
            font=dict(size=12),
            width=800,
            height=500,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        return fig

    def plot_water_balance_error(self) -> go.Figure:
        """
        Plot water balance error over time

        Returns
        -------
        fig : plotly.graph_objects.Figure
            Interactive Plotly figure
        """
        if self.results.mass_balance is None:
            raise ValueError("No mass balance data available")

        df = self.results.mass_balance

        # Calculate balance error if not already in data
        # Error = Inflow - Outflow - Storage change
        if 'cum_error' in df.columns:
            error = df['cum_error']
        else:
            # Estimate from available data
            inflow = df.get('cum_vTop', 0) + df.get('cum_rTop', 0)
            outflow = df.get('cum_vBot', 0) + df.get('cum_rRoot', 0)
            # Rough estimate (proper calculation needs storage)
            error = inflow - outflow

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['time'],
            y=error,
            mode='lines',
            name='Balance Error',
            line=dict(color='red', width=2),
            fill='tozeroy',
            hovertemplate='Time: %{x:.2f}<br>Error: %{y:.4e} cm<extra></extra>'
        ))

        fig.update_layout(
            title='Water Balance Error',
            xaxis_title='Time [days]',
            yaxis_title='Cumulative Error [cm]',
            hovermode='x unified',
            template='plotly_white',
            font=dict(size=12),
            width=800,
            height=400
        )

        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

        return fig

    def plot_animation(self, variable: str = 'theta', interval: int = 100) -> go.Figure:
        """
        Create animated profile evolution

        Parameters
        ----------
        variable : str
            Variable to animate
        interval : int
            Frame interval in milliseconds

        Returns
        -------
        fig : plotly.graph_objects.Figure
            Animated Plotly figure
        """
        times = sorted(self.results.profiles.keys())

        if not times:
            raise ValueError("No profile data available")

        # Get first profile for initialization
        first_profile = self.results.profiles[times[0]]
        depths = first_profile['depth'].values
        values_0 = first_profile[variable].values

        # Create frames
        frames = []
        for t in times:
            profile = self.results.profiles[t]
            values = profile[variable].values

            frame = go.Frame(
                data=[go.Scatter(
                    x=values,
                    y=depths,
                    mode='lines+markers',
                    line=dict(width=2),
                    marker=dict(size=6)
                )],
                name=f'{t:.2f}',
                layout=go.Layout(title_text=f'Time: {t:.2f} days')
            )
            frames.append(frame)

        # Initial plot
        fig = go.Figure(
            data=[go.Scatter(
                x=values_0,
                y=depths,
                mode='lines+markers',
                line=dict(width=2),
                marker=dict(size=6)
            )],
            frames=frames
        )

        # Variable labels
        labels = {
            'h': 'Pressure Head [cm]',
            'theta': 'Water Content [-]',
            'K': 'Hydraulic Conductivity [cm/day]'
        }

        # Add play/pause buttons
        fig.update_layout(
            updatemenus=[{
                'type': 'buttons',
                'showactive': False,
                'x': 0.1,
                'y': 0.0,
                'xanchor': 'right',
                'yanchor': 'top',
                'buttons': [
                    {
                        'label': '▶ Play',
                        'method': 'animate',
                        'args': [None, {
                            'frame': {'duration': interval, 'redraw': True},
                            'fromcurrent': True,
                            'mode': 'immediate',
                            'transition': {'duration': 0}
                        }]
                    },
                    {
                        'label': '⏸ Pause',
                        'method': 'animate',
                        'args': [[None], {
                            'frame': {'duration': 0, 'redraw': False},
                            'mode': 'immediate',
                            'transition': {'duration': 0}
                        }]
                    }
                ]
            }],
            sliders=[{
                'active': 0,
                'yanchor': 'top',
                'y': 0.0,
                'xanchor': 'left',
                'x': 0.15,
                'currentvalue': {
                    'prefix': 'Time: ',
                    'suffix': ' days',
                    'visible': True,
                    'xanchor': 'right'
                },
                'len': 0.8,
                'steps': [
                    {
                        'args': [[f.name], {
                            'frame': {'duration': 0, 'redraw': True},
                            'mode': 'immediate',
                            'transition': {'duration': 0}
                        }],
                        'label': f'{float(f.name):.1f}',
                        'method': 'animate'
                    } for f in frames
                ]
            }],
            xaxis_title=labels.get(variable, variable),
            yaxis_title='Depth [cm]',
            yaxis=dict(autorange='reversed'),
            template='plotly_white',
            font=dict(size=12),
            width=700,
            height=600
        )

        return fig

    def create_dashboard(self, variables: List[str] = None) -> go.Figure:
        """
        Create multi-panel dashboard

        Parameters
        ----------
        variables : list of str, optional
            Variables to include in dashboard

        Returns
        -------
        fig : plotly.graph_objects.Figure
            Dashboard figure with subplots
        """
        if variables is None:
            variables = ['h', 'theta']

        n_vars = len(variables)

        # Create subplots: profiles on left, time series on right
        fig = make_subplots(
            rows=n_vars,
            cols=2,
            subplot_titles=['Profiles', 'Time Series'],
            horizontal_spacing=0.12,
            vertical_spacing=0.15
        )

        # Variable labels
        labels = {
            'h': 'Pressure Head [cm]',
            'theta': 'Water Content [-]',
            'K': 'Hydraulic Conductivity [cm/day]'
        }

        # Get some representative times
        times = sorted(self.results.profiles.keys())
        plot_times = [times[i] for i in [0, len(times)//2, -1]] if len(times) > 2 else times

        # Plot each variable
        for i, var in enumerate(variables, 1):
            # Profiles
            for t in plot_times:
                try:
                    profile = self.results.get_profile(t, var)
                    profile_data = self.results.profiles[t]
                    depths = profile_data['depth'].values

                    fig.add_trace(
                        go.Scatter(
                            x=profile.values,
                            y=depths,
                            mode='lines+markers',
                            name=f't={t:.1f}',
                            showlegend=(i == 1),
                            line=dict(width=2),
                            marker=dict(size=4)
                        ),
                        row=i, col=1
                    )
                except:
                    pass

            # Time series (if observation data available)
            if self.results.obs_node_data is not None:
                time_col = 'time' if 'time' in self.results.obs_node_data.columns else self.results.obs_node_data.columns[0]
                time = self.results.obs_node_data[time_col].values

                # Find observation columns for this variable
                for col in self.results.obs_node_data.columns:
                    if col.startswith(var) and len(col) > len(var):
                        values = self.results.obs_node_data[col].values
                        node_num = col[len(var):]

                        fig.add_trace(
                            go.Scatter(
                                x=time,
                                y=values,
                                mode='lines',
                                name=f'Node {node_num}',
                                showlegend=(i == 1),
                                line=dict(width=2)
                            ),
                            row=i, col=2
                        )

            # Update axes
            fig.update_yaxes(title_text=labels.get(var, var), row=i, col=1, autorange='reversed')
            fig.update_yaxes(title_text=labels.get(var, var), row=i, col=2)
            fig.update_xaxes(title_text=labels.get(var, var), row=i, col=1)
            fig.update_xaxes(title_text='Time [days]', row=i, col=2)

        fig.update_layout(
            title_text='HYDRUS1D Results Dashboard',
            height=400 * n_vars,
            width=1200,
            template='plotly_white',
            font=dict(size=10)
        )

        return fig
