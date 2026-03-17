"""
Step 6: Device-plane ΓS sweep for a selected device (1 GHz).

Sweeps ΓS on a coarse polar grid, sets ΓL = Γout*(ΓS), computes:
  - Available gain GA (dB)
  - Noise figure NF (dB)
  - Transistor-plane input VSWR from |Γin|
  - Input/output signed stability margins (vs margin circles)
  - Edwards–Sinsky stability factors (mu1, mu2)

Writes a CSV under documentation/ and prints a ranked list of feasible points.
"""

from __future__ import annotations

import csv
import math
import os
import sys
from dataclasses import dataclass
from typing import Iterable, Optional

from constants import (
    ALL_DEVICE_NOISE_PARAMS_1GHZ,
    ALL_DEVICE_S_PARAMS,
    NOISE_FIGURE_DB_MAX,
)
from calculations import (
    compute_all_stability_circles,
    compute_available_gain_linear,
    compute_available_gain_circle,
    compute_transducer_gain_linear,
    compute_delta,
    compute_edwards_sinsky_mu,
    compute_gamma_in,
    compute_gamma_out,
    compute_noise_figure_linear,
    db_to_linear,
    get_complex_s_params,
    stability_signed_margin,
    vswr_from_gamma_mag,
)

DEFAULT_DEVICE_NAME = "NE7684A"

# Sweep grid (coarse)
MAG_MIN = 0.00
MAG_MAX = 0.95
MAG_STEP = 0.05
ANG_MIN_DEG = -180
ANG_MAX_DEG = 180
ANG_STEP_DEG = 10

# Requirements / flags
GA_DB_MIN = 18.0
NF_DB_MAX = NOISE_FIGURE_DB_MAX
VSWR_IN_MAX = 3.0  # transistor-plane input VSWR metric (informational; not an external-port spec)
STAB_MARGIN_MIN = 0.05

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "documentation"))
def _csv_path(device_name: str) -> str:
    return os.path.join(OUTPUT_DIR, f"{device_name}_step6_sweep.csv")

def _arc_csv_path(device_name: str) -> str:
    return os.path.join(OUTPUT_DIR, f"{device_name}_step6_arc_sweep.csv")

def _refined_csv_path(device_name: str) -> str:
    return os.path.join(OUTPUT_DIR, f"{device_name}_step6_refined_sweep.csv")

def _joint_csv_path(device_name: str) -> str:
    return os.path.join(OUTPUT_DIR, f"{device_name}_step6_joint_sweep.csv")

def _joint_refined_csv_path(device_name: str) -> str:
    return os.path.join(OUTPUT_DIR, f"{device_name}_step6_joint_refined.csv")


@dataclass(frozen=True)
class SweepRow:
    gamma_s: complex
    gamma_l: complex
    gamma_in: complex
    gamma_out: complex
    ga_db: float
    nf_db: float
    vswr_in: float
    margin_in: float
    margin_out: float
    mu1: float
    mu2: float

    pass_ga: bool
    pass_nf: bool
    pass_vswr_in: bool
    pass_margin_in: bool
    pass_margin_out: bool

    @property
    def feasible(self) -> bool:
        return (
            self.pass_ga
            and self.pass_nf
            and self.pass_margin_in
            and self.pass_margin_out
        )


@dataclass(frozen=True)
class ArcRow(SweepRow):
    ga_target_db: float
    theta_deg: float


@dataclass(frozen=True)
class JointRow(SweepRow):
    gt_db: float

def _polar_grid() -> list[tuple[float, float]]:
    mags = []
    m = MAG_MIN
    while m <= MAG_MAX + 1e-12:
        mags.append(round(m, 10))
        m += MAG_STEP

    angs = list(range(ANG_MIN_DEG, ANG_MAX_DEG + 1, ANG_STEP_DEG))
    return [(mag, ang) for mag in mags for ang in angs]


def _angle_deg(z: complex) -> float:
    return math.degrees(math.atan2(z.imag, z.real))


def _in_window(device_name: str, gamma_s: complex) -> bool:
    re = gamma_s.real
    im = gamma_s.imag
    if device_name == "NE7684A":
        return (re < 0.5) and (0.2 <= im <= 0.8)
    if device_name == "NE7684C":
        return (0.25 < re < 0.5) and (0.15 <= im <= 0.5)
    return True


