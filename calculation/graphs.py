"""
Stability-circle and available-gain-circle plotting utilities for EECS 182 Final Project.

Draws source and load stability circles on Gamma-plane plots with a
unit circle for reference.  Each plot includes the base stability circle
and a margin circle (same center, radius ± 0.05).
Also draws constant available gain (G_A) circles in the Γ_S plane.
Also draws constant noise figure circles in the Γ_S plane.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from calculations import compute_all_stability_circles, compute_all_gain_circles, compute_all_noise_circles

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


def plot_device_gain_figure(name: str, data: dict) -> None:
    """
    Create one figure per device: Γ_S plane with available gain circles and
    input stability overlay. Saves to documentation/{name}_gain.jpg.
    """
    fig, ax = plt.subplots(figsize=(8, 8))

    # Unit circle
    uc_x, uc_y = _circle_points(0 + 0j, 1.0)
    ax.plot(uc_x, uc_y, "k-", linewidth=1.5, label=r"|$\Gamma_S$| = 1 (unit circle)")

    # Input stability circle and margin (overlay)
    inp = data["input"]
    sc_x, sc_y = _circle_points(inp["center"], inp["radius"])
    ax.plot(sc_x, sc_y, "b-", linewidth=1.5, alpha=0.7, label="Input stability circle")
    mc_x, mc_y = _circle_points(inp["center"], inp["margin_radius"])
    ax.plot(mc_x, mc_y, "b--", linewidth=1.0, alpha=0.6, label="Stability margin")

    # Gain circles (18–24 dB)
    colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(data["gain_circles"])))
    for i, circ in enumerate(data["gain_circles"]):
        if circ["valid"] and circ["center"] is not None and circ["radius"] is not None:
            gc_x, gc_y = _circle_points(circ["center"], circ["radius"])
            ax.plot(
                gc_x, gc_y,
                "-",
                color=colors[i],
                linewidth=2.0,
                label=f"G_A = {circ['ga_dB']} dB",
            )
            ax.plot(circ["center"].real, circ["center"].imag, "+", color=colors[i], markersize=6)

    ax.set_xlabel(r"Re($\Gamma_S$)", fontsize=12)
    ax.set_ylabel(r"Im($\Gamma_S$)", fontsize=12)
    ax.set_title(f"{name} — Available Gain Circles ($\\Gamma_S$ plane)", fontsize=13)
    ax.set_aspect("equal")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower left", fontsize=8, ncol=2)
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)

    fig.suptitle(f"{name} Available Gain Circles", fontsize=14, y=1.02)
    plt.tight_layout()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, f"{name}_gain.jpg")
    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {filepath}")


def plot_device_gain_circles(results: dict) -> None:
    """Generate one gain-circle figure per device (3 total JPGs)."""
    for name, data in results.items():
        plot_device_gain_figure(name, data)


def plot_device_noise_figure(name: str, data: dict) -> None:
    """
    Create one figure per device: Γ_S plane with the 1.7 dB noise circle,
    Γopt marker, and direction toward lower noise (toward Γopt).
    Saves to documentation/{name}_noise.jpg.
    """
    fig, ax = plt.subplots(figsize=(8, 8))

    # Unit circle
    uc_x, uc_y = _circle_points(0 + 0j, 1.0)
    ax.plot(uc_x, uc_y, "k-", linewidth=1.5, label=r"|$\Gamma_S$| = 1 (unit circle)")

    # Input stability circle and margin (overlay)
    inp = data["input"]
    sc_x, sc_y = _circle_points(inp["center"], inp["radius"])
    ax.plot(sc_x, sc_y, "b-", linewidth=1.5, alpha=0.5, label="Input stability circle")
    mc_x, mc_y = _circle_points(inp["center"], inp["margin_radius"])
    ax.plot(mc_x, mc_y, "b--", linewidth=1.0, alpha=0.4, label="Stability margin")

    # Noise circle
    if data["valid"] and data["center"] is not None and data["radius"] is not None:
        nc_x, nc_y = _circle_points(data["center"], data["radius"])
        ax.plot(nc_x, nc_y, "m-", linewidth=2.0, label=f"NF = {data['nf_dB']} dB")

        # Γopt marker
        gopt = data["gamma_opt"]
        ax.plot(gopt.real, gopt.imag, "k*", markersize=12, label=r"$\Gamma_{opt}$ (min NF)")

        # Arrow toward lower noise: from a point on the circle toward Γopt
        start = data["center"] + data["radius"]  # theta = 0 point
        vec = gopt - start
        if abs(vec) > 1e-12:
            end = start + 0.25 * vec
            ax.annotate(
                "Lower NF",
                xy=(end.real, end.imag),
                xytext=(start.real, start.imag),
                arrowprops=dict(arrowstyle="->", linewidth=2.0),
                fontsize=11,
                horizontalalignment="left",
                verticalalignment="bottom",
            )

    ax.set_xlabel(r"Re($\Gamma_S$)", fontsize=12)
    ax.set_ylabel(r"Im($\Gamma_S$)", fontsize=12)
    ax.set_title(f"{name} — Noise Figure Circle ($\\Gamma_S$ plane)", fontsize=13)
    ax.set_aspect("equal")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower left", fontsize=8, ncol=2)
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)

    fig.suptitle(f"{name} Noise Figure Circle", fontsize=14, y=1.02)
    plt.tight_layout()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, f"{name}_noise.jpg")
    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {filepath}")


def plot_device_noise_circles(results: dict) -> None:
    """Generate one noise-circle figure per device (3 total JPGs)."""
    for name, data in results.items():
        plot_device_noise_figure(name, data)


def plot_device_combined_figure(
    name: str,
    stability_data: dict,
    gain_data: dict,
    noise_data: dict,
) -> None:
    """
    Create a combined figure per device with two subplots:
      - Left: Γ_S plane overlay (gain circles + noise circle + input stability + margin)
      - Right: Γ_L plane (output stability + margin)
    Saves to documentation/{name}_combined.jpg.
    """
    fig, (ax_src, ax_load) = plt.subplots(1, 2, figsize=(16, 7))

    # --- Left: ΓS overlay ---
    uc_x, uc_y = _circle_points(0 + 0j, 1.0)
    ax_src.plot(uc_x, uc_y, "k-", linewidth=1.5, label=r"|$\Gamma_S$| = 1 (unit circle)")

    inp = stability_data["input"]
    sc_x, sc_y = _circle_points(inp["center"], inp["radius"])
    ax_src.plot(sc_x, sc_y, "b-", linewidth=1.5, alpha=0.55, label="Input stability circle")
    mc_x, mc_y = _circle_points(inp["center"], inp["margin_radius"])
    ax_src.plot(mc_x, mc_y, "b--", linewidth=1.0, alpha=0.45, label="Input stability margin")

    # Gain circles 18–24 dB
    gain_circles = gain_data["gain_circles"]
    colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(gain_circles)))
    for i, circ in enumerate(gain_circles):
        if circ["valid"] and circ["center"] is not None and circ["radius"] is not None:
            gc_x, gc_y = _circle_points(circ["center"], circ["radius"])
            ax_src.plot(
                gc_x,
                gc_y,
                "-",
                color=colors[i],
                linewidth=2.0,
                label=f"G_A = {circ['ga_dB']} dB",
            )

    # Noise circle (NF = 1.7 dB) and Γopt marker
    if noise_data["valid"] and noise_data["center"] is not None and noise_data["radius"] is not None:
        nc_x, nc_y = _circle_points(noise_data["center"], noise_data["radius"])
        ax_src.plot(nc_x, nc_y, "m-", linewidth=2.5, label=f"NF = {noise_data['nf_dB']} dB")

        gopt = noise_data["gamma_opt"]
        ax_src.plot(gopt.real, gopt.imag, "k*", markersize=12, label=r"$\Gamma_{opt}$ (min NF)")

        # Arrow toward lower noise (toward Γopt)
        start = noise_data["center"] + noise_data["radius"]
        vec = gopt - start
        if abs(vec) > 1e-12:
            end = start + 0.25 * vec
            ax_src.annotate(
                "Lower NF",
                xy=(end.real, end.imag),
                xytext=(start.real, start.imag),
                arrowprops=dict(arrowstyle="->", linewidth=2.0),
                fontsize=11,
                horizontalalignment="left",
                verticalalignment="bottom",
            )

    ax_src.set_xlabel(r"Re($\Gamma_S$)", fontsize=12)
    ax_src.set_ylabel(r"Im($\Gamma_S$)", fontsize=12)
    ax_src.set_title(f"{name} — ΓS overlay (Gain + Noise + Input Stability)", fontsize=13)
    ax_src.set_aspect("equal")
    ax_src.grid(True, linestyle=":", alpha=0.6)
    ax_src.legend(loc="lower left", fontsize=8, ncol=2)
    ax_src.set_xlim(-1.5, 1.5)
    ax_src.set_ylim(-1.5, 1.5)

    # --- Right: ΓL stability ---
    out = stability_data["output"]
    _draw_stability(
        ax_load,
        center=out["center"],
        radius=out["radius"],
        margin_radius=out["margin_radius"],
        stable_inside=out["stable_inside"],
        title=f"{name} — Load Stability ($\\Gamma_L$ plane)",
    )

    fig.suptitle(f"{name} — Combined Design Constraints", fontsize=15, y=1.02)
    plt.tight_layout()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, f"{name}_combined.jpg")
    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {filepath}")


def plot_all_devices_combined_figures() -> None:
    """Generate one combined overlay figure per device (3 total JPGs)."""
    stability_results = compute_all_stability_circles()
    gain_results = compute_all_gain_circles()
    noise_results = compute_all_noise_circles()
    for name in stability_results.keys():
        plot_device_combined_figure(
            name=name,
            stability_data=stability_results[name],
            gain_data=gain_results[name],
            noise_data=noise_results[name],
        )


if __name__ == "__main__":
    results = compute_all_stability_circles()
    plot_device_stability_circles(results)
    print("\nAll 3 stability-circle plots generated.")

    gain_results = compute_all_gain_circles()
    plot_device_gain_circles(gain_results)
    print("All 3 gain-circle plots generated.")

    noise_results = compute_all_noise_circles()
    plot_device_noise_circles(noise_results)
    print("All 3 noise-circle plots generated.")

    plot_all_devices_combined_figures()
    print("All 3 combined overlay plots generated.")
