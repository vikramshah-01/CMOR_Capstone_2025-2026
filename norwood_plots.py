# Get Dependencies
import pandas as pd
import numpy as np
import math as math
import seaborn as sns
import matplotlib.pyplot as plt
import os

import scipy as sp
from Norwood_Circulation_Solver_Functions import flow_pressure_solver_1, flow_pressure_solver_2, saturation_solver
from arterial_and_venous_compliance_solver import arterial_and_venous_compliance_solver
from systolic_and_diastolic_compliance_solver import systolic_and_diastolic_compliance_solver

# Global variables
# Change as needed
baseline_values_1 = {"C_sys":1.4,
                   "C_dia":6,
                   "C_A":1.4,
                   "C_V":6,
                   "HR":140,
                   "R_s":7.74,
                   "R_p":0.34,
                   "V_total":420}

baseline_values_2 = {
                   "Hb":15,
                   "CVO2":150}

factors = np.arange(0.5, 1.55, 0.05)

def yaxis_class1(desired_output):
    baseline_values_1 = {"C_sys":1.4,
                   "C_dia":6,
                   "C_A":1.4,
                   "C_V":6,
                   "HR":140,
                   "R_s":7.74,
                   "R_p":0.34,
                   "V_total":420}

    baseline_values_2 = {
                   "Hb":15,
                   "CVO2":150}

    factors = np.arange(0.5, 1.55, 0.05)

    # Create return dictionary
    yaxis = {key : [] for key in baseline_values_1.keys()}

    # Iterate over each input value
    for input in baseline_values_1.keys():
        baseline = baseline_values_1[input]

        # Copy so we can access other values easily
        other_values = baseline_values_1.copy()

        # Iterate over each factor that we plot for
        for factor in factors:
            multiplied = baseline * factor
            other_values[input] = multiplied

            # Solve for output
            Q_s, Q_p, P_a, P_v = flow_pressure_solver_1(**other_values)

            # Pick output
            if desired_output == "Q_s":
                val = Q_s
            elif desired_output == "Q_p":
                val = Q_p
            elif desired_output == "Q_total":
                val = Q_p + Q_s
            elif desired_output == "P_a":
                val = P_a
            else:
                val = P_v

            # Add to return dict
            yaxis[input].append(val)

    return yaxis

def yaxis_class2(desired_output):
    baseline_values_1 = {"C_sys":1.4,
                   "C_dia":6,
                   "C_A":1.4,
                   "C_V":6,
                   "HR":140,
                   "R_s":7.74,
                   "R_p":0.34,
                   "V_total":420}

    baseline_values_2 = {
                   "Hb":15,
                   "CVO2":150}

    factors = np.arange(0.5, 1.55, 0.05)

    # All keys
    first_phase_keys = set(baseline_values_1.keys())
    second_phase_keys = set(baseline_values_2.keys())
    all_keys = first_phase_keys.union(second_phase_keys)

    # Create return dictionary
    yaxis = {key : [] for key in all_keys}

    # Default Q_s, Q_p
    Q_s0, Q_p0, P_a0, P_v0 = flow_pressure_solver_1(**baseline_values_1)

    # Iterate over each input value
    for input in all_keys:
        if input in baseline_values_1.keys():
            baseline = baseline_values_1[input]

            # Process step for input dictionary
            phase_1_input = baseline_values_1.copy()
            phase_2_input = baseline_values_2.copy()

            # Iterate over each factor that we plot for
            for factor in factors:
                multiplied = baseline * factor
                phase_1_input[input] = multiplied

                # Solve for output
                Q_s, Q_p, P_a, P_v = flow_pressure_solver_1(**phase_1_input)

                phase_2_input["Q_s"] = Q_s
                phase_2_input["Q_p"] = Q_p

                S_m, S_sv, OD2 = saturation_solver(**phase_2_input)

                # Pick output
                if desired_output == "S_m":
                    val = S_m
                elif desired_output == "S_sv":
                    val = S_sv
                else:
                    val = OD2

                yaxis[input].append(val)

        else:
            baseline = baseline_values_2[input]

            # Process step
            input_vals = baseline_values_2.copy()
            input_vals["Q_s"] = Q_s0
            input_vals["Q_p"] = Q_p0

            for factor in factors:
                multiplied = baseline * factor
                input_vals[input] = multiplied

                # Solve for output
                S_m, S_sv, OD2 = saturation_solver(**input_vals)

                # Pick output
                if desired_output == "S_m":
                    val = S_m
                elif desired_output == "S_sv":
                    val = S_sv
                else:
                    val = OD2

                yaxis[input].append(val)

    return yaxis

def plot_helper(yaxis, title):
    plot = plt.figure(figsize=(9,6))

    for label, y in yaxis.items():
        y = np.asarray(y)

        plt.plot(factors, y, label=label)

    plt.xlabel("Factor")
    plt.ylabel(title)

    plt.legend()
    plt.tight_layout()
    return plot

def plotter(desired_output):
    if desired_output in ("Q_s", "Q_p", "Q_total", "P_a", "P_v"):
        yaxis = yaxis_class1(desired_output)
        plot_helper(yaxis, desired_output)

    elif desired_output in ("S_m", "S_sv", "OD2"):
        yaxis = yaxis_class2(desired_output)
        plot_helper(yaxis, desired_output)


plotter("Q_total")

yaxis = yaxis_class1("Q_total")
test = plot_helper(yaxis, "Q_total")
test.show()
print(test)