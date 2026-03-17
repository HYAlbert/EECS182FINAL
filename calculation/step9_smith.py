"""
Step 9: Smith chart plots for input/output matching networks.

This script generates two Smith charts (Γ-plane with impedance grid) and overlays
the matching trajectories needed to realize the selected ΓS* and ΓL* terminations
for NE7684A at 1 GHz, using the project-constrained topology:

  - 50 Ω through line sections (series transmission line rotation)
  - a single shunt node containing two identical 100 Ω open stubs in parallel

Two identical 100 Ω open stubs in parallel provide an equivalent normalized shunt
susceptance (normalized to 50 Ω) of:
  y_eq = j * tan(θ_stub)
since Y_eq = 2 * j(1/100)tan(θ) = j(1/50)tan(θ).

No external RF libraries are required (numpy + matplotlib only).
"""

from __future__ import annotations

import os
import math
from dataclasses import dataclass

import numpy as np
import matplotlib.pyplot as plt


OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "documentation"))
Z0 = 50.0
F_HZ = 1e9
W = 2 * math.pi * F_HZ


@dataclass(frozen=True)
class StubMatchSolution:
    theta1: float  # series 50 Ω line electrical length before shunt node [rad]
    theta_stub: float  # open-stub electrical length (both stubs identical) [rad]
    theta2: float  # series 50 Ω line electrical length after shunt node [rad]
    gamma_final: complex  # achieved Γ at the device plane
    err: float  # |Γ_achieved - Γ_target|


def gamma_from_z(z: complex) -> complex:
    return (z - 1) / (z + 1)


def z_from_gamma(gamma: complex) -> complex:
    return (1 + gamma) / (1 - gamma)


def smith_grid(ax, r_vals=None, x_vals=None) -> None:
    """
    Draw a basic Smith chart grid by mapping constant-r and constant-x lines
    from the z-plane into the Γ-plane.
    """
    if r_vals is None:
        r_vals = [0, 0.2, 0.5, 1, 2, 5]
    if x_vals is None:
        x_vals = [-5, -2, -1, -0.5, 0.5, 1, 2, 5]

    # Unit circle
    th = np.linspace(0, 2 * np.pi, 721)
    ax.plot(np.cos(th), np.sin(th), "k-", lw=1.5)

    # Constant resistance circles: r = const, sweep x
    x_sweep = np.linspace(-20, 20, 4001)
    for r in r_vals:
        z = r + 1j * x_sweep
        g = gamma_from_z(z)
        ax.plot(g.real, g.imag, color="0.85", lw=1.0)

    # Constant reactance arcs: x = const, sweep r
    r_sweep = np.linspace(0, 20, 3001)
    for x in x_vals:
        z = r_sweep + 1j * x
        g = gamma_from_z(z)
        ax.plot(g.real, g.imag, color="0.85", lw=1.0)

    ax.set_aspect("equal")
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_xlabel(r"Re($\Gamma$)")
    ax.set_ylabel(r"Im($\Gamma$)")
    ax.grid(False)


def z_in_of_open_stub(theta: float, z0_stub: float = 100.0, z0_ref: float = 50.0) -> complex:
    """
    Return the *normalized-to-z0_ref* impedance of an open-circuited stub of length theta.

    For an open stub: Y_in = j*(1/Z0_stub)*tan(theta).
    Convert to normalized admittance y = Y_in * z0_ref.
    """
    y = 1j * (z0_ref / z0_stub) * math.tan(theta)
    if abs(y) < 1e-14:
        # Very small susceptance -> very large impedance
        return complex(1e14, 0.0)
    return 1 / y


def apply_series_line(gamma: complex, theta: float) -> complex:
    """Lossless line rotation (normalized to the line's Z0): Γ -> Γ·e^{-j2θ}."""
    return gamma * complex(math.cos(-2 * theta), math.sin(-2 * theta))


def apply_shunt_susceptance(z: complex, b: float) -> complex:
    """
    Apply normalized shunt susceptance +j*b in admittance plane (normalized to 50 Ω).
    z -> y=1/z -> y+j*b -> z'.
    """
    y = 1 / z
    y2 = y + 1j * b
    return 1 / y2


