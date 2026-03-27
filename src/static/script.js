// =============================================
// GENERAL UTILITY FUNCTIONS (Used across pages)
// =============================================

function updateValue(displayId, value) {
    const element = document.getElementById(displayId);
    if (element) {
        element.innerText = value;
    }
}

function showConfirmationModal(condition) {
    console.log("Modal invoked with condition:", condition);

    const modal = document.getElementById("confirmation-modal");
    const modalText = document.getElementById("modal-text");

    if (modal && modalText) {
        const messages = {
            lowPreload: "Low Preload preset applied! Low preload refers to a reduced volume of blood returning to the heart, which limits the heart's ability to fill and pump effectively. This can occur due to hemorrhage, where blood is lost from the circulatory system; dehydration, which reduces overall intravascular volume; or obstruction, where physical barriers like tension pneumothorax or cardiac tamponade impede venous return. In each of these scenarios, the heart receives less blood during diastole, resulting in decreased stroke volume and cardiac output.",
            lungProblem: "Lung Problem preset applied! Pulmonary diseases increase pulmonary vascular resistance, making it harder for blood to flow into the lungs. This reduces preload to the single ventricle, leading to decreased cardiac output. Even mild lung disease can have a major impact in Fontan patients due to their delicate hemodynamics.",
            heartFailure: "Heart Failure preset applied! In Fontan circulation, heart failure can develop due to the unique strain placed on the single functioning ventricle and the passive nature of pulmonary blood flow. Over time, the single ventricle may struggle to maintain adequate cardiac output. Ventricular dysfunction—whether systolic or diastolic—further compromises forward flow, leading to systemic congestion, exercise intolerance, and fatigue."
        };

        // Normalize in case the condition is not exact
        const normalized = condition.trim();

        modalText.innerText = messages[normalized] || "Preset applied successfully!";
        modal.style.display = "block";

        document.getElementById("modal-close").onclick = function () {
            modal.style.display = "none";
        };

        window.onclick = function (event) {
            if (event.target === modal) {
                modal.style.display = "none";
            }
        };
    }
}

// =============================================
// IMAGE MAP AND MODAL FUNCTIONALITY
// (For index.html with the Fontan diagram)
// =============================================

function setupImageMapModal() {
    const modal = document.getElementById('popup-modal');
    const modalText = document.getElementById('diagram-text');
    const closeButton = document.getElementById('diagram-close');
    const image = document.getElementById('clickable-image');

    if (!modal || !modalText || !closeButton || !image) return;

    // Add click listeners to each area
    document.querySelectorAll('area').forEach((area) => {
        area.addEventListener('click', (e) => {
            e.preventDefault();
            const content = area.getAttribute('data-content');
            modalText.textContent = content;
            modal.style.display = 'block';
        });
    });

    // Close handlers
    closeButton.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    // Initialize image map resizing
    if (typeof imageMapResize === 'function') {
        imageMapResize();
    }
}

// =============================================
// SLIDER PAGE FUNCTIONALITY (/slider_page)
// =============================================

function setupSliderPage() {
    const form = document.getElementById('parameterForm');
    if (!form) return;

    // Create a container for the results table if it doesn't exist
    let resultsContainer = document.getElementById('sliderResults');
    if (!resultsContainer) {
        resultsContainer = document.createElement('div');
        resultsContainer.id = 'sliderResults';
        form.appendChild(resultsContainer);
    }

    form.addEventListener('submit', function(event) {
        event.preventDefault();

        // collect slider values
        const HR = document.getElementById('HR').value;
        const C_sys = document.getElementById('C_sys').value;
        const C_dia = document.getElementById('C_dia').value;
        const C_A = document.getElementById('C_A').value;
        const C_V = document.getElementById('C_V').value;
        const R_s = document.getElementById('R_s').value;
        const R_p = document.getElementById('R_p').value;
        const V_total = document.getElementById('V_total').value;
        const Hb = document.getElementById('Hb').value;
        const CVO2 = document.getElementById('CVO2').value;


        fetch('/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ HR, C_sys, C_dia, C_A, C_V, R_s, R_p, V_total, Hb, CVO2 })
        })
        .then(response => response.json())
        .then(data => {
           // Generate single-column results table
           const resultsSiv = document.getElementById("sliderResults");
           if (resultsSiv) {
                resultsContainer.innerHTML = `
                <div class="card results-card">
                    <table class="results-table">
                        <thead>
                            <tr>
                                <th>Output Parameter</th>
                                <th>Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td>Systemic flow</td><td>${data.Q_s}</td></tr>
                            <tr><td>Pulmonary flow</td><td>${data.Q_p}</td></tr>
                            <tr><td>Arterial pressure</td><td>${data.P_a}</td></tr>
                            <tr><td>Venous pressure</td><td>${data.P_v}</td></tr>
                            <tr><td>Mixed oxygen saturation</td><td>${data.S_m}</td></tr>
                            <tr><td>Systemic venous saturation</td><td>${data.S_sv}</td></tr>
                            <tr><td>Oxygen delivery</td><td>${data.OD2}</td></tr>
                        </tbody>
                    </table>
                </div>
                `;
                resultsDiv.style.display = "block";
           }
   })
        .catch(error => console.error('Error:', error));
    });
}

// =============================================
// CONDITIONS PAGE FUNCTIONALITY (/conditions_page)
// =============================================

