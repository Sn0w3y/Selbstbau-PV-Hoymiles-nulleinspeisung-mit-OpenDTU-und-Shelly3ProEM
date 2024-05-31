document.addEventListener('DOMContentLoaded', function() {
    const invertersContainer = document.getElementById('invertersContainer');
    const shellyContainer = document.getElementById('shellyContainer');
    const autoModeButton = document.getElementById('autoModeButton');
    const inverterSelect = document.getElementById('inverterSelect');
    const manualButton = document.getElementById('setManualLimitButton'); // Ensure this ID is correct

    function createInverterBox(inverter, index) {
        return `
            <div class="box" id="inverterBox${index}">
                <h2>Inverter ${index + 1}</h2>
                <p>Name: ${inverter.name}</p>
                <p>Status: ${inverter.producing === 1 ? "Produzieren" : "Standby"}</p>
                <p>Leistung DC: ${Math.abs(inverter.power_dc) < 2 ? 0 : Math.abs(inverter.power_dc).toFixed(2)} W</p>
                <p>Leistung AC: ${Math.abs(inverter.power).toFixed(2)} W</p>
                <p>Limit: ${inverter.altes_limit} W</p>
            </div>
        `;
    }

    function renderInverters(config) {
        if (config.inverters && config.inverters.length > 0) {
            invertersContainer.innerHTML = config.inverters.map((inverter, index) => createInverterBox(inverter, index)).join('');
        } else {
            invertersContainer.innerHTML = '<p>No inverters configured.</p>';
        }
    }

    function updateFlowDiagram() {
        fetch('/data')
            .then(response => response.json())
            .then(data => {
                console.log(data); // Log the data structure
                if (data.inverters && data.inverters.length > 0) {
                    invertersContainer.innerHTML = data.inverters.map((inverter, index) => createInverterBox(inverter, index)).join('');
                } else {
                    invertersContainer.innerHTML = '<p>No inverters configured.</p>';
                }

                const totalACPower = data.inverters.reduce((sum, inverter) => sum + inverter.power, 0);
                const verbrauch = totalACPower + data.shelly.total_act_power;

                if (data.shelly) {
                    shellyContainer.innerHTML = `
                        <div class="box" id="shellyBox">
                            <h2>Shelly (${data.shelly.type})</h2>
                            <p>${data.shelly.total_act_power < 0 ? "Einspeisung" : "Bezug"}: ${Math.abs(data.shelly.total_act_power).toFixed(2)} W</p>
                            <p>Verbrauch: ${verbrauch.toFixed(2)} W</p>
                        </div>
                    `;
                }

                // Update auto mode button state
                autoModeButton.textContent = data.auto_mode ? 'AUTO-Modus stoppen' : 'AUTO-Modus starten';
                autoModeButton.classList.toggle('btn-success', !data.auto_mode);
                autoModeButton.classList.toggle('btn-danger', data.auto_mode);

                // Show/hide manual button and dropdown based on auto mode state
                if (data.auto_mode) {
                    manualButton.style.display = 'none';
                    inverterSelect.style.display = 'none';
                } else {
                    manualButton.style.display = 'inline-block';
                    inverterSelect.style.display = 'inline-block';

                    // Update reachable inverters dropdown
                    fetch('/reachable_inverters')
                        .then(response => response.json())
                        .then(reachableInverters => {
                            console.log(reachableInverters); // Log reachable inverters data
                            inverterSelect.innerHTML = reachableInverters.map(inverter =>
                                `<option value="${inverter.serial}">${inverter.name} (${inverter.serial})</option>`
                            ).join('');
                        });
                }
            })
            .catch(error => {
                console.error('Error fetching data:', error);
                invertersContainer.innerHTML = '<p>Fehler beim Laden der Daten.</p>';
            });
    }

    function toggleAutoMode() {
        const isAutoMode = autoModeButton.textContent === 'AUTO-Modus stoppen';
        fetch(isAutoMode ? '/stop_auto' : '/start_auto', { method: 'POST' })
            .then(() => {
                setTimeout(updateFlowDiagram, 1000);
            });
    }

    function setManualLimit() {
        const manualLimit = prompt('Manuelles Limit setzen:');
        const selectedInverter = inverterSelect.value;
        fetch('/set_manual_limit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ serial: selectedInverter, limit: parseInt(manualLimit) })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                toastr.success('Manuelles Limit erfolgreich gesetzt.');
                updateFlowDiagram();
            } else {
                toastr.error('Fehler beim Setzen des manuellen Limits.');
            }
        })
        .catch(error => {
            toastr.error('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');
        });
    }

    renderInverters(config);
    setInterval(updateFlowDiagram, 3000);
    updateFlowDiagram();

    window.toggleAutoMode = toggleAutoMode;
    window.setManualLimit = setManualLimit;
});
