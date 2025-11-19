// Dropdown and Display Plot Button Functionality
document.addEventListener('DOMContentLoaded', () => {
    
    // New functionality for generating a plot based on input/output dropdowns
    const generatePlotButton = document.getElementById('generatePlotButton');
    const inputDropdown1 = document.getElementById('inputDropdown1');
    const inputDropdown2 = document.getElementById('inputDropdown2');
    const outputDropdown = document.getElementById('outputDropdown');
    const customPlotContainer = document.getElementById('customPlotContainer');  // Targeting the second plot container

    generatePlotButton.addEventListener('click', async () => {
        const input1 = inputDropdown1.value;
        const input2 = inputDropdown2.value;
        const output = outputDropdown.value;

        try {
            const response = await fetch(`/generate_custom_plot?input1=${input1}&input2=${input2}&output=${output}`);
            if (!response.ok) {
                throw new Error('Failed to fetch the plot');
            }

            const data = await response.json();
            customPlotContainer.innerHTML = `<img src="data:image/png;base64,${data.plot}" alt="Generated Custom Plot">`;
        } catch (error) {
            console.error('Error displaying the plot:', error);
            customPlotContainer.innerHTML = `<p style="color: red;">Error displaying the plot. Check the console for details.</p>`;
        }
    });

});
