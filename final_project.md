# EECS 182

## Final Project Winter 2026

Goal: Select a suitable device among the 3 provided in the data sheet to design a single stage amplifier to meet the following requirements.

### Requirements

- Gain $G_A > 18\,\text{dB}$
- Noise figure (NF) $\leq 1.7\,\text{dB}$
- Frequency: $1\,\text{GHz}$
- $\text{VSWR}_\text{INPUT} < 3:1$ *(Note this spec is critical and must be met)*
- $\text{VSWR}_\text{OUTPUT} = 1:1$  *(Note this spec is critical and must be met)*
- (Stability margin)\_INPUT $\geq 0.05$
- (Stability margin)\_OUTPUT $\geq 0.05$

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
to be completed later

Step 2: