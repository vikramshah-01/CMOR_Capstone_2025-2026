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

import os
import numpy as np
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)

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
        "HR": 100,    # Heart Rate (beats/min)
        "UVR": 45,    # Upper Vascular Resistance (Wood Units)
        "LVR": 35,    # Lower Vascular Resistance (Wood Units)
        "PVR": 10,    # Pulmonary Vascular Resistance (Wood Units)
        "S_sa": 0.99, # Systemic Artery Saturation (%)
        "Hb": 15,     # Hemoglobin (g/dL)
        "CVO2u": 70,  # Upper Body Oxygen Consumption (mL O2/min)
        "CVO2l": 50,  # Lower Body Oxygen Consumption (mL O2/min)
        "C_d": 2 / 100,  # Compliance at Diastole
        "C_s": 0.01 / 100,  # Compliance at Systole
        "C_sa": 1 / 135,  # Compliance of Systemic Artery/Total Blood Volume
        "C_pv": 30 / 135, # Compliance of Pulmonary Vein/Total Blood Volume
        "C_pa": 2 / 135   # Compliance of Pulmonary Artery/Total Blood Volume
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

            # # Solve for flows and oxygen saturation
            # try:
            #     results = complete_results(
            #         params["UVR"], params["LVR"], params["PVR"], params["HR"],
            #         params["C_d"], params["C_s"], params["C_sa"], params["C_pv"], params["C_pa"],
            #         z0_flows, params["S_sa"], params["CVO2u"], params["CVO2l"], params["Hb"], z0_sat
            #     )
                
            #     # Store the result in the grid
            #     Z[j, i] = results[output]

            # except Exception as e:
            #     Z[j, i] = np.nan  # If the solver fails, store NaN

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

@app.route('/apply_preset')
def apply_preset():
    global updated_compliance_values
    condition = request.args.get("condition")

    presets = {
        "lowPreload": {
            # compliances all increased by 20% of normal
            "HR": 100, "UVR": 45, "LVR": 35, "PVR": 10, "S_sa": 0.99, "Hb": 15, "CVO2u": 70, "CVO2l": 50,
            "C_d": 0.02, "C_s": 0.01/100, "C_sa": 2/225, "C_pv": 4/15, "C_pa": 4/225  
        },
        "lungProblem": {
            # no compliance changes
            "HR": 100, "UVR": 45, "LVR": 35, "PVR": 27, "S_sa": 0.99, "Hb": 15, "CVO2u": 70, "CVO2l": 50,
            "C_d": 0.02241, "C_s": 0.00008625, "C_sa": 0.005115, "C_pv": 0.2986, "C_pa": 0.01481
        },
        "heartFailure": {
            # C_d decreased by 20%, C_s increased by 20%, other compliances remain the same
            "HR": 100, "UVR": 45, "LVR": 35, "PVR": 10, "S_sa": 0.99, "Hb": 15, "CVO2u": 70, "CVO2l": 50,
            "C_d": 0.016, "C_s": 0.00008, "C_sa": 1/135, "C_pv": 30/135, "C_pa": 2/135  
        } 
    }

    if condition in presets:
        preset_values = presets[condition]

        # updates compliances only if they exist in the preset
        updated_compliance_values.update({
            "C_d": preset_values["C_d"],
            "C_s": preset_values["C_s"],
            "C_sa": preset_values["C_sa"],
            "C_pv": preset_values["C_pv"],
            "C_pa": preset_values["C_pa"]
        })

        print(f"/PRESET Updated compliance values for {condition}: {updated_compliance_values}")

        return jsonify({"message": f"Preset {condition} applied!", "compliance_values": updated_compliance_values})
    return jsonify({"error": "Invalid condition"}), 400

@app.route("/calculate_condition_values", methods=["POST"])
def calculate_condition_values():
    global updated_compliance_values  # Ensure the latest values are used
    print(f"/CALCULATE compliance values: {updated_compliance_values}")

    data = request.json # get slider values
    if not data:
        return jsonify({"error": "No slider values receive."}), 400
       
    # Extract slider values from frontend
    HR = float(data.get("HR"))
    UVR = float(data.get("UVR"))
    LVR = float(data.get("LVR"))
    PVR = float(data.get("PVR"))
    S_sa = float(data.get("S_sa"))
    Hb = float(data.get("Hb"))
    CVO2u = float(data.get("CVO2u"))
    CVO2l = float(data.get("CVO2l"))

    # Use the latest compliance values
    C_d = updated_compliance_values["C_d"]
    C_s = updated_compliance_values["C_s"]
    C_sa = updated_compliance_values["C_sa"]
    C_pv = updated_compliance_values["C_pv"]
    C_pa = updated_compliance_values["C_pa"]

    print(f"C_d: {C_d}, C_s: {C_s}, C_sa: {C_sa}, C_pv: {C_pv}, C_pa: {C_pa}")

    # Solve for new vitals
    param_flows = (UVR, LVR, PVR, HR, C_d, C_s, C_sa, C_pv, C_pa)
    z0_flows = (3.1, 1.5, 1.5, 3.2, 75, 26, 2)

    result_flows = scipy.optimize.fsolve(fun_flows, z0_flows, args=param_flows, full_output=True, xtol=1e-4)
    (Q_v, Q_u, Q_l, Q_p, P_sa, P_pa, P_pv) = result_flows[0]

    param_sat = (Q_p, Q_u, Q_l, S_sa, CVO2u, CVO2l, Hb)
    z0_sat = (0.55, 0.99, 0.55, 0.55)

    result_O2_sat = scipy.optimize.fsolve(fun_sat, z0_sat, args=param_sat, full_output=True, xtol=1e-4)
    (S_pa, S_pv, S_svu, S_svl) = result_O2_sat[0]

    OER = (Q_u * (S_sa - S_svu) + Q_l * (S_sa - S_svl)) / ((Q_u + Q_l) * S_sa)

    # Send back computed values
    computed_values = {
        "Q_v": round(Q_v, 2),
        "Q_u": round(Q_u, 2),
        "Q_l": round(Q_l, 2),
        "Q_p": round(Q_p, 2),
        "P_sa": round(P_sa, 2),
        "P_pa": round(P_pa, 2),
        "P_pv": round(P_pv, 2),
        "S_pa": round(S_pa, 2),
        "S_pv": round(S_pv, 2),
        "S_svu": round(S_svu, 2),
        "S_svl": round(S_svl, 2),
        "OER": round(OER, 2),
        "C_d": C_d,
        "C_s": C_s,
        "C_sa": C_sa,
        "C_pv": C_pv,
        "C_pa": C_pa
    }

    print(f"Computed values sent: {computed_values}")
    return jsonify(computed_values)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
