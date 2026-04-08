// =============================================
// Shared script.js for:
// 1) Slider page  -> uses /process, has C_sys, no EF
// 2) Conditions page -> uses /calculate_condition_values, has EF, no C_sys
// =============================================

const Conditions = (() => {
  let baselineInputs = null;
  let baselineData = null;
  let selectedDrug = null;
  let singleComparisonChart = null;
  let allDrugComparisonChart = null;

  const drugEffects = {
    nicardipine: {
      label: "Nicardipine",
      RS_pct: -0.3,
      RP_pct: -0.05,
      selectivity: "Poor pulmonary selectivity",
      description:
        "Nicardipine decreases R_s much more than R_p, so it is not strongly pulmonary-selective.",
    },
    milrinone: {
      label: "Milrinone",
      RS_pct: -0.18,
      RP_pct: -0.225,
      selectivity: "Moderate pulmonary selectivity",
      description:
        "Milrinone decreases both R_s and R_p with a somewhat stronger pulmonary effect.",
    },
    sildenafil: {
      label: "Sildenafil",
      RS_pct: -0.1,
      RP_pct: -0.3,
      selectivity: "Good pulmonary selectivity",
      description: "Sildenafil preferentially decreases R_p more than R_s.",
    },
    ino: {
      label: "iNO",
      RS_pct: 0.0,
      RP_pct: -0.45,
      selectivity: "Excellent pulmonary selectivity",
      description:
        "iNO has minimal systemic effect and strongly decreases R_p.",
    },
    epoprostenol: {
      label: "Epoprostenol",
      RS_pct: -0.15,
      RP_pct: -0.4,
      selectivity: "Good pulmonary selectivity",
      description:
        "Epoprostenol decreases both R_s and R_p, with a stronger effect on R_p.",
    },
  };

  const VAR_LABELS = {
    Q_s: "Systemic Flow, Qs",
    Q_p: "Pulmonary Flow, Qp",
    Q_RV: "Right Ventricle Flow, QRV",
    P_a: "Arterial Pressure, Pa",
    P_v: "Venous Pressure, Pv",
    S_m: "Mixed Saturation, Smixed",
    S_sv: "Systemic Venous Saturation, SSV",
    Qp_Qs: "Flow Ratio, Qp/Qs",
    OD2: "Oxygen Delivery",
  };

  const GRAPH_KEYS = ["Q_s", "Q_p", "Q_RV", "P_a", "P_v", "Qp_Qs", "OD2"];

  function el(id) {
    return document.getElementById(id);
  }

  function hasElement(id) {
    return !!document.getElementById(id);
  }

  function hasEF() {
    return hasElement("EF");
  }

  function hasCSys() {
    return hasElement("C_sys");
  }

  function isConditionsPage() {
    return hasEF();
  }

  function isSliderPage() {
    return hasCSys() && !hasEF();
  }

  function getCalculateEndpoint() {
    return isConditionsPage() ? "/calculate_condition_values" : "/process";
  }

  function setField(id, value) {
    const node = el(id);
    if (node && value !== undefined && value !== null) {
      node.value = value;
    }
  }

  function getNumber(id) {
    const node = el(id);
    if (!node) return null;

    const value = Number(node.value);
    return Number.isFinite(value) ? value : null;
  }

  function payloadFromInputs() {
    const payload = {
      HR: getNumber("HR"),
      C_dia: getNumber("C_dia"),
      C_A: getNumber("C_A"),
      C_V: getNumber("C_V"),
      R_s: getNumber("R_s"),
      R_p: getNumber("R_p"),
      V_total: getNumber("V_total"),
      Hb: getNumber("Hb"),
      CVO2: getNumber("CVO2"),
    };

    // Conditions page only
    if (hasEF()) {
      payload.EF = getNumber("EF");
    }

    // Slider page only
    if (hasCSys()) {
      payload.C_sys = getNumber("C_sys");
    }

    for (const key in payload) {
      if (payload[key] === null) {
        throw new Error(`Invalid value for ${key}`);
      }
    }

    return payload;
  }

  function applyInputs(inputPayload) {
    setField("HR", inputPayload.HR);

    if (hasEF()) {
      setField("EF", inputPayload.EF);
    }

    if (hasCSys()) {
      setField("C_sys", inputPayload.C_sys);
    }

    setField("C_dia", inputPayload.C_dia);
    setField("C_A", inputPayload.C_A);
    setField("C_V", inputPayload.C_V);
    setField("R_s", inputPayload.R_s);
    setField("R_p", inputPayload.R_p);
    setField("V_total", inputPayload.V_total);
    setField("Hb", inputPayload.Hb);
    setField("CVO2", inputPayload.CVO2);
  }

  function formatValue(v, key = "") {
    if (v === null || v === undefined) return "—";
    const num = Number(v);
    if (!Number.isFinite(num)) return String(v);

    if (key === "S_m" || key === "S_sv" || key === "Qp_Qs" || key === "EF") {
      return num.toFixed(3);
    }

    if (Math.abs(num) >= 1) return num.toFixed(2);
    if (Math.abs(num) >= 0.01) return num.toFixed(4);
    return num.toExponential(2);
  }

  function formatDelta(curr, base, key = "") {
    if (
      curr === null ||
      curr === undefined ||
      base === null ||
      base === undefined
    ) {
      return "—";
    }

    const c = Number(curr);
    const b = Number(base);
    if (!Number.isFinite(c) || !Number.isFinite(b)) return "—";

    const d = c - b;
    const sign = d >= 0 ? "+" : "";

    if (key === "S_m" || key === "S_sv" || key === "Qp_Qs" || key === "EF") {
      return sign + d.toFixed(3);
    }

    if (Math.abs(d) >= 1) return sign + d.toFixed(2);
    if (Math.abs(d) >= 0.01) return sign + d.toFixed(4);
    return sign + d.toExponential(2);
  }

  function percentChange(curr, base) {
    const c = Number(curr);
    const b = Number(base);

    if (!Number.isFinite(c) || !Number.isFinite(b) || b === 0) {
      return null;
    }

    return ((c - b) / Math.abs(b)) * 100;
  }

  function highlightSelectedButton(condition) {
    document.querySelectorAll(".preset-btn").forEach((btn) => {
      const isSelected = btn.dataset.condition === condition;
      btn.classList.toggle("selected", isSelected);
    });
  }

  function showConfirmationModal(condition) {
    const modal = el("confirmation-modal");
    const modalText = el("modal-text");

    if (!modal || !modalText) return;

    const drug = drugEffects[condition];
    if (!drug) {
      modalText.textContent = "Preset applied successfully.";
    } else {
      modalText.textContent =
        `${drug.label} preset applied. ${drug.description} ` +
        `Selectivity: ${drug.selectivity}.`;
    }

    modal.style.display = "block";
  }

  function setupModalHandlers() {
    const modal = el("confirmation-modal");
    const close = el("modal-close");
    const popupModal = el("popup-modal");
    const popupClose = el("diagram-close");

    if (close && modal) {
      close.addEventListener("click", () => {
        modal.style.display = "none";
      });
    }

    if (popupClose && popupModal) {
      popupClose.addEventListener("click", () => {
        popupModal.style.display = "none";
      });
    }

    window.addEventListener("click", (event) => {
      if (modal && event.target === modal) modal.style.display = "none";
      if (popupModal && event.target === popupModal) {
        popupModal.style.display = "none";
      }
    });
  }

  function setupImageMapModal() {
    const modal = el("popup-modal");
    const modalText = el("diagram-text");

    if (!modal || !modalText) return;

    document.querySelectorAll("area").forEach((area) => {
      area.addEventListener("click", (e) => {
        e.preventDefault();
        modalText.textContent = area.getAttribute("data-content") || "";
        modal.style.display = "block";
      });
    });

    if (typeof imageMapResize === "function") {
      imageMapResize();
    }
  }

  function updateBaselineStatus() {
    const node = el("baselineStatus");
    if (!node) return;

    if (!baselineData) {
      node.textContent = "Baseline not initialized yet.";
      return;
    }

    node.textContent =
      "Baseline initialized from current page values. Baseline is used as the comparison reference.";
  }

  function updateSelectedDrugStatus() {
    const node = el("selectedDrugStatus");
    if (!node) return;

    if (!selectedDrug) {
      node.textContent = "No drug preset currently selected.";
      return;
    }

    const drug = drugEffects[selectedDrug];
    node.textContent =
      `Selected drug: ${drug.label}. ` +
      `ΔR_s = ${(drug.RS_pct * 100).toFixed(1)}%, ` +
      `ΔR_p = ${(drug.RP_pct * 100).toFixed(1)}%.`;
  }

  function toggleResults(show) {
    const conditionResults = el("conditionResults");
    const allDrugResults = el("allDrugResults");
    const hideBtn = el("hideResultsBtn");

    if (conditionResults) {
      conditionResults.style.display = show ? "block" : "none";
    }

    if (allDrugResults && allDrugResults.innerHTML.trim() !== "") {
      allDrugResults.style.display = show ? "block" : "none";
    }

    if (hideBtn) {
      hideBtn.style.display = show ? "inline-block" : "none";
    }
  }

  function destroyCharts() {
    if (singleComparisonChart) {
      singleComparisonChart.destroy();
      singleComparisonChart = null;
    }
    if (allDrugComparisonChart) {
      allDrugComparisonChart.destroy();
      allDrugComparisonChart = null;
    }
  }

  async function calculate(payload) {
    const response = await fetch(getCalculateEndpoint(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const rawText = await response.text();

    let data;
    try {
      data = JSON.parse(rawText);
    } catch (err) {
      throw new Error("Backend did not return valid JSON.");
    }

    if (!response.ok) {
      throw new Error(data.error || "Computation failed.");
    }

    if (
      Number.isFinite(Number(data.Q_p)) &&
      Number.isFinite(Number(data.Q_s)) &&
      Number(data.Q_s) !== 0
    ) {
      data.Qp_Qs = Number(data.Q_p) / Number(data.Q_s);
    } else {
      data.Qp_Qs = null;
    }

    return data;
  }

  function renderSliderResults(result) {
    const resultNode = el("result");
    const sliderResults = el("sliderResults");

    if (!sliderResults) return;

    destroyCharts();

    if (resultNode) {
      resultNode.textContent = "";
    }

    sliderResults.innerHTML = `
      <div class="card" style="padding:16px;">
        <h2 style="margin-top:0;">Results</h2>
        <table style="width:100%; border-collapse:collapse;">
          <tbody>
            <tr>
              <td style="padding:8px; border-bottom:1px solid #eee; font-weight:600;">Systemic Flow (Q_s)</td>
              <td style="padding:8px; border-bottom:1px solid #eee; text-align:right;">${formatValue(result.Q_s, "Q_s")}</td>
            </tr>
            <tr>
              <td style="padding:8px; border-bottom:1px solid #eee; font-weight:600;">Pulmonary Flow (Q_p)</td>
              <td style="padding:8px; border-bottom:1px solid #eee; text-align:right;">${formatValue(result.Q_p, "Q_p")}</td>
            </tr>
            <tr>
              <td style="padding:8px; border-bottom:1px solid #eee; font-weight:600;">Arterial Pressure (P_a)</td>
              <td style="padding:8px; border-bottom:1px solid #eee; text-align:right;">${formatValue(result.P_a, "P_a")}</td>
            </tr>
            <tr>
              <td style="padding:8px; border-bottom:1px solid #eee; font-weight:600;">Venous Pressure (P_v)</td>
              <td style="padding:8px; border-bottom:1px solid #eee; text-align:right;">${formatValue(result.P_v, "P_v")}</td>
            </tr>
            <tr>
              <td style="padding:8px; border-bottom:1px solid #eee; font-weight:600;">Mixed Saturation (S_m)</td>
              <td style="padding:8px; border-bottom:1px solid #eee; text-align:right;">${formatValue(result.S_m, "S_m")}</td>
            </tr>
            <tr>
              <td style="padding:8px; border-bottom:1px solid #eee; font-weight:600;">Systemic Venous Saturation (S_sv)</td>
              <td style="padding:8px; border-bottom:1px solid #eee; text-align:right;">${formatValue(result.S_sv, "S_sv")}</td>
            </tr>
            <tr>
              <td style="padding:8px; font-weight:600;">Oxygen Delivery (OD2)</td>
              <td style="padding:8px; text-align:right;">${formatValue(result.OD2, "OD2")}</td>
            </tr>
          </tbody>
        </table>
      </div>
    `;
  }

  function renderComparison(currentData, currentLabel = "Custom Inputs") {
    const container = el("conditionResults");
    if (!container || !baselineData) return;
    if (typeof Chart === "undefined") return;

    destroyCharts();

    container.innerHTML = `
      <div class="card" style="padding:16px;">
        <div style="display:flex; align-items:flex-end; justify-content:space-between; gap:12px; margin-bottom:12px;">
          <div>
            <h2 style="margin:0;">Results Comparison</h2>
            <div style="margin-top:6px; color:#666; font-size:13px;">
              Baseline: <b>Baseline</b> &nbsp; • &nbsp; Current: <b>${currentLabel}</b>
            </div>
          </div>
        </div>

        <div style="height:420px;">
          <canvas id="singleComparisonCanvas"></canvas>
        </div>

        <div style="margin-top:16px; overflow-x:auto;">
          <table style="width:100%; border-collapse:collapse; min-width:720px;">
            <thead>
              <tr>
                <th style="text-align:left; padding:10px; border-bottom:2px solid #ddd; background:#f4f4f5;">Variable</th>
                <th style="text-align:right; padding:10px; border-bottom:2px solid #ddd; background:#f4f4f5;">Baseline</th>
                <th style="text-align:right; padding:10px; border-bottom:2px solid #ddd; background:#f4f4f5;">${currentLabel}</th>
                <th style="text-align:right; padding:10px; border-bottom:2px solid #ddd; background:#f4f4f5;">Δ</th>
              </tr>
            </thead>
            <tbody>
              ${GRAPH_KEYS.map((key, idx) => {
                const baseVal = baselineData[key];
                const currVal = currentData[key];
                const delta = formatDelta(currVal, baseVal, key);
                const zebra =
                  idx % 2 === 0 ? "background:#fafafa;" : "background:#ffffff;";
                return `
                  <tr style="${zebra}">
                    <td style="padding:8px 10px; border-bottom:1px solid #eee;">
                      <div style="font-weight:600;">${VAR_LABELS[key] || key}</div>
                      <div style="font-size:12px; color:#666; margin-top:2px;">${key}</div>
                    </td>
                    <td style="padding:8px 10px; border-bottom:1px solid #eee; text-align:right;">
                      ${formatValue(baseVal, key)}
                    </td>
                    <td style="padding:8px 10px; border-bottom:1px solid #eee; text-align:right;">
                      ${formatValue(currVal, key)}
                    </td>
                    <td style="padding:8px 10px; border-bottom:1px solid #eee; text-align:right;">
                      ${delta}
                    </td>
                  </tr>
                `;
              }).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;

    const canvas = el("singleComparisonCanvas");
    if (canvas) {
      singleComparisonChart = new Chart(canvas, {
        type: "bar",
        data: {
          labels: GRAPH_KEYS.map((key) => VAR_LABELS[key] || key),
          datasets: [
            {
              label: "% Change from Baseline",
              data: GRAPH_KEYS.map((key) =>
                percentChange(currentData[key], baselineData[key]),
              ),
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "top",
            },
            title: {
              display: true,
              text: `${currentLabel} vs Baseline (% Change)`,
            },
            tooltip: {
              callbacks: {
                label: function (context) {
                  const value = context.raw;
                  if (value === null || value === undefined) return "N/A";
                  return `${value.toFixed(2)}%`;
                },
              },
            },
          },
          scales: {
            x: {
              ticks: {
                maxRotation: 45,
                minRotation: 45,
              },
            },
            y: {
              title: {
                display: true,
                text: "Percent Change (%)",
              },
              ticks: {
                callback: function (value) {
                  return value + "%";
                },
              },
            },
          },
        },
      });
    }

    container.style.display = "block";
  }

  function renderAllDrugComparison(results) {
    const container = el("allDrugResults");
    if (!container || !baselineData) return;
    if (typeof Chart === "undefined") return;

    destroyCharts();

    const rows = results
      .map((item, idx) => {
        const zebra =
          idx % 2 === 0 ? "background:#fafafa;" : "background:#ffffff;";

        return `
          <tr style="${zebra}">
            <td style="padding:8px 10px; border-bottom:1px solid #eee; font-weight:600;">
              ${item.label}
            </td>
            <td style="padding:8px 10px; border-bottom:1px solid #eee; text-align:right;">
              ${(item.RS_pct * 100).toFixed(1)}%
            </td>
            <td style="padding:8px 10px; border-bottom:1px solid #eee; text-align:right;">
              ${(item.RP_pct * 100).toFixed(1)}%
            </td>
            <td style="padding:8px 10px; border-bottom:1px solid #eee; text-align:right;">
              ${formatValue(item.data.Q_s, "Q_s")}
            </td>
            <td style="padding:8px 10px; border-bottom:1px solid #eee; text-align:right;">
              ${formatValue(item.data.Q_p, "Q_p")}
            </td>
            <td style="padding:8px 10px; border-bottom:1px solid #eee; text-align:right;">
              ${formatValue(item.data.Qp_Qs, "Qp_Qs")}
            </td>
            <td style="padding:8px 10px; border-bottom:1px solid #eee; text-align:right;">
              ${formatValue(item.data.P_a, "P_a")}
            </td>
            <td style="padding:8px 10px; border-bottom:1px solid #eee; text-align:right;">
              ${formatValue(item.data.P_v, "P_v")}
            </td>
            <td style="padding:8px 10px; border-bottom:1px solid #eee; text-align:right;">
              ${formatValue(item.data.S_m, "S_m")}
            </td>
            <td style="padding:8px 10px; border-bottom:1px solid #eee; text-align:right;">
              ${formatValue(item.data.S_sv, "S_sv")}
            </td>
          </tr>
        `;
      })
      .join("");

    container.innerHTML = `
      <div class="card" style="padding:16px;">
        <h2 style="margin:0 0 12px 0;">All Drug Comparison Summary</h2>
        <div style="color:#666; font-size:13px; margin-bottom:12px;">
          Graph + table view for all preset drugs relative to baseline.
        </div>

        <div style="height:420px; margin-bottom:18px;">
          <canvas id="allDrugComparisonCanvas"></canvas>
        </div>

        <div style="overflow-x:auto;">
          <table style="width:100%; border-collapse:collapse; min-width:1050px;">
            <thead>
              <tr>
                <th style="text-align:left; padding:10px; border-bottom:2px solid #ddd; background:#f4f4f5;">Drug</th>
                <th style="text-align:right; padding:10px; border-bottom:2px solid #ddd; background:#f4f4f5;">ΔR_s</th>
                <th style="text-align:right; padding:10px; border-bottom:2px solid #ddd; background:#f4f4f5;">ΔR_p</th>
                <th style="text-align:right; padding:10px; border-bottom:2px solid #ddd; background:#f4f4f5;">Q_s</th>
                <th style="text-align:right; padding:10px; border-bottom:2px solid #ddd; background:#f4f4f5;">Q_p</th>
                <th style="text-align:right; padding:10px; border-bottom:2px solid #ddd; background:#f4f4f5;">Qp/Qs</th>
                <th style="text-align:right; padding:10px; border-bottom:2px solid #ddd; background:#f4f4f5;">P_a</th>
                <th style="text-align:right; padding:10px; border-bottom:2px solid #ddd; background:#f4f4f5;">P_v</th>
                <th style="text-align:right; padding:10px; border-bottom:2px solid #ddd; background:#f4f4f5;">S_m</th>
                <th style="text-align:right; padding:10px; border-bottom:2px solid #ddd; background:#f4f4f5;">S_sv</th>
              </tr>
            </thead>
            <tbody>
              ${rows}
            </tbody>
          </table>
        </div>
      </div>
    `;

    const canvas = el("allDrugComparisonCanvas");
    if (canvas) {
      allDrugComparisonChart = new Chart(canvas, {
        type: "bar",
        data: {
          labels: results.map((item) => item.label),
          datasets: [
            {
              label: "Baseline Qp/Qs",
              data: results.map(() => Number(baselineData.Qp_Qs)),
            },
            {
              label: "Drug Qp/Qs",
              data: results.map((item) => Number(item.data.Qp_Qs)),
            },
            {
              label: "Baseline Qs",
              data: results.map(() => Number(baselineData.Q_s)),
            },
            {
              label: "Drug Qs",
              data: results.map((item) => Number(item.data.Q_s)),
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "top",
            },
            title: {
              display: true,
              text: "All Drug Effects Compared With Baseline",
            },
          },
          scales: {
            y: {
              beginAtZero: true,
            },
          },
        },
      });
    }

    container.style.display = "block";
  }

  function applyDrugToInputs(baseInputs, condition) {
    const drug = drugEffects[condition];
    if (!drug) throw new Error(`Unknown drug condition: ${condition}`);

    return {
      ...baseInputs,
      R_s: Number((baseInputs.R_s * (1 + drug.RS_pct)).toFixed(6)),
      R_p: Number((baseInputs.R_p * (1 + drug.RP_pct)).toFixed(6)),
    };
  }

  async function initializeBaseline() {
    baselineInputs = payloadFromInputs();
    baselineData = await calculate(baselineInputs);
    updateBaselineStatus();
    updateSelectedDrugStatus();
    renderComparison(baselineData, "Baseline");
  }

  async function applyCondition(condition) {
    try {
      if (!baselineInputs || !baselineData) {
        alert("Baseline not initialized yet. Refresh the page and try again.");
        return;
      }

      const modifiedInputs = applyDrugToInputs(baselineInputs, condition);
      applyInputs(modifiedInputs);

      selectedDrug = condition;
      highlightSelectedButton(condition);
      updateSelectedDrugStatus();
      showConfirmationModal(condition);

      const result = await calculate(modifiedInputs);
      renderComparison(result, drugEffects[condition].label);

      const allDrugContainer = el("allDrugResults");
      if (allDrugContainer) {
        allDrugContainer.innerHTML = "";
        allDrugContainer.style.display = "none";
      }

      toggleResults(true);
    } catch (error) {
      console.error(error);
      alert(error.message || "Failed to apply condition.");
    }
  }

  async function compareAllDrugs() {
    try {
      if (!baselineInputs || !baselineData) {
        alert("Baseline not initialized yet. Refresh the page and try again.");
        return;
      }

      const entries = Object.entries(drugEffects);
      const results = [];

      for (const [key, drug] of entries) {
        const modifiedInputs = applyDrugToInputs(baselineInputs, key);
        const result = await calculate(modifiedInputs);

        results.push({
          key,
          label: drug.label,
          RS_pct: drug.RS_pct,
          RP_pct: drug.RP_pct,
          data: result,
        });
      }

      renderAllDrugComparison(results);
      toggleResults(true);
    } catch (error) {
      console.error(error);
      alert(error.message || "Failed to compare all drugs.");
    }
  }

  function resetToBaseline() {
    if (!baselineInputs) return;

    applyInputs(baselineInputs);
    selectedDrug = null;
    updateSelectedDrugStatus();

    document.querySelectorAll(".preset-btn").forEach((btn) => {
      btn.classList.remove("selected");
    });

    const allDrugContainer = el("allDrugResults");
    if (allDrugContainer) {
      allDrugContainer.innerHTML = "";
      allDrugContainer.style.display = "none";
    }

    if (baselineData) {
      renderComparison(baselineData, "Baseline");
      toggleResults(true);
    }
  }

  function bindButtons() {
    document
      .querySelectorAll(".preset-btn[data-condition]")
      .forEach((button) => {
        button.addEventListener("click", () => {
          const condition = button.dataset.condition;
          applyCondition(condition);
        });
      });

    const compareAllBtn = el("compareAllBtn");
    if (compareAllBtn) {
      compareAllBtn.addEventListener("click", compareAllDrugs);
    }

    const resetBaselineBtn = el("resetBaselineBtn");
    if (resetBaselineBtn) {
      resetBaselineBtn.addEventListener("click", resetToBaseline);
    }
  }

  async function onSubmit(event) {
    event.preventDefault();

    try {
      const payload = payloadFromInputs();
      const result = await calculate(payload);

      if (isConditionsPage()) {
        renderComparison(
          result,
          selectedDrug
            ? `${drugEffects[selectedDrug].label} (Edited)`
            : "Custom Inputs",
        );

        const allDrugContainer = el("allDrugResults");
        if (allDrugContainer) {
          allDrugContainer.innerHTML = "";
          allDrugContainer.style.display = "none";
        }

        toggleResults(true);
      } else {
        renderSliderResults(result);
      }
    } catch (error) {
      console.error(error);
      alert(error.message || "Submit failed.");
    }
  }

  function init() {
    setupModalHandlers();
    setupImageMapModal();

    const form = el("parameterForm");
    if (form) {
      form.addEventListener("submit", onSubmit);
    }

    if (isConditionsPage()) {
      bindButtons();

      initializeBaseline().catch((error) => {
        console.error(error);
        alert(`Failed to initialize baseline: ${error.message}`);
      });
    } else if (isSliderPage()) {
      console.log("Slider page detected.");
    } else {
      console.log("Unknown page type detected.");
    }
  }

  return {
    init,
    applyCondition,
    toggleResults,
  };
})();

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("parameterForm");
  if (!form) {
    console.log("No parameter form found; skipping init.");
    return;
  }

  window.Conditions = Conditions;
  Conditions.init();
});
