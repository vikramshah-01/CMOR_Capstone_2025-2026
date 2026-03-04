document.addEventListener('DOMContentLoaded', () => {
  const displayPlotButton = document.getElementById('displayPlotButton');
  const plotTypeSelect = document.getElementById('plotType');
  const plotContainer = document.getElementById('plotContainer');

  displayPlotButton.addEventListener('click', async () => {
    const selectedPlot = plotTypeSelect.value; // flows | pressures | aortic

    try {
      plotContainer.innerHTML = `<p>Loading...</p>`;

      // NOTE: calls your time-dependent endpoint
      const response = await fetch(`/generate_timedep_plot?plot_type=${encodeURIComponent(selectedPlot)}`);

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`HTTP ${response.status}: ${text}`);
      }

      const data = await response.json();
      plotContainer.innerHTML = `<img src="data:image/png;base64,${data.plot}" alt="Generated Plot">`;
    } catch (error) {
      console.error('Error displaying the plot:', error);
      plotContainer.innerHTML = `<p style="color:red;">Error displaying the plot. Check console.</p>`;
    }
  });

  // optional: generate once on load
  // displayPlotButton.click();
});