"""
Quantum Yield Calculator Utilities
Calculation functions for photon absorption and quantum yield analysis
"""

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


def load_absorbance_data(uploaded_file):
    """
    Load absorbance data from Excel file.
    Expected format: Column 1 = wavelengths, Column 2 = absorbance values

    Returns:
        tuple: (raw_abs array, error message or None)
    """
    try:
        if uploaded_file is None:
            return None, "No file uploaded"

        df = pd.read_excel(uploaded_file, header=None)
        if df.shape[1] < 2:
            return None, "File must have at least 2 columns (wavelength, absorbance)"

        data = df.values

        if len(data) < 2:
            return None, "File must have at least 2 data rows"

        try:
            wavelengths = pd.to_numeric(data[:, 0])
            absorbance = pd.to_numeric(data[:, 1])
        except Exception:
            return None, "Columns must contain numeric values"

        if not np.all(np.diff(wavelengths) > 0):
            return None, "Wavelengths must be in increasing order"

        return data, None

    except Exception as e:
        return None, f"Error loading file: {str(e)}"


def calculate_extinction(raw_abs, l1, c1):
    """
    Calculate extinction coefficient from raw absorbance data.
    Formula: Extinction = Absorbance / (pathlength * concentration)

    Returns:
        tuple: (wavelengths array, extinction array, error message or None)
    """
    try:
        if l1 <= 0 or c1 <= 0:
            return None, None, "Pathlength and concentration must be positive"

        wavelengths = raw_abs[:, 0].astype(float)
        absorbance = raw_abs[:, 1].astype(float)

        extinction = absorbance / (l1 * c1)

        return wavelengths, extinction, None

    except Exception as e:
        return None, None, f"Error calculating extinction: {str(e)}"


def calculate_new_absorbance(extinction, l2, c2):
    """
    Scale extinction coefficient to new pathlength and concentration.
    Formula: NewABS = Extinction * L2 * C2

    Returns:
        tuple: (new_abs array, error message or None)
    """
    try:
        if l2 <= 0 or c2 <= 0:
            return None, "Pathlength and concentration must be positive"

        new_abs = extinction * l2 * c2
        return new_abs, None

    except Exception as e:
        return None, f"Error calculating new absorbance: {str(e)}"


def load_led_data(uploaded_file):
    """
    Load LED emission data from Excel file.
    Expected format: Column 1 = wavelengths, Column 2 = emission intensity

    Returns:
        tuple: (raw_led array, error message or None)
    """
    try:
        if uploaded_file is None:
            return None, "No file uploaded"

        df = pd.read_excel(uploaded_file, header=None)
        if df.shape[1] < 2:
            return None, "File must have at least 2 columns (wavelength, emission)"

        data = df.values

        if len(data) < 2:
            return None, "File must have at least 2 data rows"

        try:
            wavelengths = pd.to_numeric(data[:, 0])
            emission = pd.to_numeric(data[:, 1])
        except Exception:
            return None, "Columns must contain numeric values"

        if not np.all(np.diff(wavelengths) > 0):
            return None, "Wavelengths must be in increasing order"

        return data, None

    except Exception as e:
        return None, f"Error loading LED file: {str(e)}"


def baseline_led(raw_led):
    """
    Baseline LED emission by subtracting minimum value.
    Formula: BaseLED = RawLED(:,2) - min(RawLED(:,2))

    Returns:
        tuple: (base_led array, led_min value, error message or None)
    """
    try:
        led_emission = raw_led[:, 1].astype(float)
        led_min = np.min(led_emission)
        base_led = led_emission - led_min

        return base_led, led_min, None

    except Exception as e:
        return None, None, f"Error baselining LED: {str(e)}"


