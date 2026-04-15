from flask import Flask, render_template, request, jsonify

import numpy as np
import matplotlib.pyplot as plt
import scipy as sp
from Norwood_Circulation_Solver_Functions import (
    flow_pressure_solver_1,
    flow_pressure_solver_2,
    saturation_solver,
)
from arterial_and_venous_compliance_solver import arterial_and_venous_compliance_solver
from systolic_and_diastolic_compliance_solver import systolic_and_diastolic_compliance_solver
from norwood_plots import yaxis_class1, yaxis_class2
from time_dependent_model import time_dependent_norwood, time_dependent_norwood_valve, Q_Ao_2

import os
import io
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)

# --------------------------------------------------
# Helpers
# --------------------------------------------------

DEFAULT_BSA = 0.25  # representative infant body surface area in m^2

def indexed_cvo2_to_vo2(indexed_cvo2, bsa=DEFAULT_BSA):
    """
    Convert indexed oxygen consumption (mL/m^2/min) to absolute VO2 (mL/min).
    """
    return indexed_cvo2 * bsa


def validate_physiology(S_m, S_sv, OD2):
    """
    Raise an error if outputs are non-physiologic.
    """
    if not (0 <= S_m <= 1):
        raise ValueError(f"Non-physiologic mixed saturation: {S_m:.4f}")

    if not (0 <= S_sv <= 1):
        raise ValueError(f"Non-physiologic systemic venous saturation: {S_sv:.4f}")

    if OD2 < 0:
        raise ValueError(f"Non-physiologic oxygen delivery: {OD2:.4f}")


def get_clinical_baseline():
    """
    More reasonable default baseline for the EF-based steady-state model.
    """
    return {
        "HR": 120.0,
        "EF": 0.45,
        "C_dia": 0.01,
        "C_A": 0.03,
        "C_V": 0.20,
        "R_s": 25.0,
        "R_p": 20.0,
        "V_total": 1.0,
        "Hb": 15.0,
        "CVO2": 160.0,  # indexed oxygen consumption (mL/m^2/min)
    }


# --------------------------------------------------
# Render pages
# --------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/slider_page")
def slider():
    return render_template("slider_page.html")


@app.route("/plot_page")
def display_plot():
    return render_template("plot_page.html")


@app.route("/timedep_page")
def timedep_plot():
    return render_template("timedep_page.html")


@app.route("/heatmap_page")
def heatmap():
    return render_template("heatmap_page.html")


@app.route("/conditions_page")
def conditions_page():
    return render_template("conditions_page.html")


# --------------------------------------------------
# Adjustable parameters page
# --------------------------------------------------

