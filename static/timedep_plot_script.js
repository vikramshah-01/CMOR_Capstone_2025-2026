document.addEventListener('DOMContentLoaded', () => {
  const displayPlotButton = document.getElementById('displayPlotButton');
  const plotTypeSelect = document.getElementById('plotType');
  const plotContainer = document.getElementById('plotContainer');

  displayPlotButton.addEventListener('click', async () => {
  const selectedPlot = plotTypeSelect.value;

  // read numeric inputs
  const getVal = (id) => document.getElementById(id)?.value;

  const params = new URLSearchParams({
    plot_type: selectedPlot,
    R_s: getVal("R_s"),
    R_p: getVal("R_p"),
    R_BTS: getVal("R_BTS"),
    C_s: getVal("C_s"),
    C_p: getVal("C_p"),
    P_sa_0: getVal("P_sa_0"),
    P_pa_0: getVal("P_pa_0"),
    t_end: getVal("t_end"),
    dt: getVal("dt"),
  });

  try {
    plotContainer.innerHTML = `<p>Loading...</p>`;

    const response = await fetch(`/generate_timedep_plot?${params.toString()}`);

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`HTTP ${response.status}: ${text}`);
    }

    const data = await response.json();
    plotContainer.innerHTML = `<img src="data:image/png;base64,${data.plot}" alt="Generated Plot">`;
  } catch (error) {
    console.error('Error displaying the plot:', error);
    plotContainer.innerHTML = `<p style="color:red;">Error: ${error.message}</p>`;
  }
});

  // optional: generate once on load
  // displayPlotButton.click();
});