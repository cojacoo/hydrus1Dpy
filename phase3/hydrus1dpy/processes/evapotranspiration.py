"""
Evapotranspiration Calculations for HYDRUS1D Phase 3
====================================================

Implements Penman-Monteith and other ET estimation methods.

Author: HYDRUS1DPy Development Team

References
----------
Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998).
Crop evapotranspiration - Guidelines for computing crop water requirements.
FAO Irrigation and drainage paper 56. FAO, Rome, 300(9), D05109.

Penman, H. L. (1948).
Natural evaporation from open water, bare soil and grass.
Proceedings of the Royal Society of London. Series A, 193(1032), 120-145.

Monteith, J. L. (1965).
Evaporation and environment. In Symposia of the society for experimental
biology (Vol. 19, pp. 205-234). Cambridge University Press (CUP) Cambridge.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Callable


@dataclass
class WeatherData:
    """
    Weather/climate data for ET calculation.

    Parameters
    ----------
    time : float
        Time [days]
    temperature : float
        Air temperature [°C]
    relative_humidity : float
        Relative humidity [%]
    wind_speed : float
        Wind speed at 2m height [m/s]
    solar_radiation : float
        Solar radiation [MJ/m²/day]
    pressure : float, optional
        Atmospheric pressure [kPa] (default: 101.3)
    """
    time: float
    temperature: float
    relative_humidity: float
    wind_speed: float
    solar_radiation: float
    pressure: float = 101.3

    def validate(self):
        """Validate weather data ranges."""
        if not -50 <= self.temperature <= 60:
            raise ValueError(f"Temperature {self.temperature}°C out of range")
        if not 0 <= self.relative_humidity <= 100:
            raise ValueError(f"RH {self.relative_humidity}% out of range")
        if self.wind_speed < 0:
            raise ValueError(f"Wind speed cannot be negative")
        if self.solar_radiation < 0:
            raise ValueError(f"Solar radiation cannot be negative")


class PenmanMonteith:
    """
    FAO-56 Penman-Monteith reference evapotranspiration.

    Calculates reference ET (ET₀) for a hypothetical grass reference surface.

    Parameters
    ----------
    latitude : float
        Site latitude [degrees] for extraterrestrial radiation
    elevation : float, optional
        Site elevation [m] for atmospheric pressure (default: 0)
    albedo : float, optional
        Surface albedo (default: 0.23 for grass)
    crop_height : float, optional
        Crop/vegetation height [m] (default: 0.12 for grass)

    Examples
    --------
    >>> pm = PenmanMonteith(latitude=52.0, elevation=100)
    >>> weather = WeatherData(
    ...     time=180,  # Day of year
    ...     temperature=20,
    ...     relative_humidity=50,
    ...     wind_speed=2.0,
    ...     solar_radiation=20.0
    ... )
    >>> et0 = pm.calculate_et0(weather)
    >>> print(f"ET₀ = {et0:.2f} mm/day")
    """

    def __init__(
        self,
        latitude: float,
        elevation: float = 0.0,
        albedo: float = 0.23,
        crop_height: float = 0.12
    ):
        self.latitude = np.deg2rad(latitude)
        self.elevation = elevation
        self.albedo = albedo
        self.crop_height = crop_height

        # Calculate atmospheric pressure from elevation
        # P = 101.3 * ((293 - 0.0065*z) / 293)^5.26
        self.pressure = 101.3 * ((293 - 0.0065 * elevation) / 293) ** 5.26

    def calculate_et0(self, weather: WeatherData) -> float:
        """
        Calculate reference ET using FAO-56 Penman-Monteith.

        Parameters
        ----------
        weather : WeatherData
            Weather conditions

        Returns
        -------
        et0 : float
            Reference evapotranspiration [mm/day]

        Notes
        -----
        FAO-56 Penman-Monteith equation:

        ET₀ = (0.408 Δ(Rn - G) + γ(900/(T+273))u₂(es - ea)) / (Δ + γ(1 + 0.34u₂))

        where:
        - Δ = slope of saturation vapor pressure curve [kPa/°C]
        - Rn = net radiation [MJ/m²/day]
        - G = soil heat flux [MJ/m²/day] (≈ 0 for daily)
        - γ = psychrometric constant [kPa/°C]
        - T = air temperature [°C]
        - u₂ = wind speed at 2m [m/s]
        - es = saturation vapor pressure [kPa]
        - ea = actual vapor pressure [kPa]
        """
        weather.validate()

        T = weather.temperature
        RH = weather.relative_humidity
        u2 = weather.wind_speed
        Rs = weather.solar_radiation

        # Saturation vapor pressure [kPa]
        es = 0.6108 * np.exp((17.27 * T) / (T + 237.3))

        # Actual vapor pressure [kPa]
        ea = es * RH / 100.0

        # Slope of saturation vapor pressure curve [kPa/°C]
        delta = (4098 * es) / (T + 237.3) ** 2

        # Psychrometric constant [kPa/°C]
        gamma = 0.665e-3 * self.pressure

        # Net radiation [MJ/m²/day]
        # Simplified: Rn ≈ (1 - albedo) * Rs - net longwave
        # For daily calculation, assume net longwave ≈ 0.1 * Rs
        Rn = (1 - self.albedo) * Rs - 0.1 * Rs

        # Soil heat flux [MJ/m²/day] - negligible for daily timestep
        G = 0.0

        # Reference ET [mm/day]
        numerator = 0.408 * delta * (Rn - G) + gamma * (900 / (T + 273)) * u2 * (es - ea)
        denominator = delta + gamma * (1 + 0.34 * u2)

        et0 = numerator / denominator

        # Ensure non-negative
        et0 = max(0.0, et0)

        return et0


class SimpleET:
    """
    Simple evapotranspiration model with default reference ET.

    Uses a constant reference ET when no weather data is available.

    Parameters
    ----------
    et0_default : float, optional
        Default reference ET [mm/day] (default: 4.0 mm/day)

    Examples
    --------
    >>> simple_et = SimpleET(et0_default=4.0)
    >>> et = simple_et.calculate_et(time=10.0)
    >>> print(f"ET = {et:.2f} mm/day")
    """

    def __init__(self, et0_default: float = 4.0):
        self.et0_default = et0_default

    def calculate_et(self, time: float) -> float:
        """
        Calculate ET using default value.

        Parameters
        ----------
        time : float
            Current time [days]

        Returns
        -------
        et : float
            Evapotranspiration [mm/day]
        """
        return self.et0_default


class ETCalculator:
    """
    Flexible ET calculator supporting multiple methods.

    Parameters
    ----------
    method : str
        ET calculation method:
        - 'penman_monteith': FAO-56 Penman-Monteith (requires weather data)
        - 'simple': Constant default value
    weather_func : callable, optional
        Function returning WeatherData for given time: weather_func(t) -> WeatherData
        Required for 'penman_monteith' method
    et0_default : float, optional
        Default ET [mm/day] for 'simple' method (default: 4.0)
    latitude : float, optional
        Site latitude [degrees] for Penman-Monteith
    elevation : float, optional
        Site elevation [m] for Penman-Monteith

    Examples
    --------
    >>> # Simple constant ET
    >>> et_calc = ETCalculator(method='simple', et0_default=4.0)
    >>> et = et_calc.calculate(time=10.0)

    >>> # Penman-Monteith with weather data
    >>> def get_weather(t):
    ...     return WeatherData(
    ...         time=t,
    ...         temperature=20 + 5*np.sin(2*np.pi*t/365),
    ...         relative_humidity=60,
    ...         wind_speed=2.0,
    ...         solar_radiation=15.0
    ...     )
    >>> et_calc = ETCalculator(
    ...     method='penman_monteith',
    ...     weather_func=get_weather,
    ...     latitude=52.0
    ... )
    >>> et = et_calc.calculate(time=180.0)
    """

    def __init__(
        self,
        method: str = 'simple',
        weather_func: Optional[Callable] = None,
        et0_default: float = 4.0,
        latitude: float = 0.0,
        elevation: float = 0.0
    ):
        self.method = method

        if method == 'penman_monteith':
            if weather_func is None:
                raise ValueError("weather_func required for Penman-Monteith method")
            self.weather_func = weather_func
            self.pm = PenmanMonteith(latitude=latitude, elevation=elevation)

        elif method == 'simple':
            self.simple_et = SimpleET(et0_default=et0_default)

        else:
            raise ValueError(f"Unknown ET method: {method}")

    def calculate(self, time: float) -> float:
        """
        Calculate potential ET at given time.

        Parameters
        ----------
        time : float
            Current time [days]

        Returns
        -------
        et : float
            Potential evapotranspiration [mm/day]
        """
        if self.method == 'penman_monteith':
            weather = self.weather_func(time)
            et = self.pm.calculate_et0(weather)

        elif self.method == 'simple':
            et = self.simple_et.calculate_et(time)

        return et


def pf_to_head(pf: float) -> float:
    """
    Convert pF value to pressure head.

    Parameters
    ----------
    pf : float
        pF value (log10 of absolute pressure head in cm)

    Returns
    -------
    h : float
        Pressure head [cm] (negative)

    Examples
    --------
    >>> h_wilting = pf_to_head(4.2)  # Wilting point
    >>> print(f"h = {h_wilting:.0f} cm")
    h = -15849 cm

    >>> h_stage2 = pf_to_head(4.5)  # Stage 2 evaporation threshold
    >>> print(f"h = {h_stage2:.0f} cm")
    h = -31623 cm
    """
    return -10 ** pf


def head_to_pf(h: float) -> float:
    """
    Convert pressure head to pF value.

    Parameters
    ----------
    h : float
        Pressure head [cm] (should be negative)

    Returns
    -------
    pf : float
        pF value

    Examples
    --------
    >>> pf = head_to_pf(-15849)
    >>> print(f"pF = {pf:.1f}")
    pF = 4.2
    """
    if h >= 0:
        return 0.0
    return np.log10(-h)