def cascade_series_then_shunt_then_series(
    gamma_start: complex, theta1: float, theta_stub: float, theta2: float
) -> complex:
    """
    Start at Γ on a 50 Ω line, apply:
      series line θ1 -> shunt balanced stub pair -> series line θ2
    and return final Γ at the end of θ2.

    Balanced pair (2× 100 Ω open stubs in parallel) gives normalized susceptance:
      b_eq = tan(theta_stub)   (normalized to 50 Ω)
    """
    # Rotate to shunt node
    g1 = apply_series_line(gamma_start, theta1)
    z1 = z_from_gamma(g1)

    # Shunt node: add susceptance b_eq
    b_eq = math.tan(theta_stub)
    z2 = apply_shunt_susceptance(z1, b_eq)
    g2 = gamma_from_z(z2)

    # Rotate from shunt node to device plane
    g3 = apply_series_line(g2, theta2)
    return g3


def trajectory_series_then_shunt_then_series(
    theta1: float, theta_stub: float, theta2: float, n_line: int = 220, n_stub: int = 160
) -> tuple[np.ndarray, np.ndarray]:
    """
    Build Γ trajectory points for plotting:
      start (Γ=0) -> series line sweep to θ1 -> shunt stub sweep to θ_stub -> series line sweep to θ2
    """
    gamma0 = 0 + 0j

    # Series line sweep to shunt node
    th1 = np.linspace(0.0, theta1, n_line)
    g_line1 = gamma0 * np.exp(-1j * 2 * th1)

    # Shunt sweep at node (work in z/y)
    g1_end = apply_series_line(gamma0, theta1)
    z1_end = z_from_gamma(g1_end)
    ths = np.linspace(0.0, theta_stub, n_stub)
    b_eq = np.tan(ths)
    # z(th) = 1 / (1/z1 + j*b_eq(th))
    z_shunt = 1 / ((1 / z1_end) + 1j * b_eq)
    g_shunt = gamma_from_z(z_shunt)

    # Series line sweep from node to device plane
    th2 = np.linspace(0.0, theta2, n_line)
    g2_end = g_shunt[-1]
    g_line2 = g2_end * np.exp(-1j * 2 * th2)

    g = np.concatenate([g_line1, g_shunt[1:], g_line2[1:]])
    return g.real, g.imag


def solve_for_target_gamma(
    gamma_target: complex,
    theta_grid: int = 361,
    theta_stub_grid: int = 721,
    max_err: float = 5e-3,
) -> StubMatchSolution:
    """
    Find a (theta1, theta_stub, theta2) solution for the topology:
      50Ω line θ1 -> shunt balanced stub pair -> 50Ω line θ2
    such that Γ_final ≈ Γ_target.

    Strategy:
      - brute-force theta1 and theta_stub grids
      - compute Γ at shunt node after stub
      - choose theta2 to rotate (phase) to best match Γ_target with same |Γ|
      - return the best overall solution (smallest complex error)
    """
    gamma0 = 0 + 0j

    best: StubMatchSolution | None = None

    # If starting at Γ=0, the first series line does nothing to Γ. Still keep θ1 for physical placement;
    # in this single-node stub topology, θ1 matters only if there are additional elements before the stub.
    # We keep θ1 in the model to match the writeup and to allow future extension.
    theta1_vals = np.linspace(0.0, math.pi, theta_grid, endpoint=False)
    theta_stub_vals = np.linspace(1e-6, math.pi / 2 - 1e-6, theta_stub_grid)  # short-ish open stubs

    for theta1 in theta1_vals:
        # at Γ=0, g1 is still 0 regardless of theta1
        g1 = apply_series_line(gamma0, theta1)
        z1 = z_from_gamma(g1)  # = 1

        # Shunt node after adding b_eq = tan(theta_stub)
        # z2(theta_stub) = 1 / (1/z1 + j*b_eq)
        b_eq = np.tan(theta_stub_vals)
        z2 = 1 / ((1 / z1) + 1j * b_eq)
        g2 = gamma_from_z(z2)

        # Choose theta2 to best match gamma_target via rotation: g3 = g2 * e^{-j2θ2}
        # For each g2, the optimal θ2 aligns phases: θ2 = -0.5 * angle(gamma_target/g2)
        # (mod π). Then error depends on |g2| vs |gamma_target| and numerical phase rounding.
        ratio = gamma_target / g2
        theta2_opt = (-0.5 * np.angle(ratio)) % math.pi
        g3 = g2 * np.exp(-1j * 2 * theta2_opt)
        err = np.abs(g3 - gamma_target)

        k = int(np.argmin(err))
        cand = StubMatchSolution(
            theta1=float(theta1),
            theta_stub=float(theta_stub_vals[k]),
            theta2=float(theta2_opt[k]),
            gamma_final=complex(g3[k]),
            err=float(err[k]),
        )
        if best is None or cand.err < best.err:
            best = cand
            if best.err <= max_err:
                return best

    assert best is not None
    return best


