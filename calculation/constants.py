"""
S-parameter constants for the three devices.

S parameters at VDS = 3 V, ID = 10 mA.
"""

VDS = 3.0  # Volts
ID = 10e-3  # Amperes

NE7684A_S_PARAMS = {
    "S11_MAG": 0.65,
    "S11_PHASE_DEG": -135.1,
    "S21_MAG": 6.72,
    "S21_PHASE_DEG": 45.0,
    "S12_MAG": 0.051,
    "S12_PHASE_DEG": 34.1,
    "S22_MAG": 0.487,
    "S22_PHASE_DEG": -119.0,
}

NE7684B_S_PARAMS = {
    "S11_MAG": 0.580,
    "S11_PHASE_DEG": -135.0,
    "S21_MAG": 5.40,
    "S21_PHASE_DEG": 45.1,
    "S12_MAG": 0.051,
    "S12_PHASE_DEG": 34.7,
    "S22_MAG": 0.487,
    "S22_PHASE_DEG": -119.0,
}

NE7684C_S_PARAMS = {
    "S11_MAG": 0.780,
    "S11_PHASE_DEG": -15.0,
    "S21_MAG": 5.100,
    "S21_PHASE_DEG": 65.0,
    "S12_MAG": 0.051,
    "S12_PHASE_DEG": 34.0,
    "S22_MAG": 0.587,
    "S22_PHASE_DEG": 77.0,
}

ALL_DEVICE_S_PARAMS = {
    "NE7684A": NE7684A_S_PARAMS,
    "NE7684B": NE7684B_S_PARAMS,
    "NE7684C": NE7684C_S_PARAMS,
}