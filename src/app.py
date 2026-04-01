from flask import Flask, render_template, request, jsonify, send_from_directory
from hlhs_model import fun_flows, fun_sat, update_compliance, C_d, C_s, C_sa, C_pv, C_pa
import scipy.optimize

import numpy as np
import matplotlib.pyplot as plt
import scipy as sp
from Norwood_Circulation_Solver_Functions import flow_pressure_solver_1, flow_pressure_solver_2, saturation_solver
from arterial_and_venous_compliance_solver import arterial_and_venous_compliance_solver
from systolic_and_diastolic_compliance_solver import systolic_and_diastolic_compliance_solver
from norwood_plots import yaxis_class1, yaxis_class2
from time_dependent_model import time_dependent_norwood, Q_Ao
# from time_dependent_model import time_dependent_norwood

import os
import numpy as np
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)

# Ensure you have a folder to save plots
#PLOTS_FOLDER = 'static/plots'
#os.makedirs(PLOTS_FOLDER, exist_ok=True)

# Render the pages
@app.route("/")
def index():
    return render_template("index.html")

@app.route('/slider_page')
def slider():
    return render_template('slider_page.html')

@app.route('/plot_page')
def display_plot():
    return render_template('plot_page.html')

@app.route('/timedep_page')
def timedep_plot():
    return render_template('timedep_page.html')

@app.route('/heatmap_page')
def heatmap():
    return render_template('heatmap_page.html')

@app.route('/conditions_page')
def conditions_page():
    return render_template('conditions_page.html')

# Process the slider input
@app.route("/process", methods=["POST"])
def process():

    data = request.json
    HR = float(data.get("HR"))  # Slider value, e.g., heart rate
    C_sys = float(data.get("C_sys"))
    C_dia = float(data.get("C_dia"))
    C_A = float(data.get("C_A"))
    C_V = float(data.get("C_V"))
    R_s = float(data.get("R_s"))
    R_p = float(data.get("R_p"))
    V_total = float(data.get("V_total"))
    Hb = float(data.get("Hb"))
    CVO2 = float(data.get("CVO2"))

    Q_s, Q_p, P_a, P_v = flow_pressure_solver_1(C_dia, C_sys, C_A, C_V, HR, R_p, R_s, V_total)
    S_m, S_sv, OD2 = saturation_solver(Q_s, Q_p, Hb, CVO2)


    return jsonify({
        "Q_s": round(Q_s, 2),
        "Q_p": round(Q_p, 2),
        "P_a": round(P_a, 2),
        "P_v": round(P_v, 2),
        "S_m": round(S_m, 2),
        "S_sv": round(S_sv, 2),
        "OD2": round(OD2, 2),
    })

# Route to generate a plot based on user selection
@app.route('/generate_plot')
def generate_plot():
    factors = np.arange(0.5, 1.55, 0.05)

    plot_type = request.args.get('plot_type')

    if plot_type in ("Q_s", "Q_p", "Q_total", "P_a", "P_v"):
        yaxis = yaxis_class1(plot_type)
        plot = plt.figure(figsize=(9,6))

        for label, y in yaxis.items():
            y = np.asarray(y)

            plt.plot(factors, y, label=label)

        plt.xlabel("Factor")
        plt.ylabel(plot_type)

        plt.legend()
        plt.tight_layout()

    elif plot_type in ("S_m", "S_sv", "OD2"):
        yaxis = yaxis_class1(plot_type)
        plot = plt.figure(figsize=(9,6))

        for label, y in yaxis.items():
            y = np.asarray(y)

            plt.plot(factors, y, label=label)

        plt.xlabel("Factor")
        plt.ylabel(plot_type)

        plt.legend()
        plt.tight_layout()

    else:
        return jsonify({'error': 'Invalid plot type'}), 400

    # Convert the plot to a PNG image
    img = io.BytesIO()
    plot.savefig(img, format='png')
    img.seek(0)
    
    # Encode the image as base64
    plot_data = base64.b64encode(img.getvalue()).decode('utf-8')

    return jsonify({'plot': plot_data})

import seaborn as sns
from io import BytesIO
@app.route('/generate_custom_plot')
def generate_custom_plot():
    # Capture the query parameters from the frontend
    input1 = request.args.get('input1')
    input2 = request.args.get('input2')
    output = request.args.get('output')

    baseline_values = {
            "HR": 100,
            "C_dia": 0.02,
            "C_sys": 0.01,
            "C_A": 1/135,
            "C_V": 30/135,
            "R_p": 10,
            "R_s": 80,
            "V_total": 5.0,
            "EF": 0.55,
            "Hb": 15,
            "CVO2": 200,
    }

    # Initial guesses for solvers
    z0_flows = [3.0, 1.5, 1.5, 3.0, 90, 5, 10]  # Initial guesses for fun_flows
    z0_sat = [0.8, 0.7, 0.7, 0.7]  # Initial guesses for fun_sat

    # Define value ranges for the two input parameters (±50% of baseline)
    input1_values = np.linspace(baseline_values[input1] * 0.5, baseline_values[input1] * 1.5, 50)
    input2_values = np.linspace(baseline_values[input2] * 0.5, baseline_values[input2] * 1.5, 50)

    # Create a grid for the heatmap
    Z = np.zeros((len(input2_values), len(input1_values)))

    for i, val1 in enumerate(input1_values):
        for j, val2 in enumerate(input2_values):
            # Set parameter values for this iteration, keeping others at baseline
            params = baseline_values.copy()
            params[input1] = val1
            params[input2] = val2

            # Solve Norwood model
            Q_s, Q_p, P_a, P_v = flow_pressure_solver_1(
                params["C_dia"],
                params["C_sys"],
                params["C_A"],
                params["C_V"],
                params["HR"],
                params["R_p"],
                params["R_s"],
                params["V_total"]
)

            # Compute saturation if needed
            if output in ["S_m", "S_sv", "D20"]:
                S_m, S_sv, D20 = saturation_solver(
                    Q_s, Q_p, params["Hb"], params["CVO2"]
                )
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


    # Plot the heatmap
    plt.figure(figsize=(10, 7.5))
    heatmap = sns.heatmap(Z, xticklabels=np.round(input1_values, 1), yticklabels=np.round(input2_values, 1),
                cmap="coolwarm", cbar_kws={'label': output}, linewidths=0.5)
    plt.xlabel(input1, fontsize=14)
    plt.ylabel(input2, fontsize=14)
    plt.title(f"Heatmap of {output}", fontsize = 18)

    # Invert the direction of the y-axis
    plt.gca().invert_yaxis()
    #make ticks readably small
    plt.tick_params(axis='both', which='major', labelsize=7)
    # Customize the color bar labels font size
    cbar = heatmap.collections[0].colorbar
    cbar.ax.tick_params(labelsize=12)  # Adjust the size of the color bar labels
    cbar.set_label(output, fontsize=14)  # Adjust font size of the color bar label

    # Convert plot to PNG and encode as Base64
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plot_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()

    return jsonify({"plot": plot_base64})

updated_compliance_values = {
    "C_d": C_d,
    "C_s": C_s,
    "C_sa": C_sa,
    "C_pv": C_pv,
    "C_pa": C_pa
    }

