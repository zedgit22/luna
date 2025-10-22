document.addEventListener('DOMContentLoaded', () => {
    const runButton = document.getElementById('runButton');
    const helpButton = document.getElementById('helpButton'); // NEW
    const gloveMassInput = document.getElementById('gloveMass');
    const nitrileMassInput = document.getElementById('nitrileMass');
    const regolithMassInput = document.getElementById('regolithMass');
    const regolithIronInput = document.getElementById('regolithIron');
    const waterAvailableInput = document.getElementById('waterAvailable');
    const oxygenAvailableInput = document.getElementById('oxygenAvailable');
    const catalystEfficiencyInput = document.getElementById('catalystEfficiency');
    const carryingCapacityInput = document.getElementById('carryingCapacity');
    const simulationDurationInput = document.getElementById('simulationDuration');
    const loadingSpinner = document.getElementById('loadingSpinner');

    let resultsChart;

    const API_URL = `${window.location.origin}/run_simulation`; // API endpoint (same-origin by default)

    // LHS-1 lunar highlands simulant iron composition (Fe-bearing) percentage
    // Source: UCF LHS-1 specification. If exact fraction differs, update this constant.
    const LHS1_FE_PERCENT = 5.0;

    function createOrUpdateChart(data) {
        const canvas = document.getElementById('resultsChart');
        if (!canvas) { console.error('resultsChart canvas not found'); return; }
        const ctx = canvas.getContext('2d');
        if (resultsChart) {
            resultsChart.destroy();
        }

        resultsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.time_points,
                datasets: [
                    {
                        label: 'Plant Biomass (g)',
                        data: data.biomass_history,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        yAxisID: 'y-mass',
                    },
                    {
                        label: 'Nitrile Mass (g)',
                        data: data.nitrile_history,
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        yAxisID: 'y-mass',
                        borderDash: [5, 5],
                    },
                    {
                        label: 'Nitrogen (ppm)',
                        data: data.nitrogen_history,
                        borderColor: 'rgba(54, 162, 235, 1)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        yAxisID: 'y-ppm',
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: { display: true, text: 'Time (minutes)' }
                    },
                    'y-mass': {
                        type: 'linear',
                        position: 'left',
                        title: { display: true, text: 'Mass (g)' }
                    },
                    'y-ppm': {
                        type: 'linear',
                        position: 'right',
                        title: { display: true, text: 'Nitrogen (ppm)' },
                        grid: {
                            drawOnChartArea: false, // only draw grid for first Y axis
                        },
                    }
                }
            }
        });
    }

    function updateDerivedFields() {
        // 100% of gloves mass is nitrile mass (material of the waste)
        const glove = parseFloat(gloveMassInput?.value);
        const safeGlove = Number.isFinite(glove) ? glove : 0;
        if (nitrileMassInput) {
            nitrileMassInput.value = String(safeGlove);
        }
        // Regolith iron auto-set from LHS-1 spec
        if (regolithIronInput) {
            regolithIronInput.value = String(LHS1_FE_PERCENT);
        }
    }

    async function runSimulation() {
        loadingSpinner.style.display = 'block';
        if (runButton) runButton.disabled = true;

        try {
            updateDerivedFields();

            const nitrile = parseFloat(nitrileMassInput.value);
            const iron = parseFloat(regolithIronInput.value);
            const water = parseFloat(waterAvailableInput.value);
            const oxygen = parseFloat(oxygenAvailableInput.value);
            const eff = parseFloat(catalystEfficiencyInput.value);
            const K = parseFloat(carryingCapacityInput.value);
            const duration = parseFloat(simulationDurationInput.value);

            if ([nitrile, iron, water, oxygen, eff, K, duration].some(v => !Number.isFinite(v))) {
                throw new Error('Invalid input: please provide valid numbers for all parameters.');
            }

            const params = {
                initial_nitrile_mass_g: nitrile,
                regolith_iron_percent: iron,
                catalyst_efficiency_factor: eff,
                water_available_g: water,
                oxygen_available_ppm: oxygen,
                carrying_capacity_K: K,
                simulation_duration_h: duration,
            };

            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            createOrUpdateChart(data);

        } catch (error) {
            console.error("Error running simulation:", error);
            alert("Failed to run simulation. Check the console for details and make sure the backend server is running.");
        } finally {
            loadingSpinner.style.display = 'none';
            if (runButton) runButton.disabled = false;
        }
    }

    if (runButton) {
        runButton.addEventListener('click', runSimulation);
    }

    // NEW: Help button opens the help page in a new tab
    if (helpButton) {
        helpButton.addEventListener('click', (e) => {
            e.preventDefault();
            window.open('help.html', '_blank', 'noopener');
        });
    }

    // Keep derived fields in sync when user edits base inputs
    if (gloveMassInput) {
        gloveMassInput.addEventListener('input', updateDerivedFields);
        gloveMassInput.addEventListener('change', updateDerivedFields);
    }

    // Initialize derived fields and run a default simulation on page load
    updateDerivedFields();
    runSimulation();
});