def _compute_row(
    device_name: str,
    S: dict,
    noise_params: dict,
    stability: dict,
    mu1: float,
    mu2: float,
    gamma_s: complex,
) -> SweepRow:
    inp = stability["input"]
    out = stability["output"]

    gamma_out = compute_gamma_out(S, gamma_s)
    gamma_l = gamma_out.conjugate()
    gamma_in = compute_gamma_in(S, gamma_l)

    ga_lin = compute_available_gain_linear(S, gamma_s)
    ga_db = 10 * math.log10(ga_lin) if ga_lin > 0 and math.isfinite(ga_lin) else float("inf")

    f_lin = compute_noise_figure_linear(noise_params, gamma_s)
    nf_db = 10 * math.log10(f_lin) if f_lin > 0 and math.isfinite(f_lin) else float("inf")

    vswr_in = vswr_from_gamma_mag(abs(gamma_in))

    margin_in = stability_signed_margin(
        gamma=gamma_s,
        center=inp["center"],
        radius=inp["radius"],
        stable_inside=inp["stable_inside"],
    )
    margin_out = stability_signed_margin(
        gamma=gamma_l,
        center=out["center"],
        radius=out["radius"],
        stable_inside=out["stable_inside"],
    )

    pass_ga = ga_db > GA_DB_MIN
    pass_nf = nf_db <= NF_DB_MAX
    pass_vswr_in = vswr_in < VSWR_IN_MAX
    pass_margin_in = margin_in >= STAB_MARGIN_MIN
    pass_margin_out = margin_out >= STAB_MARGIN_MIN

    return SweepRow(
        gamma_s=gamma_s,
        gamma_l=gamma_l,
        gamma_in=gamma_in,
        gamma_out=gamma_out,
        ga_db=ga_db,
        nf_db=nf_db,
        vswr_in=vswr_in,
        margin_in=margin_in,
        margin_out=margin_out,
        mu1=mu1,
        mu2=mu2,
        pass_ga=pass_ga,
        pass_nf=pass_nf,
        pass_vswr_in=pass_vswr_in,
        pass_margin_in=pass_margin_in,
        pass_margin_out=pass_margin_out,
    )


def _compute_joint_row(
    S: dict,
    noise_params: dict,
    stability: dict,
    mu1: float,
    mu2: float,
    gamma_s: complex,
    gamma_l: complex,
) -> JointRow:
    inp = stability["input"]
    out = stability["output"]

    gamma_out = compute_gamma_out(S, gamma_s)
    gamma_in = compute_gamma_in(S, gamma_l)

    gt_lin = compute_transducer_gain_linear(S, gamma_s, gamma_l)
    gt_db = 10 * math.log10(gt_lin) if gt_lin > 0 and math.isfinite(gt_lin) else float("inf")

    # Compute GA(ΓS) for meeting the project gain requirement during joint sweep.
    ga_lin = compute_available_gain_linear(S, gamma_s)
    ga_db = 10 * math.log10(ga_lin) if ga_lin > 0 and math.isfinite(ga_lin) else float("inf")

    f_lin = compute_noise_figure_linear(noise_params, gamma_s)
    nf_db = 10 * math.log10(f_lin) if f_lin > 0 and math.isfinite(f_lin) else float("inf")

    vswr_in = vswr_from_gamma_mag(abs(gamma_in))

    margin_in = stability_signed_margin(
        gamma=gamma_s,
        center=inp["center"],
        radius=inp["radius"],
        stable_inside=inp["stable_inside"],
    )
    margin_out = stability_signed_margin(
        gamma=gamma_l,
        center=out["center"],
        radius=out["radius"],
        stable_inside=out["stable_inside"],
    )

    pass_ga = ga_db > GA_DB_MIN
    pass_nf = nf_db <= NF_DB_MAX
    pass_vswr_in = vswr_in < VSWR_IN_MAX
    pass_margin_in = margin_in >= STAB_MARGIN_MIN
    pass_margin_out = margin_out >= STAB_MARGIN_MIN

    return JointRow(
        gamma_s=gamma_s,
        gamma_l=gamma_l,
        gamma_in=gamma_in,
        gamma_out=gamma_out,
        ga_db=ga_db,
        gt_db=gt_db,
        nf_db=nf_db,
        vswr_in=vswr_in,
        margin_in=margin_in,
        margin_out=margin_out,
        mu1=mu1,
        mu2=mu2,
        pass_ga=pass_ga,
        pass_nf=pass_nf,
        pass_vswr_in=pass_vswr_in,
        pass_margin_in=pass_margin_in,
        pass_margin_out=pass_margin_out,
    )