@app.route("/process", methods=["POST"])
def process():
    data = request.json

    if not data:
        return jsonify({"error": "No input data received."}), 400

    try:
        HR = float(data.get("HR"))
        C_sys = float(data.get("C_sys"))
        C_dia = float(data.get("C_dia"))
        C_A = float(data.get("C_A"))
        C_V = float(data.get("C_V"))
        R_s = float(data.get("R_s"))
        R_p = float(data.get("R_p"))
        V_total = float(data.get("V_total"))
        Hb = float(data.get("Hb"))
        CVO2 = float(data.get("CVO2"))

        Q_s, Q_p, P_a, P_v = flow_pressure_solver_1(
            C_dia, C_sys, C_A, C_V, HR, R_p, R_s, V_total
        )

        VO2 = indexed_cvo2_to_vo2(CVO2)
        S_m, S_sv, OD2 = saturation_solver(Q_s, Q_p, Hb, VO2)
        validate_physiology(S_m, S_sv, OD2)

        return jsonify({
            "Q_s": round(Q_s, 2),
            "Q_p": round(Q_p, 2),
            "P_a": round(P_a, 2),
            "P_v": round(P_v, 2),
            "S_m": round(S_m, 4),
            "S_sv": round(S_sv, 4),
            "OD2": round(OD2, 2),
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to process inputs: {str(e)}"}), 400


# --------------------------------------------------
# Variable response plots
# --------------------------------------------------

@app.route("/generate_plot")
def generate_plot():
    factors = np.arange(0.5, 1.55, 0.05)
    plot_type = request.args.get("plot_type")

    if plot_type in ("Q_s", "Q_p", "Q_total", "P_a", "P_v"):
        yaxis = yaxis_class1(plot_type)
        plot = plt.figure(figsize=(9, 6))

        for label, y in yaxis.items():
            y = np.asarray(y)
            plt.plot(factors, y, label=label)

        plt.xlabel("Factor")
        plt.ylabel(plot_type)
        plt.legend()
        plt.tight_layout()

    elif plot_type in ("S_m", "S_sv", "OD2"):
        yaxis = yaxis_class1(plot_type)
        plot = plt.figure(figsize=(9, 6))

        for label, y in yaxis.items():
            y = np.asarray(y)
            plt.plot(factors, y, label=label)

        plt.xlabel("Factor")
        plt.ylabel(plot_type)
        plt.legend()
        plt.tight_layout()

    else:
        return jsonify({"error": "Invalid plot type"}), 400

    img = io.BytesIO()
    plot.savefig(img, format="png")
    img.seek(0)
    plot_data = base64.b64encode(img.getvalue()).decode("utf-8")
    plt.close(plot)

    return jsonify({"plot": plot_data})


# --------------------------------------------------
# Heatmap page
# --------------------------------------------------

@app.route("/generate_custom_plot")
def generate_custom_plot():
    input1 = request.args.get("input1")
    input2 = request.args.get("input2")
    output = request.args.get("output")

    baseline_values = {
        "HR": 100,
        "C_dia": 0.02,
        "C_sys": 0.01,
        "C_A": 1 / 135,
        "C_V": 30 / 135,
        "R_p": 10,
        "R_s": 80,
        "V_total": 5.0,
        "EF": 0.55,
        "Hb": 15,
        "CVO2": 200,
    }

    input1_values = np.linspace(baseline_values[input1] * 0.5, baseline_values[input1] * 1.5, 50)
    input2_values = np.linspace(baseline_values[input2] * 0.5, baseline_values[input2] * 1.5, 50)

    Z = np.zeros((len(input2_values), len(input1_values)))

    for i, val1 in enumerate(input1_values):
        for j, val2 in enumerate(input2_values):
            params = baseline_values.copy()
            params[input1] = val1
            params[input2] = val2

            Q_s, Q_p, P_a, P_v = flow_pressure_solver_1(
                params["C_dia"],
                params["C_sys"],
                params["C_A"],
                params["C_V"],
                params["HR"],
                params["R_p"],
                params["R_s"],
                params["V_total"],
            )

            if output in ["S_m", "S_sv", "D20"]:
                VO2 = indexed_cvo2_to_vo2(params["CVO2"])
                S_m, S_sv, D20 = saturation_solver(Q_s, Q_p, params["Hb"], VO2)

            if output == "Q_s":
                Z[j, i] = Q_s
            elif output == "Q_p":
                Z[j, i] = Q_p
            elif output == "P_a":
                Z[j, i] = P_a
            elif output == "P_v":
                Z[j, i] = P_v
            elif output == "S_m":
                Z[j, i] = S_m
            elif output == "S_sv":
                Z[j, i] = S_sv
            elif output == "D20":
                Z[j, i] = D20

    plt.figure(figsize=(10, 7.5))
    heatmap = sns.heatmap(
        Z,
        xticklabels=np.round(input1_values, 1),
        yticklabels=np.round(input2_values, 1),
        cmap="coolwarm",
        cbar_kws={"label": output},
        linewidths=0.5,
    )
    plt.xlabel(input1, fontsize=14)
    plt.ylabel(input2, fontsize=14)
    plt.title(f"Heatmap of {output}", fontsize=18)
    plt.gca().invert_yaxis()
    plt.tick_params(axis="both", which="major", labelsize=7)

    cbar = heatmap.collections[0].colorbar
    cbar.ax.tick_params(labelsize=12)
    cbar.set_label(output, fontsize=14)

    img = io.BytesIO()
    plt.savefig(img, format="png", bbox_inches="tight")
    img.seek(0)
    plot_base64 = base64.b64encode(img.getvalue()).decode("utf-8")
    plt.close()

    return jsonify({"plot": plot_base64})

# --------------------------------------------------
# Time dependent page
# --------------------------------------------------

@app.route("/generate_timedep_plot")
def generate_timedep_plot():
    def qfloat(name, default):
        raw = request.args.get(name, None)
        if raw is None or raw == "":
            return float(default)
        return float(raw)

    R_s = qfloat("R_s", 62)
    R_p = qfloat("R_p", 6)
    R_BTS = qfloat("R_BTS", 48)
    C_s = qfloat("C_s", 0.0004)
    C_p = qfloat("C_p", 0.0007)
    P_sa_0 = qfloat("P_sa_0", 20.0)
    P_pa_0 = qfloat("P_pa_0", 20.0)
    t_end = qfloat("t_end", 0.1)
    dt = qfloat("dt", 0.00001)

    if t_end <= 0 or dt <= 0:
        return jsonify({"error": "t_end and dt must be > 0"}), 400
    if dt >= t_end:
        return jsonify({"error": "dt must be smaller than t_end"}), 400

    plot_type = request.args.get("plot_type", "flows")

    (t1, Q_sa1, Q_sv1, Q_pa1, Q_pv1, P_sa1, P_sv1, P_pa1, P_pv1) = time_dependent_norwood(
        R_s, R_p, R_BTS,
        C_s, C_p,
        P_sa_0, P_pa_0,
        Q_Ao_2,          
        t_end, dt
    )

    (t2, Q_sa2, Q_sv2, Q_pa2, Q_pv2, P_sa2, P_sv2, P_pa2, P_pv2) = time_dependent_norwood_valve(
        R_s, R_p, R_BTS,
        C_s, C_p,
        P_sa_0, P_pa_0,
        Q_Ao_2,          
        t_end, dt
    )


    Q_AO = np.array([Q_Ao_2(ti) for ti in t1])
    fig = plt.figure(figsize=(9, 6))

    if plot_type == "flows":
        plt.plot(t2, Q_sa2, label="Q_SA")
        plt.plot(t2, Q_sv2, label="Q_SV")
        plt.plot(t2, Q_pa2, label="Q_PA")
        plt.plot(t2, Q_pv2, label="Q_PV")
        plt.plot(t2, Q_AO, "--", label="Q_AO (input)")
        plt.title("Time Dependent Plot: Flows")
        plt.xlabel("Time [min]")
        plt.ylabel("Flow [L/min]")
        plt.grid(True)
        plt.legend()

    elif plot_type == "pressures":
        plt.plot(t2, P_sa2, label="P_SA")
        plt.plot(t2, P_sv2, label="P_SV")
        plt.plot(t2, P_pa2, label="P_PA")
        plt.plot(t2, P_pv2, '--', label="P_PV")
        plt.title("Time Dependent Plot: Pressures")
        plt.xlabel("Time [min]")
        plt.ylabel("Pressure [mmHg]")
        plt.grid(True)
        plt.legend()

    elif plot_type == "aortic":
        plt.plot(t2, Q_AO, "-", label="Q_AO (input)")
        plt.title("Time Dependent Plot: Aortic Flow")
        plt.xlabel("Time [min]")
        plt.ylabel("Flow [L/min]")
        plt.grid(True)
        plt.legend()

    else:
        plt.close(fig)
        return jsonify({"error": "Invalid plot type"}), 400

    plt.xlabel("Time [min]")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    img = io.BytesIO()
    fig.savefig(img, format="png", bbox_inches="tight")
    img.seek(0)
    plot_data = base64.b64encode(img.getvalue()).decode("utf-8")
    plt.close(fig)

    return jsonify({"plot": plot_data})


# --------------------------------------------------
# Clinical conditions page
# --------------------------------------------------

@app.route("/apply_preset")
def apply_preset():
    """
    Return report-style baseline inputs with drug effects applied to R_s and R_p.
    Compatible with:
    HR, EF, C_dia, C_A, C_V, R_s, R_p, V_total, Hb, CVO2
    """
    condition = request.args.get("condition", "").strip().lower()
    baseline = get_clinical_baseline()

    drug_effects = {
        "nicardipine": {
            "svr_reduction": 0.30,
            "pvr_reduction": 0.05,
            "selectivity": "Poor pulmonary selectivity",
        },
        "milrinone": {
            "svr_reduction": 0.175,
            "pvr_reduction": 0.225,
            "selectivity": "Moderate pulmonary selectivity",
        },
        "sildenafil": {
            "svr_reduction": 0.10,
            "pvr_reduction": 0.30,
            "selectivity": "Good pulmonary selectivity",
        },
        "ino": {
            "svr_reduction": 0.00,
            "pvr_reduction": 0.45,
            "selectivity": "Excellent pulmonary selectivity",
        },
        "epoprostenol": {
            "svr_reduction": 0.15,
            "pvr_reduction": 0.40,
            "selectivity": "Good pulmonary selectivity",
        },
    }

    if condition not in drug_effects:
        return jsonify({"error": "Invalid drug selection"}), 400

    effect = drug_effects[condition]

    preset_values = {
        **baseline,
        "R_s": round(baseline["R_s"] * (1 - effect["svr_reduction"]), 4),
        "R_p": round(baseline["R_p"] * (1 - effect["pvr_reduction"]), 4),
        "drug": condition,
        "selectivity": effect["selectivity"],
    }

    return jsonify(preset_values)


@app.route("/calculate_condition_values", methods=["POST"])
def calculate_condition_values():
    data = request.json
    print("Received /calculate_condition_values payload:", data)

    if not data:
        return jsonify({"error": "No input data received."}), 400

    try:
        HR = float(data.get("HR"))
        EF = float(data.get("EF"))
        C_dia = float(data.get("C_dia"))
        C_A = float(data.get("C_A"))
        C_V = float(data.get("C_V"))
        R_s = float(data.get("R_s"))
        R_p = float(data.get("R_p"))
        V_total = float(data.get("V_total"))
        Hb = float(data.get("Hb"))
        CVO2 = float(data.get("CVO2"))

        print("Parsed inputs:", HR, EF, C_dia, C_A, C_V, R_s, R_p, V_total, Hb, CVO2)

        # EF-based steady-state model from the report
        Q_s, Q_p, P_a, P_v = flow_pressure_solver_2(
            C_dia, C_A, C_V, HR, R_p, R_s, V_total, EF
        )
        print("Flow outputs:", Q_s, Q_p, P_a, P_v)

        VO2 = indexed_cvo2_to_vo2(CVO2)
        S_m, S_sv, OD2 = saturation_solver(Q_s, Q_p, Hb, VO2)
        print("Sat outputs:", S_m, S_sv, OD2)

        validate_physiology(S_m, S_sv, OD2)

        Q_RV = Q_s + Q_p
        Qp_Qs = Q_p / Q_s if Q_s != 0 else None

        return jsonify({
            "Q_s": round(Q_s, 2),
            "Q_p": round(Q_p, 2),
            "Q_RV": round(Q_RV, 2),
            "P_a": round(P_a, 2),
            "P_v": round(P_v, 2),
            "S_m": round(S_m, 4),
            "S_sv": round(S_sv, 4),
            "OD2": round(OD2, 2),
            "Qp_Qs": round(Qp_Qs, 4) if Qp_Qs is not None else None,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to calculate condition values: {str(e)}"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)