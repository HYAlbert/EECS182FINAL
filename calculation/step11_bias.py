"""
Step 11: Bias network sizing helpers (1 GHz, microstrip + lumped parts).

Computes:
- Microstrip w/h, width W, eps_eff, lambda_g, and quarter-wave length for 20 Ω and 200 Ω lines
  using closed-form microstrip equations (no design curves).
- Gate divider (R1/R2) from +5 V to -5 V for Vg ≈ -0.47 V (IG ~ 0).
- Drain resistor R3 for VDS=3 V, ID=10 mA from +5 V.
- Choke/decap values meeting impedance targets at 1 GHz:
    |Zc| < 1 Ω, |Zl| > 10 kΩ.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class MicrostripResult:
    z0_ohm: float
    wh: float
    w_mm: float
    eeff: float
    lambda_g_mm: float
    quarter_wave_mm: float


def _eeff(er: float, wh: float) -> float:
    # Hammerstad/Jensen effective permittivity (simple form).
    if wh <= 0:
        return float("nan")
    return (er + 1) / 2 + (er - 1) / 2 * (1 / math.sqrt(1 + 12 / wh))


def _z0_microstrip(er: float, wh: float) -> float:
    """
    Quasi-TEM microstrip characteristic impedance using standard closed forms.
    (Commonly used Hammerstad-style approximation.)
    """
    eeff = _eeff(er, wh)
    if not math.isfinite(eeff) or eeff <= 0:
        return float("nan")

    if wh <= 1:
        return (60 / math.sqrt(eeff)) * math.log(8 / wh + 0.25 * wh)
    return (120 * math.pi) / (math.sqrt(eeff) * (wh + 1.393 + 0.667 * math.log(wh + 1.444)))


def solve_wh_for_z0(er: float, z0_target: float) -> float:
    """
    Solve for w/h given target Z0 using bisection on a wide bracket.
    """
    # w/h small -> very high Z0; w/h large -> low Z0
    lo, hi = 1e-4, 200.0
    f_lo = _z0_microstrip(er, lo) - z0_target
    f_hi = _z0_microstrip(er, hi) - z0_target
    if not (math.isfinite(f_lo) and math.isfinite(f_hi)) or f_lo * f_hi > 0:
        raise RuntimeError("Failed to bracket w/h for Z0 target.")

    for _ in range(200):
        mid = 0.5 * (lo + hi)
        f_mid = _z0_microstrip(er, mid) - z0_target
        if abs(f_mid) < 1e-9:
            return mid
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return 0.5 * (lo + hi)


def microstrip_from_z0(er: float, h_mm: float, f_hz: float, z0_target: float) -> MicrostripResult:
    wh = solve_wh_for_z0(er, z0_target)
    w_mm = wh * h_mm
    eeff = _eeff(er, wh)
    c_mm_s = 299_792_458_000.0  # mm/s
    lambda0_mm = c_mm_s / f_hz
    lambda_g_mm = lambda0_mm / math.sqrt(eeff)
    return MicrostripResult(
        z0_ohm=z0_target,
        wh=wh,
        w_mm=w_mm,
        eeff=eeff,
        lambda_g_mm=lambda_g_mm,
        quarter_wave_mm=lambda_g_mm / 4,
    )


def gate_divider_values(vp: float, vn: float, vg: float, r_total_ohm: float = 10_000.0) -> tuple[float, float, float, float, float]:
    """
    Divider between vp and vn:
      vp -- R1 -- node(vg) -- R2 -- vn
    """
    a = (vg - vn) / (vp - vn)  # R2/(R1+R2)
    r2 = a * r_total_ohm
    r1 = r_total_ohm - r2
    i = (vp - vn) / r_total_ohm
    p1 = i * i * r1
    p2 = i * i * r2
    return r1, r2, i, p1, p2


def main() -> None:
    er = 4.0
    h_mm = 0.254
    f = 1e9

    for z0 in (20.0, 200.0):
        r = microstrip_from_z0(er=er, h_mm=h_mm, f_hz=f, z0_target=z0)
        print(f"Microstrip Z0={z0:.0f} ohm:")
        print(f"  w/h = {r.wh:.4f}  ->  W = {r.w_mm:.4f} mm")
        print(f"  eps_eff = {r.eeff:.4f}")
        print(f"  lambda_g = {r.lambda_g_mm:.2f} mm  ->  quarter-wave = {r.quarter_wave_mm:.2f} mm\n")

    # Gate bias divider (+5 / -5) for Vg ≈ -0.47 V
    r1, r2, i, p1, p2 = gate_divider_values(vp=5.0, vn=-5.0, vg=-0.47, r_total_ohm=10_000.0)
    print("Gate divider (+5 V to -5 V):")
    print("  target Vg ~ -0.47 V -> choose R_total = 10 kOhm")
    print(f"  R1 (to +5) = {r1/1e3:.2f} kOhm, R2 (to -5) = {r2/1e3:.2f} kOhm")
    print(f"  I_div = {i*1e3:.3f} mA")
    print(f"  P_R1 = {p1*1e3:.3f} mW, P_R2 = {p2*1e3:.3f} mW\n")

    # Drain resistor from +5 to Vd=3 V at 10 mA
    id_a = 10e-3
    vds = 3.0
    r3 = (5.0 - vds) / id_a
    pr3 = id_a * id_a * r3
    print("Drain resistor R3 (+5 V -> drain):")
    print(f"  R3 = (5 - 3)/10 mA = {r3:.1f} ohm")
    print(f"  P_R3 = I^2 R = {pr3*1e3:.2f} mW\n")

    # Choke / decap at 1 GHz targets
    w = 2 * math.pi * f
    c_min = 1 / w  # |Zc| < 1Ω
    l_min = 10_000 / w  # |Zl| > 10kΩ
    print("Choke/decoupling targets at 1 GHz:")
    print(f"  For |Zc| < 1 ohm:  C > 1/(w) = {c_min*1e12:.1f} pF")
    print(f"  For |Zl| > 10 kohm: L > 10k/w = {l_min*1e6:.3f} uH")


if __name__ == '__main__':
    main()

