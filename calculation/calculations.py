"""
Stability-circle calculations for EECS 182 Final Project.

Computes input and output stability circles (center, radius) for each device,
determines the stable side, and provides a margin-adjusted radius (±0.05).
"""

import cmath
import math
from constants import ALL_DEVICE_S_PARAMS

STABILITY_MARGIN = 0.05


def polar_to_complex(mag: float, phase_deg: float) -> complex:
    return cmath.rect(mag, math.radians(phase_deg))


def get_complex_s_params(raw: dict) -> dict:
    """Convert a raw S-parameter dict (mag/phase) to complex-valued dict."""
    return {
        "S11": polar_to_complex(raw["S11_MAG"], raw["S11_PHASE_DEG"]),
        "S21": polar_to_complex(raw["S21_MAG"], raw["S21_PHASE_DEG"]),
        "S12": polar_to_complex(raw["S12_MAG"], raw["S12_PHASE_DEG"]),
        "S22": polar_to_complex(raw["S22_MAG"], raw["S22_PHASE_DEG"]),
    }


def compute_delta(S: dict) -> complex:
    return S["S11"] * S["S22"] - S["S12"] * S["S21"]


def compute_rollet_k(S: dict) -> float:
    delta = compute_delta(S)
    numerator = (
        1
        - abs(S["S11"]) ** 2
        - abs(S["S22"]) ** 2
        + abs(delta) ** 2
    )
    denominator = 2 * abs(S["S12"] * S["S21"])
    return numerator / denominator


def compute_output_stability_circle(S: dict) -> tuple:
    """Return (center, radius) of the output stability circle in the Gamma_L plane."""
    delta = compute_delta(S)
    denom = abs(S["S22"]) ** 2 - abs(delta) ** 2
    center = (S["S22"] - delta * S["S11"].conjugate()).conjugate() / denom
    radius = abs(S["S12"] * S["S21"]) / abs(denom)
    return center, radius


def compute_input_stability_circle(S: dict) -> tuple:
    """Return (center, radius) of the input stability circle in the Gamma_S plane."""
    delta = compute_delta(S)
    denom = abs(S["S11"]) ** 2 - abs(delta) ** 2
    center = (S["S11"] - delta * S["S22"].conjugate()).conjugate() / denom
    radius = abs(S["S12"] * S["S21"]) / abs(denom)
    return center, radius


def is_origin_inside_circle(center: complex, radius: float) -> bool:
    """Check whether Gamma = 0 (origin) lies inside the given circle."""
    return abs(center) < radius


def determine_stable_side(center: complex, radius: float, s_ii_mag: float) -> bool:
    """
    Determine whether the stable region is inside the stability circle.

    If |S_ii| < 1 the origin is a known-stable point.
    - If the origin is inside the circle  -> stable region is inside  -> return True
    - If the origin is outside the circle -> stable region is outside -> return False
    """
    origin_inside = is_origin_inside_circle(center, radius)
    if s_ii_mag < 1:
        return origin_inside
    return not origin_inside


def compute_margin_radius(radius: float, stable_inside: bool) -> float:
    """
    Adjust the radius by the stability margin.

    stable_inside=True  -> margin circle shrinks (r - 0.05) to stay inside stable zone
    stable_inside=False -> margin circle grows  (r + 0.05) to push boundary outward
    """
    if stable_inside:
        return radius - STABILITY_MARGIN
    return radius + STABILITY_MARGIN


def compute_all_stability_circles() -> dict:
    """
    Compute stability circles for every device.

    Returns a nested dict keyed by device name, each containing:
        - k, delta_mag (overall stability indicators)
        - input / output dicts with center, radius, margin_radius, stable_inside
    """
    results = {}
    for name, raw in ALL_DEVICE_S_PARAMS.items():
        S = get_complex_s_params(raw)
        k = compute_rollet_k(S)
        delta = compute_delta(S)

        c_in, r_in = compute_input_stability_circle(S)
        stable_in = determine_stable_side(c_in, r_in, abs(S["S22"]))  # Gamma_S plane
        mr_in = compute_margin_radius(r_in, stable_in)

        c_out, r_out = compute_output_stability_circle(S)
        stable_out = determine_stable_side(c_out, r_out, abs(S["S11"]))  # Gamma_L plane
        mr_out = compute_margin_radius(r_out, stable_out)

        results[name] = {
            "k": k,
            "delta_mag": abs(delta),
            "input": {
                "center": c_in,
                "radius": r_in,
                "margin_radius": mr_in,
                "stable_inside": stable_in,
            },
            "output": {
                "center": c_out,
                "radius": r_out,
                "margin_radius": mr_out,
                "stable_inside": stable_out,
            },
        }
    return results


if __name__ == "__main__":
    results = compute_all_stability_circles()
    for name, data in results.items():
        print(f"\n=== {name} ===")
        print(f"  k = {data['k']:.4f},  |Delta| = {data['delta_mag']:.4f}")
        for plane in ("input", "output"):
            d = data[plane]
            c = d["center"]
            print(
                f"  {plane.upper()} circle: center = ({c.real:.4f}, {c.imag:.4f}j), "
                f"radius = {d['radius']:.4f}, margin_radius = {d['margin_radius']:.4f}, "
                f"stable_inside = {d['stable_inside']}"
            )
