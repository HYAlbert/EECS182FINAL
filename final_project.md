# EECS 182

## Final Project Winter 2026

Goal: Select a suitable device among the 3 provided in the data sheet to design a single stage amplifier to meet the following requirements.

### Requirements

- Gain $G_A > 18\,\text{dB}$
- Noise figure (NF) $\leq 1.7\,\text{dB}$
- Frequency: $1\,\text{GHz}$
- $\text{VSWR}_\text{INPUT} < 3:1$ *(Note this spec is critical and must be met)*
- $\text{VSWR}_\text{OUTPUT} = 1:1$  *(Note this spec is critical and must be met)*
- Stability margin at input $\ge 0.05$
- Stability margin at output $\ge 0.05$

## Project Instructions

1. Analyze the requirements and describe your approach for the design of the amplifier.
2. For each device check stability, if the device is not unconditionally stable draw the stability circles at the input and output on two separate Smith's charts for the input and output plane.
3. For each device draw the available gain circles in the proper plane.
4. For each device draw the noise figure circles in the proper plane.
5. Select the device that satisfy or exceed the requirements specified above, explain your choice and explain why you select one device vs. the other two.
6. For the selected device tune $\Gamma_s$ to trade off between Gain, noise figure, stability margin and (VSWR)\_INPUT/OUTPUT. Note this last specification **must be met at all costs**.
7. Select the optimum value for the input $\Gamma_s$ accordingly to the amplifier specifications and stability requirements. Pay particular attention to the VSWR\_IN requirement and make sure you meet this specification.
8. Select the correspondent value of $\Gamma_L$ and verify the stability requirements for it in the proper plane.
9. Use two separate Smith's charts to design the input and output matching networks. Use balanced open stubs having characteristic impedance of $100\,\Omega$ in combination with transmission line (as in Fig.1) to design the matching circuit.
10. Realize your matching circuits in MIC technology using microstrip lines for the matching stub. use open stubs having impedance of $100\,\Omega$. (use the graphs in Fig.3 to design all the microstrip lines). Use Rogers as substrate ($\varepsilon_r = 4$, $h = 0.254\,\text{mm}$) and 201 form factor for the passive components (see Fig. 2) for the bias circuit and the decoupling network.
11. Design the bias network for the device including the decupling capacitors as follow:
    - Use High/Low impedance ($200\,\Omega / 20\,\Omega$) quarter wave line/stub configuration to provide the bias to the gate and drain of the device, the source should be connected to ground trough a via hole.
    - Assume differential voltage $V_{CC} = +5\,\text{V} / -5\,\text{V}$ supply is available for the bias of the device.
    - You can assume no current on the gate ($I_G \sim 0$) of the device when biasing the gate ($V_{GS}$), determine the value of the resistors $R1$ and $R2$.
    - Use the I-V curve in the data sheet and draw the proper load line to calculate the resistors $R3$ needed to bias the drain ($V_{DS}$).
    - In addition to their value also compute the power dissipated by each resistor used in the bias network.
    - Compute the values for the choke inductors $L_{CK}$ and decoupling capacitors $C_{DEC}$.
12. Provide a good draw to scale of the circuit layout (make sure it is "to scale") including matching network, bias network and decoupling capacitors.
13. Summarize your final amplifier circuit and performance trade off.
14. If your design cannot meet all the requirements explain why, discuss what you learn during this project and explain your tradeoffs.

![SMD\_dimensions](SMD_dimensions.jpg)
![design\_curves](design_curves.jpg)

Device Specs:

S parameters at $V_{DS} = 3\,\text{V}$, $I_D = 10\,\text{mA}$

NE7684A
- $S_{11}$ mag $0.65$
- $S_{11}$ phase $-135.1$
- $S_{21}$ mag $6.72$
- $S_{21}$ phase $45.0$
- $S_{12}$ mag $0.051$
- $S_{12}$ phase $34.1$
- $S_{22}$ mag $0.487$
- $S_{22}$ phase $-119$

NE7684B
- $S_{11}$ mag $0.580$
- $S_{11}$ phase $-135$
- $S_{21}$ mag $5.40$
- $S_{21}$ phase $45.1$
- $S_{12}$ mag $0.051$
- $S_{12}$ phase $34.7$
- $S_{22}$ mag $0.487$
- $S_{22}$ phase $-119$

NE7684C
- $S_{11}$ mag $0.780$
- $S_{11}$ phase $-15.0$
- $S_{21}$ mag $5.100$
- $S_{21}$ phase $65.0$
- $S_{12}$ mag $0.051$
- $S_{12}$ phase $34.0$
- $S_{22}$ mag $0.587$
- $S_{22}$ phase $77.0$