def sweep_joint(
    device_name: str,
    mag_step: float = 0.05,
    ang_step_deg: float = 10.0,
) -> list[JointRow]:
    raw_s = ALL_DEVICE_S_PARAMS[device_name]
    S = get_complex_s_params(raw_s)
    noise_params = ALL_DEVICE_NOISE_PARAMS_1GHZ[device_name]
    stability = compute_all_stability_circles()[device_name]
    mu1, mu2 = compute_edwards_sinsky_mu(S)

    # Build ΓS and ΓL candidate lists and prefilter by stability margin.
    mags = []
    m = 0.0
    while m <= 0.95 + 1e-12:
        mags.append(round(m, 10))
        m += mag_step
    angs = list(range(-180, 181, int(ang_step_deg)))

    gamma_s_list: list[complex] = []
    gamma_l_list: list[complex] = []
    inp = stability["input"]
    out = stability["output"]

    for mag in mags:
        for ang in angs:
            g = complex(mag * math.cos(math.radians(ang)), mag * math.sin(math.radians(ang)))
            if abs(g) >= 1.0:
                continue
            ms = stability_signed_margin(g, inp["center"], inp["radius"], inp["stable_inside"])
            if ms >= STAB_MARGIN_MIN:
                gamma_s_list.append(g)
            ml = stability_signed_margin(g, out["center"], out["radius"], out["stable_inside"])
            if ml >= STAB_MARGIN_MIN:
                gamma_l_list.append(g)

    rows: list[JointRow] = []
    for gs in gamma_s_list:
        for gl in gamma_l_list:
            rows.append(_compute_joint_row(S, noise_params, stability, mu1, mu2, gs, gl))
    return rows


def sweep_joint_target_gamma_in(
    device_name: str,
    gamma_in_target: complex,
    gamma_in_tol: float = 0.05,
    mag_step: float = 0.05,
    ang_step_deg: float = 10.0,
) -> list[JointRow]:
    """
    Joint ΓS–ΓL sweep, but only over ΓL values whose resulting Γin(ΓL)
    lies near a desired complex target point.

    Note: for a two-port terminated by ΓL, Γin depends on ΓL and S only
    (not on ΓS). This targeted sweep is useful when VSWR_IN is the primary
    gating constraint and we want to explore ΓS tradeoffs conditioned on
    a promising Γin region.
    """
    raw_s = ALL_DEVICE_S_PARAMS[device_name]
    S = get_complex_s_params(raw_s)
    noise_params = ALL_DEVICE_NOISE_PARAMS_1GHZ[device_name]
    stability = compute_all_stability_circles()[device_name]
    mu1, mu2 = compute_edwards_sinsky_mu(S)

    mags = []
    m = 0.0
    while m <= 0.95 + 1e-12:
        mags.append(round(m, 10))
        m += mag_step
    angs = list(range(-180, 181, int(ang_step_deg)))

    inp = stability["input"]
    out = stability["output"]

    gamma_s_set: set[complex] = set()
    gamma_l_set: set[complex] = set()

    for mag in mags:
        for ang in angs:
            g = complex(mag * math.cos(math.radians(ang)), mag * math.sin(math.radians(ang)))
            if abs(g) >= 1.0:
                continue

            ms = stability_signed_margin(g, inp["center"], inp["radius"], inp["stable_inside"])
            if ms >= STAB_MARGIN_MIN:
                gamma_s_set.add(g)

            ml = stability_signed_margin(g, out["center"], out["radius"], out["stable_inside"])
            if ml >= STAB_MARGIN_MIN:
                gin = compute_gamma_in(S, g)
                if abs(gin - gamma_in_target) <= gamma_in_tol:
                    gamma_l_set.add(g)

    gamma_s_list = sorted(gamma_s_set, key=lambda z: (abs(z), _angle_deg(z)))
    gamma_l_list = sorted(gamma_l_set, key=lambda z: (abs(z), _angle_deg(z)))

    rows: list[JointRow] = []
    for gs in gamma_s_list:
        for gl in gamma_l_list:
            rows.append(_compute_joint_row(S, noise_params, stability, mu1, mu2, gs, gl))
    return rows