def normalize_led_area(wavelengths, base_led, intensity):
    """
    Normalize LED by integrating area under curve to equal intensity.
    Formula:
        # UPDATE, numpy doesn't have .trapz anymore
        LEDIntegral = trapezoid(wavelengths, BaseLED)
        ConversionFactor = LEDIntegral / Intensity
        LEDAreaNorm = BaseLED / ConversionFactor

    Returns:
        tuple: (normalized_led array, conversion_factor, error message or None)
    """
    try:
        wavelengths = np.asarray(wavelengths, dtype=float)
        base_led = np.asarray(base_led, dtype=float)

        if intensity <= 0:
            return None, None, "Intensity must be positive"

        # UPDATE, numpy doesn't have .trapz anymore
        led_integral = np.trapezoid(base_led, wavelengths)

        if led_integral == 0:
            return None, None, "LED integral is zero"

        conversion_factor = led_integral / intensity
        led_area_norm = base_led / conversion_factor

        return led_area_norm, conversion_factor, None

    except Exception as e:
        return None, None, f"Error normalizing LED area: {str(e)}"


def interpolate_absorbance_to_led(abs_wavelengths, new_abs, led_wavelengths):
    """
    Interpolate absorbance values onto the LED wavelength grid.

    Returns:
        tuple: (interpolated_absorbance array, error message or None)
    """
    try:
        abs_wavelengths = np.asarray(abs_wavelengths, dtype=float)
        new_abs = np.asarray(new_abs, dtype=float)
        led_wavelengths = np.asarray(led_wavelengths, dtype=float)

        if len(abs_wavelengths) != len(new_abs):
            return None, "Absorbance wavelength and absorbance arrays must have the same length"

        if not np.all(np.diff(abs_wavelengths) > 0):
            return None, "Absorbance wavelengths must be strictly increasing"

        if led_wavelengths.min() < abs_wavelengths.min() or led_wavelengths.max() > abs_wavelengths.max():
            return None, (
                "LED wavelength range extends beyond absorbance wavelength range. "
                "Please use absorbance data covering the full LED spectrum."
            )

        interp_abs = np.interp(led_wavelengths, abs_wavelengths, new_abs)
        return interp_abs, None

    except Exception as e:
        return None, f"Error interpolating absorbance to LED wavelengths: {str(e)}"


