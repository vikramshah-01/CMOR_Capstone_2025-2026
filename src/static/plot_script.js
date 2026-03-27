


// Dropdown and Display Plot Button Functionality
document.addEventListener('DOMContentLoaded', () => {
    const displayPlotButton = document.getElementById('displayPlotButton');
    const plotTypeSelect = document.getElementById('plotType');
    const plotContainer = document.getElementById('plotContainer');

    displayPlotButton.addEventListener('click', async () => {
        const selectedPlot = plotTypeSelect.value;

        try {
            const response = await fetch(`/generate_plot?plot_type=${selectedPlot}`);
            if (!response.ok) {
                throw new Error('Failed to fetch the plot');
            }

            const data = await response.json();
            plotContainer.innerHTML = `<img src="data:image/png;base64,${data.plot}" alt="Generated Plot">`;
        } catch (error) {
            console.error('Error displaying the plot:', error);
            plotContainer.innerHTML = `<p style="color: red;">Error displaying the plot. Check the console for details.</p>`;
        }
    });

});