def sweep_gain_circle_arcs(
    device_name: str,
    ga_levels_db: list[float],
    theta_step_deg: float = 1.0,
) -> list[ArcRow]:
    raw_s = ALL_DEVICE_S_PARAMS[device_name]
    S = get_complex_s_params(raw_s)
    noise_params = ALL_DEVICE_NOISE_PARAMS_1GHZ[device_name]
    stability = compute_all_stability_circles()[device_name]
    mu1, mu2 = compute_edwards_sinsky_mu(S)

    rows: list[ArcRow] = []
    for ga_target in ga_levels_db:
        circ = compute_available_gain_circle(S, ga_target)
        if circ is None:
            continue
        center, radius = circ
        theta = 0.0
        while theta < 360.0 + 1e-9:
            gamma_s = center + radius * complex(
                math.cos(math.radians(theta)), math.sin(math.radians(theta))
            )
            if abs(gamma_s) < 1.0 and _in_window(device_name, gamma_s):
                base = _compute_row(device_name, S, noise_params, stability, mu1, mu2, gamma_s)
                rows.append(
                    ArcRow(
                        **base.__dict__,
                        ga_target_db=ga_target,
                        theta_deg=theta,
                    )
                )
            theta += theta_step_deg
    return rows


def refine_around_point(
    device_name: str,
    center_point: complex,
    half_width: float = 0.05,
    step: float = 0.01,
) -> list[SweepRow]:
    raw_s = ALL_DEVICE_S_PARAMS[device_name]
    S = get_complex_s_params(raw_s)
    noise_params = ALL_DEVICE_NOISE_PARAMS_1GHZ[device_name]
    stability = compute_all_stability_circles()[device_name]
    mu1, mu2 = compute_edwards_sinsky_mu(S)

    rows: list[SweepRow] = []
    re0, im0 = center_point.real, center_point.imag
    re = re0 - half_width
    while re <= re0 + half_width + 1e-12:
        im = im0 - half_width
        while im <= im0 + half_width + 1e-12:
            gamma_s = complex(re, im)
            if abs(gamma_s) < 1.0 and _in_window(device_name, gamma_s):
                rows.append(_compute_row(device_name, S, noise_params, stability, mu1, mu2, gamma_s))
            im += step
        re += step
    return rows


def sweep_device(device_name: str = DEFAULT_DEVICE_NAME) -> list[SweepRow]:
    raw_s = ALL_DEVICE_S_PARAMS[device_name]
    S = get_complex_s_params(raw_s)
    noise_params = ALL_DEVICE_NOISE_PARAMS_1GHZ[device_name]
    stability = compute_all_stability_circles()[device_name]

    inp = stability["input"]
    out = stability["output"]
    mu1, mu2 = compute_edwards_sinsky_mu(S)

    rows: list[SweepRow] = []
    for mag, ang_deg in _polar_grid():
        gamma_s = complex(mag * math.cos(math.radians(ang_deg)), mag * math.sin(math.radians(ang_deg)))

        gamma_out = compute_gamma_out(S, gamma_s)
        gamma_l = gamma_out.conjugate()
        gamma_in = compute_gamma_in(S, gamma_l)

        ga_lin = compute_available_gain_linear(S, gamma_s)
        ga_db = 10 * math.log10(ga_lin) if ga_lin > 0 and math.isfinite(ga_lin) else float("inf")

        f_lin = compute_noise_figure_linear(noise_params, gamma_s)
        nf_db = 10 * math.log10(f_lin) if f_lin > 0 and math.isfinite(f_lin) else float("inf")

        # Transistor-plane input VSWR from |Γin|
        vswr_in = vswr_from_gamma_mag(abs(gamma_in))

        # Signed distance to the BASE stability circle boundary.
        # Requirement is margin >= 0.05 relative to the base circle.
        margin_in = stability_signed_margin(
            gamma=gamma_s,
            center=inp["center"],
            radius=inp["radius"],
            stable_inside=inp["stable_inside"],
        )
        margin_out = stability_signed_margin(
            gamma=gamma_l,
            center=out["center"],
            radius=out["radius"],
            stable_inside=out["stable_inside"],
        )

        pass_ga = ga_db > GA_DB_MIN
        pass_nf = nf_db <= NF_DB_MAX
        pass_vswr_in = vswr_in < VSWR_IN_MAX
        pass_margin_in = margin_in >= STAB_MARGIN_MIN
        pass_margin_out = margin_out >= STAB_MARGIN_MIN
        rows.append(
            SweepRow(
                gamma_s=gamma_s,
                gamma_l=gamma_l,
                gamma_in=gamma_in,
                gamma_out=gamma_out,
                ga_db=ga_db,
                nf_db=nf_db,
                vswr_in=vswr_in,
                margin_in=margin_in,
                margin_out=margin_out,
                mu1=mu1,
                mu2=mu2,
                pass_ga=pass_ga,
                pass_nf=pass_nf,
                pass_vswr_in=pass_vswr_in,
                pass_margin_in=pass_margin_in,
                pass_margin_out=pass_margin_out,
            )
        )

    return rows


