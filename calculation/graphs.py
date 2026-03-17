"""
Stability-circle plotting utilities for EECS 182 Final Project.

Draws source and load stability circles on Gamma-plane plots with a
unit circle for reference.  Each plot includes the base stability circle
and a margin circle (same center, radius ± 0.05).
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from calculations import compute_all_stability_circles

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "documentation"))


def _circle_points(center: complex, radius: float, n: int = 361) -> tuple:
    """Return (x, y) arrays tracing a circle in the complex plane."""
    theta = np.linspace(0, 2 * np.pi, n)
    x = center.real + radius * np.cos(theta)
    y = center.imag + radius * np.sin(theta)
    return x, y


def _draw_stability(
    ax,
    center: complex,
    radius: float,
    margin_radius: float,
    stable_inside: bool,
    title: str,
) -> None:
    """
    Draw a stability circle with its margin circle on the given axis.
    """
    uc_x, uc_y = _circle_points(0 + 0j, 1.0)
    ax.plot(uc_x, uc_y, "k-", linewidth=1.5, label=r"|$\Gamma$| = 1 (unit circle)")

    sc_x, sc_y = _circle_points(center, radius)
    ax.plot(sc_x, sc_y, "b-", linewidth=2.0, label=f"Stability circle (r = {radius:.4f})")

    mc_x, mc_y = _circle_points(center, margin_radius)
    ax.plot(
        mc_x, mc_y, "r--", linewidth=2.0,
        label=f"Margin circle (r = {margin_radius:.4f})",
    )

    ax.plot(center.real, center.imag, "b+", markersize=10, markeredgewidth=2)

    stable_label = "inside" if stable_inside else "outside"
    ax.annotate(
        f"Stable region: {stable_label}",
        xy=(0.03, 0.97),
        xycoords="axes fraction",
        fontsize=10,
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.8),
    )

    ax.set_xlabel(r"Re($\Gamma$)", fontsize=12)
    ax.set_ylabel(r"Im($\Gamma$)", fontsize=12)
    ax.set_title(title, fontsize=13)
    ax.set_aspect("equal")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower right", fontsize=9)


def plot_device_stability_figure(name: str, data: dict) -> None:
    """
    Create one figure per device with two subplots: source (Γ_S) and load (Γ_L).
    Saves to documentation/{name}_stability.jpg.
    """
    fig, (ax_src, ax_load) = plt.subplots(1, 2, figsize=(14, 7))

    inp = data["input"]
    _draw_stability(
        ax_src,
        center=inp["center"],
        radius=inp["radius"],
        margin_radius=inp["margin_radius"],
        stable_inside=inp["stable_inside"],
        title=f"{name} — Source Stability Circle ($\\Gamma_S$ plane)",
    )

    out = data["output"]
    _draw_stability(
        ax_load,
        center=out["center"],
        radius=out["radius"],
        margin_radius=out["margin_radius"],
        stable_inside=out["stable_inside"],
        title=f"{name} — Load Stability Circle ($\\Gamma_L$ plane)",
    )

    fig.suptitle(f"{name} Stability Circles", fontsize=14, y=1.02)
    plt.tight_layout()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, f"{name}_stability.jpg")
    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {filepath}")


def plot_device_stability_circles(results: dict) -> None:
    """Generate one combined stability figure per device (3 total JPGs)."""
    for name, data in results.items():
        plot_device_stability_figure(name, data)


if __name__ == "__main__":
    results = compute_all_stability_circles()
    plot_device_stability_circles(results)
    print("\nAll 3 stability-circle plots generated.")