@app.route('/generate_timedep_plot')
def generate_timedep_plot():
    def qfloat(name, default):
        raw = request.args.get(name, None)
        if raw is None or raw == "":
            return float(default)
        return float(raw)

    # defaults (same as your current hard-coded values)
    R_s    = qfloat("R_s",   17.5)
    R_p    = qfloat("R_p",   1.79)
    R_BTS  = qfloat("R_BTS", 5.0)
    C_s    = qfloat("C_s",   0.01)
    C_p    = qfloat("C_p",   0.08)
    P_sa_0 = qfloat("P_sa_0", 20.0)
    P_pa_0 = qfloat("P_pa_0", 20.0)
    t_end  = qfloat("t_end", 0.1)
    dt     = qfloat("dt",    0.00001)

    # simple guardrails (time_dependent_norwood already raises for <=0 too :contentReference[oaicite:4]{index=4})
    if t_end <= 0 or dt <= 0:
        return jsonify({"error": "t_end and dt must be > 0"}), 400
    if dt >= t_end:
        return jsonify({"error": "dt must be smaller than t_end"}), 400

    plot_type = request.args.get("plot_type", "flows")

    (t, Q_sa, Q_sv, Q_pa, Q_pv, P_sa, P_sv, P_pa, P_pv) = time_dependent_norwood(
        R_s, R_p, R_BTS,
        C_s, C_p,
        P_sa_0, P_pa_0,
        Q_Ao,
        t_end, dt
    )

    Q_AO = np.array([Q_Ao(ti) for ti in t])

    fig = plt.figure(figsize=(9,6))

    if plot_type == "flows":
        plt.plot(t, Q_sa, label="Q_SA")
        plt.plot(t, Q_sv, label="Q_SV")
        plt.plot(t, Q_pa, label="Q_PA")
        plt.plot(t, Q_pv, label="Q_PV")
        plt.plot(t, Q_AO, "--", label="Q_AO")
        plt.ylabel("Flow [L/min]")
        plt.title("Flows")

    elif plot_type == "pressures":
        plt.plot(t, P_sa, label="P_SA")
        plt.plot(t, P_sv, label="P_SV")
        plt.plot(t, P_pa, label="P_PA")
        plt.plot(t, P_pv, label="P_PV")
        plt.ylabel("Pressure [mmHg]")
        plt.title("Pressures")

    elif plot_type == "aortic":
        plt.plot(t, Q_AO, label="Q_AO")
        plt.ylabel("Flow [L/min]")
        plt.title("Aortic Flow")

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

@app.route('/apply_preset')
def apply_preset():
    """
    Return report-style baseline inputs with drug effects applied to R_s and R_p.
    Compatible with the report-style HTML/JS fields:
    HR, EF, C_dia, C_A, C_V, R_s, R_p, V_total, Hb, CVO2
    """
    condition = request.args.get("condition", "").strip().lower()

    baseline = {
        "HR": 100.0,
        "EF": 0.55,
        "C_dia": 0.02,
        "C_A": 1 / 135,
        "C_V": 30 / 135,
        "R_s": 80.0,
        "R_p": 10.0,
        "V_total": 5.0,
        "Hb": 15.0,
        "CVO2": 200.0,
    }

    drug_effects = {
        "nicardipine": {
            "svr_reduction": 0.30,
            "pvr_reduction": 0.05,
            "selectivity": "Poor pulmonary selectivity"
        },
        "milrinone": {
            "svr_reduction": 0.175,
            "pvr_reduction": 0.225,
            "selectivity": "Moderate pulmonary selectivity"
        },
        "sildenafil": {
            "svr_reduction": 0.10,
            "pvr_reduction": 0.30,
            "selectivity": "Good pulmonary selectivity"
        },
        "ino": {
            "svr_reduction": 0.00,
            "pvr_reduction": 0.45,
            "selectivity": "Excellent pulmonary selectivity"
        },
        "epoprostenol": {
            "svr_reduction": 0.15,
            "pvr_reduction": 0.40,
            "selectivity": "Good pulmonary selectivity"
        }
    }

    if condition not in drug_effects:
        return jsonify({"error": "Invalid drug selection"}), 400

    effect = drug_effects[condition]

    preset_values = {
        **baseline,
        "R_s": round(baseline["R_s"] * (1 - effect["svr_reduction"]), 4),
        "R_p": round(baseline["R_p"] * (1 - effect["pvr_reduction"]), 4),
        "drug": condition,
        "selectivity": effect["selectivity"]
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

        C_sys = 0.01

        Q_s, Q_p, P_a, P_v = flow_pressure_solver_1(
            C_dia, C_sys, C_A, C_V, HR, R_p, R_s, V_total
        )
        print("Flow outputs:", Q_s, Q_p, P_a, P_v)

        S_m, S_sv, OD2 = saturation_solver(Q_s, Q_p, Hb, CVO2)
        print("Sat outputs:", S_m, S_sv, OD2)

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
            "Qp_Qs": round(Qp_Qs, 4) if Qp_Qs is not None else None
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to calculate condition values: {str(e)}"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