def rank_feasible(rows: list[SweepRow]) -> list[SweepRow]:
    feasible = [r for r in rows if r.feasible]

    # Ranking priority (available-gain framework):
    # 1) higher available gain
    # 2) lower noise figure
    # 3) larger stability margins (min of in/out)
    def key(r: SweepRow) -> tuple[float, float, float]:
        min_margin = min(r.margin_in, r.margin_out)
        return (r.ga_db, -r.nf_db, min_margin)

    return sorted(feasible, key=key, reverse=True)


def rank_tradeoff_candidates(rows: list[SweepRow]) -> list[SweepRow]:
    """
    Rank candidates that meet GA/NF/stability margins but may fail VSWR_IN screening.
    This is useful when the VSWR screening metric is overly conservative under
    the ΓL=Γout* assumption.
    """
    candidates = [
        r
        for r in rows
        if (r.pass_ga and r.pass_nf and r.pass_margin_in and r.pass_margin_out)
    ]

    def key(r: SweepRow) -> tuple[float, float, float, float]:
        # Prefer: larger min stability margin, lower NF, higher GA, lower VSWR screen
        min_margin = min(r.margin_in, r.margin_out)
        return (min_margin, -r.nf_db, r.ga_db, -r.vswr_in)

    return sorted(candidates, key=key, reverse=True)


def write_csv(rows: list[SweepRow]) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # CSV path is set by caller
    raise RuntimeError("write_csv() must be called with a path. Use write_csv_path().")


def write_csv_path(rows: list[SweepRow], path: str) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "GammaS_mag",
                "GammaS_ang_deg",
                "GammaL_mag",
                "GammaL_ang_deg",
                "GA_dB",
                "NF_dB",
                "VSWR_IN_transistor_plane",
                "Margin_in",
                "Margin_out",
                "mu1",
                "mu2",
                "pass_GA",
                "pass_NF",
                "pass_VSWR_IN",
                "pass_margin_in",
                "pass_margin_out",
                "feasible",
            ]
        )
        for r in rows:
            w.writerow(
                [
                    abs(r.gamma_s),
                    _angle_deg(r.gamma_s),
                    abs(r.gamma_l),
                    _angle_deg(r.gamma_l),
                    r.ga_db,
                    r.nf_db,
                    r.vswr_in,
                    r.margin_in,
                    r.margin_out,
                    r.mu1,
                    r.mu2,
                    r.pass_ga,
                    r.pass_nf,
                    r.pass_vswr_in,
                    r.pass_margin_in,
                    r.pass_margin_out,
                    r.feasible,
                ]
            )


def write_arc_csv_path(rows: list[ArcRow], path: str) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "GA_target_dB",
                "theta_deg",
                "GammaS_mag",
                "GammaS_ang_deg",
                "GammaS_re",
                "GammaS_im",
                "GammaL_mag",
                "GammaL_ang_deg",
                "GA_dB",
                "NF_dB",
                "VSWR_IN_transistor_plane",
                "Margin_in",
                "Margin_out",
                "mu1",
                "mu2",
                "pass_GA",
                "pass_NF",
                "pass_VSWR_IN",
                "pass_margin_in",
                "pass_margin_out",
                "feasible",
            ]
        )
        for r in rows:
            w.writerow(
                [
                    r.ga_target_db,
                    r.theta_deg,
                    abs(r.gamma_s),
                    _angle_deg(r.gamma_s),
                    r.gamma_s.real,
                    r.gamma_s.imag,
                    abs(r.gamma_l),
                    _angle_deg(r.gamma_l),
                    r.ga_db,
                    r.nf_db,
                    r.vswr_in,
                    r.margin_in,
                    r.margin_out,
                    r.mu1,
                    r.mu2,
                    r.pass_ga,
                    r.pass_nf,
                    r.pass_vswr_in,
                    r.pass_margin_in,
                    r.pass_margin_out,
                    r.feasible,
                ]
            )


