"""
Stability-circle and available-gain-circle calculations for EECS 182 Final Project.

Computes input and output stability circles (center, radius) for each device,
determines the stable side, and provides a margin-adjusted radius (±0.05).
Also computes constant available gain (G_A) circles in the Γ_S plane using
g_A = G_A/|S21|^2.
"""

import cmath
import math
from constants import ALL_DEVICE_S_PARAMS, ALL_DEVICE_NOISE_PARAMS_1GHZ, NOISE_FIGURE_DB_MAX

STABILITY_MARGIN = 0.05
GAIN_LEVELS_DB = [18, 19, 20, 21, 22, 23, 24]
NOISE_CIRCLE_DB = NOISE_FIGURE_DB_MAX


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


def compute_edwards_sinsky_mu(S: dict) -> tuple[float, float]:
    """
    Edwards–Sinsky stability factors (mu1, mu2).

    Unconditional stability is guaranteed if mu1 > 1 and mu2 > 1.
    """
    delta = compute_delta(S)
    denom1 = abs(S["S22"] - delta * S["S11"].conjugate()) + abs(S["S12"] * S["S21"])
    denom2 = abs(S["S11"] - delta * S["S22"].conjugate()) + abs(S["S12"] * S["S21"])

    mu1 = (1 - abs(S["S11"]) ** 2) / denom1 if denom1 != 0 else float("inf")
    mu2 = (1 - abs(S["S22"]) ** 2) / denom2 if denom2 != 0 else float("inf")
    return mu1, mu2


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


def db_to_linear(db: float) -> float:
    """Convert power gain from dB to linear."""
    return 10 ** (db / 10.0)


def compute_noise_figure_linear(noise_params: dict, gamma_s: complex) -> float:
    """
    Compute noise factor F (linear) at a given Γ_S using the 4 noise parameters.

    F = Fmin + (4 * (Rn/Z0) * |ΓS - Γopt|^2) / ((1 - |ΓS|^2) * |1 + Γopt|^2)
    """
    fmin = db_to_linear(noise_params["NFMIN_DB"])
    gamma_opt = polar_to_complex(
        noise_params["GAMMA_OPT_MAG"], noise_params["GAMMA_OPT_ANG_DEG"]
    )
    rn_over_z0 = noise_params["RN_OVER_Z0"]

    denom = (1 - abs(gamma_s) ** 2) * (abs(1 + gamma_opt) ** 2)
    if denom <= 0:
        return float("inf")

    return fmin + (4 * rn_over_z0 * (abs(gamma_s - gamma_opt) ** 2)) / denom


def compute_noise_circle(noise_params: dict, nf_dB: float) -> tuple | None:
    """
    Compute center and radius of a constant noise figure circle in the Γ_S plane.

    Define:
      N = ((F - Fmin) * |1 + Γopt|^2) / (4 * (Rn/Z0))

    Then:
      c_N = Γopt / (1 + N)
      r_N = sqrt(N^2 + N(1 - |Γopt|^2)) / |1 + N|

    Returns (center, radius, gamma_opt) or None if invalid.
    """
    f = db_to_linear(nf_dB)
    fmin = db_to_linear(noise_params["NFMIN_DB"])
    gamma_opt = polar_to_complex(
        noise_params["GAMMA_OPT_MAG"], noise_params["GAMMA_OPT_ANG_DEG"]
    )
    rn_over_z0 = noise_params["RN_OVER_Z0"]

    if rn_over_z0 <= 0:
        return None

    n = ((f - fmin) * (abs(1 + gamma_opt) ** 2)) / (4 * rn_over_z0)
    if n < 0:
        return None

    denom = 1 + n
    radicand = n**2 + n * (1 - abs(gamma_opt) ** 2)
    if radicand < 0:
        return None

    center = gamma_opt / denom
    radius = math.sqrt(radicand) / abs(denom)
    return center, radius, gamma_opt


def compute_all_noise_circles(nf_dB: float = NOISE_CIRCLE_DB) -> dict:
    """
    Compute constant-NF noise circles for every device at the given nf_dB.

    Returns a nested dict keyed by device name, each containing:
      - nf_dB, center, radius, gamma_opt, valid
      - input: stability circle data (for overlay)
    """
    stability = compute_all_stability_circles()
    results: dict = {}
    for name, noise_params in ALL_DEVICE_NOISE_PARAMS_1GHZ.items():
        circle = compute_noise_circle(noise_params, nf_dB)
        if circle is None:
            results[name] = {
                "nf_dB": nf_dB,
                "center": None,
                "radius": None,
                "gamma_opt": None,
                "valid": False,
                "input": stability[name]["input"],
            }
            continue

        center, radius, gamma_opt = circle
        results[name] = {
            "nf_dB": nf_dB,
            "center": center,
            "radius": radius,
            "gamma_opt": gamma_opt,
            "valid": True,
            "input": stability[name]["input"],
        }
    return results