function setupConditionsPage() {
    // Apply preset when a preset button is clicked
    document.querySelectorAll(".preset-btn").forEach(button => {
        button.addEventListener("click", function() {
            const condition = this.dataset.condition;
            fetch(`/apply_preset?condition=${condition}`)
            .then(response => response.json())
            .then(data => {
                for (const key in data) {
                    if (document.getElementById(key)) {
                        document.getElementById(key).value = data[key];
                        document.getElementById(`${key}Value`).innerText = data[key];
                    }
                }
                showConfirmationModal(condition);
            })
            .catch(error => console.error("Error applying preset:", error));
        });
    });

    // Handle condition calculation
    const conditionBtn = document.getElementById("conditionSubmitBtn");
    if (!conditionBtn) return;

    conditionBtn.addEventListener("click", function() {
        const sliderValuesAdjusted = {
            HR: document.getElementById("HR").value,
            UVR: document.getElementById("UVR").value,
            LVR: document.getElementById("LVR").value,
            PVR: document.getElementById("PVR").value,
            S_sa: document.getElementById("S_sa").value,
            Hb: document.getElementById("Hb").value,
            CVO2u: document.getElementById("CVO2u").value,
            CVO2l: document.getElementById("CVO2l").value
        };

        const sliderValuesBaseline = { ...sliderValuesAdjusted };
        let baselineLabel = "Baseline";

        if (Number(sliderValuesAdjusted.PVR) === 27) { 
            sliderValuesBaseline.PVR = 10;
            baselineLabel = "Baseline (PVR=10)";
        }

        Promise.all([
            fetch("/calculate_condition_values", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(sliderValuesAdjusted)
            }).then(res => res.json()),
            fetch("/process", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(sliderValuesBaseline)
            }).then(res => res.json())
        ])
        .then(([adjustedResult, baselineResult]) => {
            const resultsDiv = document.getElementById("conditionResults");
            if (resultsDiv) {
                resultsDiv.innerHTML = `
                <div class="card results-card">
                    <table class="results-table">
                        <thead>
                            <tr>
                                <th>Parameter</th>
                                <th>With Condition</th>
                                <th>${baselineLabel}</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td>Cardiac Output (L/min)</td><td>${adjustedResult.Q_v}</td><td>${baselineResult.Q_v}</td></tr>
                            <tr><td>Blood Flow to Upper Body (L/min)</td><td>${adjustedResult.Q_u}</td><td>${baselineResult.Q_u}</td></tr>
                            <tr><td>Blood Flow to Lower Body (L/min)</td><td>${adjustedResult.Q_l}</td><td>${baselineResult.Q_l}</td></tr>
                            <tr><td>Pulmonary Blood Flow (L/min)</td><td>${adjustedResult.Q_p}</td><td>${baselineResult.Q_p}</td></tr>
                            <tr><td>Systemic Artery Pressure (mmHg)</td><td>${adjustedResult.P_sa}</td><td>${baselineResult.P_sa}</td></tr>
                            <tr><td>Fontan Pressure (mmHg)</td><td>${adjustedResult.P_pa}</td><td>${baselineResult.P_pa}</td></tr>
                            <tr><td>Common Atrium Pressure (mmHg)</td><td>${adjustedResult.P_pv}</td><td>${baselineResult.P_pv}</td></tr>
                            <tr><td>Oxygen Extraction Ratio</td><td>${adjustedResult.OER}</td><td>${baselineResult.OER}</td></tr>
                        </tbody>
                    </table>
                </div>
                `;
                resultsDiv.style.display = "block";
            }
        })
        .catch(error => console.error("Error fetching data:", error));
    });
}

// =============================================
// PLOT PAGE FUNCTIONALITY (/plot_page)
// =============================================

function setupPlotPage() {
    const displayPlotButton = document.getElementById('displayPlotButton');
    const plotTypeSelect = document.getElementById('plotType');
    const plotContainer = document.getElementById('plotContainer');

    if (displayPlotButton && plotTypeSelect && plotContainer) {
        displayPlotButton.addEventListener('click', async () => {
            const selectedPlot = plotTypeSelect.value;
            try {
                const response = await fetch(`/generate_plot?plot_type=${selectedPlot}`);
                const data = await response.json();
                plotContainer.innerHTML = `<img src="data:image/png;base64,${data.plot}" alt="Generated Plot">`;
            } catch (error) {
                plotContainer.innerHTML = `<p style="color: red;">Error displaying plot.</p>`;
            }
        });
    }

    // Custom plot functionality
    const generatePlotButton = document.getElementById('generatePlotButton');
    const customPlotContainer = document.getElementById('customPlotContainer');

    if (generatePlotButton && customPlotContainer) {
        generatePlotButton.addEventListener('click', async () => {
            const input1 = document.getElementById('inputDropdown1').value;
            const input2 = document.getElementById('inputDropdown2').value;
            const output = document.getElementById('outputDropdown').value;

            try {
                const response = await fetch(
                    `/generate_custom_plot?input1=${input1}&input2=${input2}&output=${output}`
                );
                const data = await response.json();
                customPlotContainer.innerHTML = `<img src="data:image/png;base64,${data.plot}" alt="Generated Custom Plot">`;
            } catch (error) {
                customPlotContainer.innerHTML = `<p style="color: red;">Error displaying custom plot.</p>`;
            }
        });
    }
}

// =============================================
// MAIN INITIALIZATION (Runs when page loads)
// =============================================

document.addEventListener('DOMContentLoaded', () => {
    console.log("Initializing page scripts...");
    
    // Setup functionality based on what exists on the page
    setupImageMapModal();  // For index.html
    setupSliderPage();     // For /slider_page
    setupConditionsPage(); // For /conditions_page
    setupPlotPage();       // For /plot_page

    // Initialize image map if it exists
    if (document.getElementById('clickable-image') && typeof imageMapResize === 'function') {
        imageMapResize();
    }
});