def gaussian_fit_led(wavelengths, emission, n_gaussians=2):
    """
    Fit Gaussian curve(s) to LED emission spectrum.

    Returns:
        tuple: (fit_function, fitted_values_at_original_wavelengths, error message or None)
    """
    try:
        wavelengths = np.asarray(wavelengths, dtype=float)
        emission = np.asarray(emission, dtype=float)

        def multi_gaussian(x, *params):
            result = np.zeros_like(x, dtype=float)
            n_params = len(params) // 3
            for i in range(n_params):
                a = params[3 * i]
                b = params[3 * i + 1]
                c = params[3 * i + 2]
                result += a * np.exp(-((x - b) / c) ** 2)
            return result

        p0 = []
        lower_bounds = []
        upper_bounds = []

        step = max(1, len(wavelengths) // (n_gaussians + 1))

        for i in range(n_gaussians):
            idx = min((i + 1) * step, len(wavelengths) - 1)

            p0.extend([
                max(np.max(emission) / n_gaussians, 1e-12),  # amplitude
                wavelengths[idx],                            # center
                10.0                                         # width
            ])

            lower_bounds.extend([0.0, wavelengths.min(), 1e-6])
            upper_bounds.extend([np.inf, wavelengths.max(), np.ptp(wavelengths) * 2])

        popt, _ = curve_fit(
            multi_gaussian,
            wavelengths,
            emission,
            p0=p0,
            bounds=(lower_bounds, upper_bounds),
            maxfev=20000
        )

        fitted_values = multi_gaussian(wavelengths, *popt)

        return lambda x: multi_gaussian(np.asarray(x, dtype=float), *popt), fitted_values, None

    except Exception as e:
        return None, None, f"Error fitting Gaussian to LED: {str(e)}"


def validate_led_areas(wavelengths, led_area_norm, fitted_led, target_intensity):
    """
    Validate that the normalized LED integrates to the target intensity,
    and show how much the Gaussian fit changes that area.

    Returns:
        dict with normalized_area, fitted_area, target_intensity, errors
    """
    try:
        wavelengths = np.asarray(wavelengths, dtype=float)
        led_area_norm = np.asarray(led_area_norm, dtype=float)
        fitted_led = np.asarray(fitted_led, dtype=float)

        # UPDATE, numpy doesn't have .trapz anymore
        normalized_area = np.trapezoid(led_area_norm, wavelengths)
        fitted_area = np.trapezoid(fitted_led, wavelengths)

        return {
            "normalized_area": normalized_area,
            "fitted_area": fitted_area,
            "target_intensity": target_intensity,
            "normalized_error": normalized_area - target_intensity,
            "fitted_error": fitted_area - target_intensity,
            "error": None
        }

    except Exception as e:
        return {
            "error": f"Error validating LED areas: {str(e)}"
        }


def calculate_photon_metrics(wavelengths, led_spectrum, absorbance):
    """
    Calculate photon-related metrics: energy, photon count,
    transmission fraction, and absorption fraction.

    Args:
        wavelengths: Wavelength array (nm)
        led_spectrum: LED emission spectrum (mW/cm²/nm)
        absorbance: Absorbance values on the SAME wavelength grid

    Returns:
        dict with keys: 'NRG', 'NP', 'FPT', 'FPA', 'error'
    """
    try:
        wavelengths = np.asarray(wavelengths, dtype=float)
        led_spectrum = np.asarray(led_spectrum, dtype=float)
        absorbance = np.asarray(absorbance, dtype=float)

        if not (len(wavelengths) == len(led_spectrum) == len(absorbance)):
            return {'error': "Wavelengths, LED spectrum, and absorbance must all have the same length"}

        h = 6.626e-34
        c = 299792458

        wavelengths_m = wavelengths * 1e-9
        nrg = h * c / wavelengths_m

        np_array = led_spectrum / 1000.0 / nrg
        fpt = 10 ** (-absorbance)
        fpa = 1 - fpt

        return {
            'NRG': nrg,
            'NP': np_array,
            'FPT': fpt,
            'FPA': fpa,
            'error': None
        }

    except Exception as e:
        return {'error': f"Error calculating photon metrics: {str(e)}"}


def calculate_absorbed_photons(wavelengths, np_array, fpa_array):
    """
    Calculate total absorbed photons and total LED photons via integration.

    Returns:
        dict with keys: 'total_absorbed', 'total_led', 'efficiency', 'error'
    """
    try:
        wavelengths = np.asarray(wavelengths, dtype=float)
        np_array = np.asarray(np_array, dtype=float)
        fpa_array = np.asarray(fpa_array, dtype=float)

        ap = np_array * fpa_array

        # UPDATE, numpy doesn't have .trapz anymore
        total_absorbed = np.trapezoid(ap, wavelengths)
        total_led = np.trapezoid(np_array, wavelengths)

        if total_led == 0:
            return {'error': "Total LED photons is zero"}

        efficiency = (total_absorbed / total_led) * 100

        return {
            'total_absorbed': total_absorbed,
            'total_led': total_led,
            'efficiency': efficiency,
            'error': None
        }

    except Exception as e:
        return {'error': f"Error calculating absorbed photons: {str(e)}"}


def calculate_quantum_yields(rate_ftir, l2, monomer_conc, total_led_photons, total_absorbed_photons):
    """
    Calculate external and internal quantum yields.

    Returns:
        dict with keys: 'external_qy', 'internal_qy', 'rate_molecules', 'error'
    """
    try:
        if rate_ftir <= 0 or l2 <= 0 or monomer_conc <= 0:
            return {'error': "All inputs must be positive"}

        if total_led_photons == 0:
            return {'error': "Total LED photons cannot be zero"}

        avogadro = 6.022e23

        rate_molecules_converted = rate_ftir * l2 * monomer_conc * avogadro * (1 / 1000)

        external_qy = rate_molecules_converted / total_led_photons

        if total_absorbed_photons == 0:
            return {'error': "Total absorbed photons cannot be zero"}

        internal_qy = rate_molecules_converted / total_absorbed_photons

        return {
            'external_qy': external_qy,
            'internal_qy': internal_qy,
            'rate_molecules': rate_molecules_converted,
            'error': None
        }

    except Exception as e:
        return {'error': f"Error calculating quantum yields: {str(e)}"}
    