def verify_noise_circle(
    noise_params: dict,
    nf_dB: float,
    center: complex,
    radius: float,
    n_points: int = 36,
) -> float:
    """
    Sample points on a noise circle and compute NF at each. Return max |error| in dB.
    """
    max_err_db = 0.0
    for i in range(n_points):
        theta = 2 * math.pi * i / n_points
        gamma_s = center + radius * cmath.rect(1, theta)
        if abs(gamma_s) >= 1.0:
            continue
        f_linear = compute_noise_figure_linear(noise_params, gamma_s)
        if f_linear <= 0 or not math.isfinite(f_linear):
            continue
        nf_db_meas = 10 * math.log10(f_linear)
        max_err_db = max(max_err_db, abs(nf_db_meas - nf_dB))
    return max_err_db


def compute_available_gain_linear(S: dict, gamma_s: complex) -> float:
    """
    Compute available gain G_A (linear) at a given Γ_S.
    G_A = |S21|^2 * (1 - |ΓS|^2) / (|1 - S11 ΓS|^2 * (1 - |Γout|^2))
    where Γout = S22 + (S12 S21 ΓS) / (1 - S11 ΓS)
    """
    gamma_out = S["S22"] + (S["S12"] * S["S21"] * gamma_s) / (1 - S["S11"] * gamma_s)
    denom1 = 1 - S["S11"] * gamma_s
    denom2 = 1 - abs(gamma_out) ** 2
    if abs(denom1) < 1e-12 or denom2 <= 0:
        return float("inf")  # Singular or unstable
    ga = (abs(S["S21"]) ** 2) * (1 - abs(gamma_s) ** 2) / (abs(denom1) ** 2 * denom2)
    return ga


def compute_transducer_gain_linear(S: dict, gamma_s: complex, gamma_l: complex) -> float:
    """
    Compute transducer gain G_T (linear) for given (ΓS, ΓL).

    G_T = (1-|ΓS|^2) |S21|^2 (1-|ΓL|^2) /
          ( |(1-S11 ΓS)(1-S22 ΓL) - S12 S21 ΓS ΓL|^2 )
    """
    if abs(gamma_s) >= 1 or abs(gamma_l) >= 1:
        return 0.0

    denom = (1 - S["S11"] * gamma_s) * (1 - S["S22"] * gamma_l) - (S["S12"] * S["S21"] * gamma_s * gamma_l)
    denom_mag2 = abs(denom) ** 2
    if denom_mag2 == 0:
        return float("inf")

    num = (1 - abs(gamma_s) ** 2) * (abs(S["S21"]) ** 2) * (1 - abs(gamma_l) ** 2)
    return num / denom_mag2


def compute_gamma_out(S: dict, gamma_s: complex) -> complex:
    """Compute Γout looking into the device output for a given ΓS."""
    denom = 1 - S["S11"] * gamma_s
    if abs(denom) < 1e-12:
        return complex("nan")
    return S["S22"] + (S["S12"] * S["S21"] * gamma_s) / denom


def compute_gamma_in(S: dict, gamma_l: complex) -> complex:
    """Compute Γin looking into the device input for a given ΓL."""
    denom = 1 - S["S22"] * gamma_l
    if abs(denom) < 1e-12:
        return complex("nan")
    return S["S11"] + (S["S12"] * S["S21"] * gamma_l) / denom


def compute_gamma_a_mag(gamma_in: complex, gamma_s: complex) -> float:
    """
    External input mismatch screening magnitude |Γa|.

    |Γa| = | (Γin - ΓS*) / (1 - Γin ΓS) |
    """
    denom = 1 - gamma_in * gamma_s
    if abs(denom) < 1e-12:
        return float("inf")
    return abs((gamma_in - gamma_s.conjugate()) / denom)


def vswr_from_gamma_mag(gamma_mag: float) -> float:
    """Compute VSWR from |Γ| (returns inf if |Γ|>=1)."""
    if gamma_mag >= 1:
        return float("inf")
    return (1 + gamma_mag) / (1 - gamma_mag)


def stability_signed_margin(
    gamma: complex,
    center: complex,
    radius: float,
    stable_inside: bool,
) -> float:
    """
    Signed stability margin using distance to circle boundary.

    stable_inside=False (stable outside): m = |Γ - C| - r
    stable_inside=True  (stable inside):  m = r - |Γ - C|
    """
    d = abs(gamma - center)
    if stable_inside:
        return radius - d
    return d - radius