def _best_or_near_best(rows: list[SweepRow]) -> tuple[Optional[SweepRow], bool]:
    feasible = rank_feasible(rows)
    if feasible:
        return feasible[0], True
    # Near-best fallback: satisfy GA/NF/margins, then minimize VSWR_IN
    candidates = [r for r in rows if (r.pass_ga and r.pass_nf and r.pass_margin_in and r.pass_margin_out)]
    if not candidates:
        return None, False
    best = min(candidates, key=lambda r: r.vswr_in)
    return best, False


def rank_joint_feasible(rows: list[JointRow]) -> list[JointRow]:
    feasible = [r for r in rows if r.feasible]

    def key(r: JointRow) -> tuple[float, float, float]:
        # Stability is a hard constraint already; prioritize:
        # 1) higher gain, 2) lower NF, 3) lower VSWR_IN.
        return (r.ga_db, -r.nf_db, -r.vswr_in)

    return sorted(feasible, key=key, reverse=True)


def write_joint_csv_path(rows: list[JointRow], path: str) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "GammaS_mag",
                "GammaS_ang_deg",
                "GammaS_re",
                "GammaS_im",
                "GammaL_mag",
                "GammaL_ang_deg",
                "GammaL_re",
                "GammaL_im",
                "GT_dB",
                "GA_dB",
                "NF_dB",
                "VSWR_IN_transistor_plane",
                "Margin_in",
                "Margin_out",
                "mu1",
                "mu2",
                "pass_GA",
                "pass_NF",
                "pass_VSWR_IN",
                "pass_margin_in",
                "pass_margin_out",
                "feasible",
            ]
        )
        for r in rows:
            w.writerow(
                [
                    abs(r.gamma_s),
                    _angle_deg(r.gamma_s),
                    r.gamma_s.real,
                    r.gamma_s.imag,
                    abs(r.gamma_l),
                    _angle_deg(r.gamma_l),
                    r.gamma_l.real,
                    r.gamma_l.imag,
                    r.gt_db,
                    r.ga_db,
                    r.nf_db,
                    r.vswr_in,
                    r.margin_in,
                    r.margin_out,
                    r.mu1,
                    r.mu2,
                    r.pass_ga,
                    r.pass_nf,
                    r.pass_vswr_in,
                    r.pass_margin_in,
                    r.pass_margin_out,
                    r.feasible,
                ]
            )


def main() -> None:
    device_name = "NE7684A"
    print(f"=== {device_name} Step 6 sweep (available-gain framework) ===")

    rows = sweep_device(device_name)
    coarse_csv = _csv_path(device_name)
    write_csv_path(rows, coarse_csv)
    ranked = rank_feasible(rows)
    print(f"Wrote coarse CSV: {coarse_csv}")
    print(f"Total coarse rows: {len(rows)}")
    print(f"Feasible rows (GA/NF/margins): {len(ranked)}")

    if not ranked:
        print("No feasible points found on coarse grid.")
        return

    best = ranked[0]
    print(
        "Best coarse feasible:\n"
        f"  Gamma_S* = ({best.gamma_s.real:+.6f}{best.gamma_s.imag:+.6f}j)\n"
        f"  Gamma_L* = ({best.gamma_l.real:+.6f}{best.gamma_l.imag:+.6f}j)  (conj Gamma_out)\n"
        f"  G_A = {best.ga_db:.3f} dB,  NF = {best.nf_db:.3f} dB\n"
        f"  stability margins: m_in = {best.margin_in:.3f},  m_out = {best.margin_out:.3f}\n"
        f"  device-plane VSWR_IN (info) = {best.vswr_in:.3f}"
    )

    refined = refine_around_point(
        device_name=device_name,
        center_point=best.gamma_s,
        half_width=0.04,
        step=0.002,
    )
    refined_csv = _refined_csv_path(device_name)
    write_csv_path(refined, refined_csv)
    refined_ranked = rank_feasible(refined)
    print(f"Wrote refined CSV: {refined_csv}")
    if refined_ranked:
        rb = refined_ranked[0]
        print(
            "Best refined feasible:\n"
            f"  Gamma_S* = ({rb.gamma_s.real:+.6f}{rb.gamma_s.imag:+.6f}j)\n"
            f"  Gamma_L* = ({rb.gamma_l.real:+.6f}{rb.gamma_l.imag:+.6f}j)\n"
            f"  G_A = {rb.ga_db:.3f} dB,  NF = {rb.nf_db:.3f} dB\n"
            f"  stability margins: m_in = {rb.margin_in:.3f},  m_out = {rb.margin_out:.3f}\n"
            f"  device-plane VSWR_IN (info) = {rb.vswr_in:.3f}"
        )


if __name__ == "__main__":
    main()