Step 1:
I will complete this later.

Step 2: Stability Analysis

### Stability Circle Equations

A two-port network is **unconditionally stable** when the Rollet stability factor $k > 1$ and $|\Delta| < 1$, where:

$$\Delta = S_{11} S_{22} - S_{12} S_{21}$$

$$k = \frac{1 - |S_{11}|^2 - |S_{22}|^2 + |\Delta|^2}{2|S_{12} S_{21}|}$$

When $k \leq 1$ the device is only **conditionally stable**, so I draw stability circles to identify the stable regions in the $\Gamma_S$ and $\Gamma_L$ planes. In this report, **source** refers to the **input** plane ($\Gamma_S$) and **load** refers to the **output** plane ($\Gamma_L$).

**Load stability circle** (in the $\Gamma_L$ plane):

$$C_L = \frac{\bigl(S_{22} - \Delta\, S_{11}^{*}\bigr)^{*}}{\bigl|S_{22}\bigr|^{2} - \bigl|\Delta\bigr|^{2}} \qquad r_L = \left|\frac{S_{12}\, S_{21}}{\bigl|S_{22}\bigr|^{2} - \bigl|\Delta\bigr|^{2}}\right|$$

**Source stability circle** (in the $\Gamma_S$ plane):

$$C_S = \frac{\bigl(S_{11} - \Delta\, S_{22}^{*}\bigr)^{*}}{\bigl|S_{11}\bigr|^{2} - \bigl|\Delta\bigr|^{2}} \qquad r_S = \left|\frac{S_{12}\, S_{21}}{\bigl|S_{11}\bigr|^{2} - \bigl|\Delta\bigr|^{2}}\right|$$

**Load stability circle** (in the $\Gamma_L$ plane):

$$
C_L = \frac{(S_{22} - \Delta S_{11}^*)^*}{|S_{22}|^2 - |\Delta|^2}
\qquad
r_L = \left|\frac{S_{12} S_{21}}{|S_{22}|^2 - |\Delta|^2}\right|
$$

**Source stability circle** (in the $\Gamma_S$ plane):

$$
C_S = \frac{(S_{11} - \Delta S_{22}^*)^*}{|S_{11}|^2 - |\Delta|^2}
\qquad
r_S = \left|\frac{S_{12} S_{21}}{|S_{11}|^2 - |\Delta|^2}\right|
$$

**Determining the stable side:**  
In the $\Gamma_L$ plane, I test the point $\Gamma_L = 0$, which gives $\Gamma_{in} = S_{11}$. So if $|S_{11}| < 1$, the origin is stable in the load plane.  

In the $\Gamma_S$ plane, I test the point $\Gamma_S = 0$, which gives $\Gamma_{out} = S_{22}$. So if $|S_{22}| < 1$, the origin is stable in the source plane.  

I then check whether the origin lies inside or outside the corresponding stability circle. If the origin is outside the circle, the stable region is outside; if the origin is inside, the stable region is inside.

**Stability margin:** I draw a second circle with the same center but radius adjusted by $\pm\,0.05$. If the stable region is **outside** the circle, the margin circle has radius $r + 0.05$ (expanding toward the stable side). If the stable region is **inside** the circle, the margin circle has radius $r - 0.05$ (shrinking toward the stable side). I kept the $\Gamma_S$ and $\Gamma_L$ within the margin circle boundary to satisfy the $\geq 0.05$ stability margin requirement.

### Computed Results

I compute the stability circles for all three devices in `calculation/calculations.py` and plot them via `calculation/graphs.py`. I save the resulting 3 graphs (one per device with source and load subplots) as JPG files under `documentation/`.

**Summary of stability for each device:**

| Device | k | Delta mag | Unconditionally stable? |
|--------|---|-----------|-------------------------|
| NE7684A | 0.5315 | 0.1549 | No (k &lt; 1) |
| NE7684B | 0.8033 | 0.1266 | No (k &lt; 1) |
| NE7684C | 0.2578 | 0.2951 | No (k &lt; 1) |

All three devices are **conditionally stable** ($k < 1$). In every case, the origin ($\Gamma = 0$) lies outside the stability circle, so the **stable region is outside** the circle. The margin circle (red dashed) has radius $r + 0.05$, and I must keep $\Gamma_S$ / $\Gamma_L$ outside that boundary.

![NE7684A Stability](documentation/NE7684A_stability.jpg)
![NE7684B Stability](documentation/NE7684B_stability.jpg)
![NE7684C Stability](documentation/NE7684C_stability.jpg)