def compute_available_gain_circle(S: dict, ga_dB: float) -> tuple | None:
    """
    Compute center and radius of constant available gain circle in the Γ_S plane.

    Uses g_A = G_A/|S21|^2 with G_A in linear form. Formulas:
        C_1 = S11 - Δ S22*
        D_A = 1 + g_A(|S11|^2 - |Δ|^2)
        c_A = g_A C_1* / D_A
        r_A = sqrt(1 - 2k|S12 S21|g_A + (|S12 S21|g_A)^2) / |D_A|

    Returns (center, radius) or None if the radicand is negative (circle not realizable).
    """
    delta = compute_delta(S)
    k = compute_rollet_k(S)
    s12s21 = S["S12"] * S["S21"]
    s12s21_mag = abs(s12s21)

    ga_linear = db_to_linear(ga_dB)
    ga = ga_linear / (abs(S["S21"]) ** 2)

    c1 = S["S11"] - delta * S["S22"].conjugate()
    da = 1 + ga * (abs(S["S11"]) ** 2 - abs(delta) ** 2)

    radicand = 1 - 2 * k * s12s21_mag * ga + (s12s21_mag * ga) ** 2
    if radicand < 0:
        return None

    center = (ga * c1.conjugate()) / da
    radius = math.sqrt(radicand) / abs(da)
    return center, radius


def compute_all_gain_circles() -> dict:
    """
    Compute available gain circles for every device at GAIN_LEVELS_DB.

    Returns a nested dict keyed by device name, each containing:
        - gain_circles: list of {ga_dB, center, radius, valid}
        - input: stability circle data (for overlay)
    """
    stability = compute_all_stability_circles()
    results = {}
    for name, raw in ALL_DEVICE_S_PARAMS.items():
        S = get_complex_s_params(raw)
        circles = []
        for ga_dB in GAIN_LEVELS_DB:
            result = compute_available_gain_circle(S, ga_dB)
            if result is not None:
                center, radius = result
                circles.append({"ga_dB": ga_dB, "center": center, "radius": radius, "valid": True})
            else:
                circles.append({"ga_dB": ga_dB, "center": None, "radius": None, "valid": False})
        results[name] = {
            "gain_circles": circles,
            "input": stability[name]["input"],
        }
    return results


def verify_gain_circle(
    S: dict,
    ga_dB: float,
    center: complex,
    radius: float,
    n_points: int = 36,
) -> float:
    """
    Sample points on the gain circle and compute G_A at each. Return max |error| in dB.
    Confirms the plotted circle matches the constant-G_A contour.
    """
    target_linear = db_to_linear(ga_dB)
    max_err_db = 0.0
    for i in range(n_points):
        theta = 2 * math.pi * i / n_points
        gamma_s = center + radius * cmath.rect(1, theta)
        if abs(gamma_s) >= 1.0:
            continue  # Outside unit circle, skip
        ga_linear = compute_available_gain_linear(S, gamma_s)
        if ga_linear <= 0 or not math.isfinite(ga_linear):
            continue
        ga_db = 10 * math.log10(ga_linear)
        err_db = abs(ga_db - ga_dB)
        max_err_db = max(max_err_db, err_db)
    return max_err_db


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

    # Verify gain circles: sample points on each circle and check G_A matches
    gain_results = compute_all_gain_circles()
    print("\n=== Gain circle verification (max |error| in dB) ===")
    for name, raw in ALL_DEVICE_S_PARAMS.items():
        S = get_complex_s_params(raw)
        data = gain_results[name]
        for circ in data["gain_circles"]:
            if circ["valid"] and circ["center"] is not None and circ["radius"] is not None:
                err = verify_gain_circle(S, circ["ga_dB"], circ["center"], circ["radius"])
                print(f"  {name} G_A={circ['ga_dB']} dB: max error = {err:.4f} dB")

    # Verify noise circles at NF requirement
    noise_results = compute_all_noise_circles()
    print("\n=== Noise circle verification (max |error| in dB) ===")
    for name, noise_params in ALL_DEVICE_NOISE_PARAMS_1GHZ.items():
        d = noise_results[name]
        if d["valid"] and d["center"] is not None and d["radius"] is not None:
            err = verify_noise_circle(noise_params, d["nf_dB"], d["center"], d["radius"])
            print(f"  {name} NF={d['nf_dB']} dB: max error = {err:.4f} dB")