def plot_input_smith(gamma_s_star: complex, sol: StubMatchSolution, outpath: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 8))
    smith_grid(ax)

    # Key points
    g50 = 0 + 0j  # 50Ω normalized
    ax.plot([g50.real], [g50.imag], "ko", ms=6, label=r"$50\,\Omega$ (port)")
    ax.plot([gamma_s_star.real], [gamma_s_star.imag], "r*", ms=12, label=r"$\Gamma_S^\star$")

    x, y = trajectory_series_then_shunt_then_series(sol.theta1, sol.theta_stub, sol.theta2)
    ax.plot(x, y, "b-", lw=2.0, label="50Ω line → balanced shunt stubs → 50Ω line")

    ax.set_title(r"Input matching on Smith chart ($\Gamma_S$ plane)")
    ax.legend(loc="lower left", fontsize=9)
    fig.tight_layout()

    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    fig.savefig(outpath, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_output_smith(gamma_l_star: complex, sol: StubMatchSolution, outpath: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 8))
    smith_grid(ax)

    g50 = 0 + 0j
    ax.plot([g50.real], [g50.imag], "ko", ms=6, label=r"$50\,\Omega$ (port)")
    ax.plot([gamma_l_star.real], [gamma_l_star.imag], "r*", ms=12, label=r"$\Gamma_L^\star$")

    x, y = trajectory_series_then_shunt_then_series(sol.theta1, sol.theta_stub, sol.theta2)
    ax.plot(x, y, "b-", lw=2.0, label="50Ω line → balanced shunt stubs → 50Ω line")

    ax.set_title(r"Output matching on Smith chart ($\Gamma_L$ plane)")
    ax.legend(loc="lower left", fontsize=9)
    fig.tight_layout()

    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    fig.savefig(outpath, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    # Selected terminations (from Step 6 refined optimum)
    gamma_s_star = complex(-0.2600, 0.4530)
    gamma_l_star = complex(0.9856, -0.1650)

    # Solve for distributed balanced-stub solutions (θ1, θstub, θ2)
    in_sol = solve_for_target_gamma(gamma_s_star, max_err=5e-3)
    out_sol = solve_for_target_gamma(gamma_l_star, max_err=5e-3)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plot_input_smith(
        gamma_s_star=gamma_s_star,
        sol=in_sol,
        outpath=os.path.join(OUTPUT_DIR, "NE7684A_step9_input_smith.jpg"),
    )
    plot_output_smith(
        gamma_l_star=gamma_l_star,
        sol=out_sol,
        outpath=os.path.join(OUTPUT_DIR, "NE7684A_step9_output_smith.jpg"),
    )

    def deg(x: float) -> float:
        return x * 180.0 / math.pi

    def fmt_sol(name: str, sol: StubMatchSolution, gamma_target: complex) -> None:
        b_eq = math.tan(sol.theta_stub)
        # Each 100 Ω stub contributes half the equivalent susceptance when normalized to 50 Ω:
        # y_total = j*b_eq, so Y_total = j*b_eq/Z0; each stub Y = 0.5*Y_total
        B_each = 0.5 * (b_eq / Z0)  # Siemens
        print(f"{name}:")
        print(f"  target Gamma = {gamma_target.real:+.4f}{gamma_target.imag:+.4f}j")
        print(f"  achieved Gamma = {sol.gamma_final.real:+.4f}{sol.gamma_final.imag:+.4f}j  (err={sol.err:.4e})")
        print(f"  theta1 (50 ohm series line before stubs)  = {deg(sol.theta1):.2f} deg")
        print(f"  theta_stub (each 100 ohm open stub)       = {deg(sol.theta_stub):.2f} deg")
        print(f"  theta2 (50 ohm series line after stubs)   = {deg(sol.theta2):.2f} deg")
        print(f"  balanced-stub susceptance: y_eq = j*tan(theta_stub) = j*{b_eq:+.4f}")
        print(f"  each stub susceptance: B_each ~ {B_each:+.6f} S (at 1 GHz)")

    print("Balanced-stub distributed solutions (50 ohm line + 2x100 ohm open stubs in parallel):\n")
    fmt_sol("INPUT match (Gamma_S plane)", in_sol, gamma_s_star)
    print()
    fmt_sol("OUTPUT match (Gamma_L plane)", out_sol, gamma_l_star)


if __name__ == "__main__":
    main()

