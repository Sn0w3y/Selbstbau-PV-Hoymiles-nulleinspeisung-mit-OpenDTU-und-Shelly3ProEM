document.addEventListener('DOMContentLoaded', function() {
    function updateFlowDiagram() {
        fetch('/data')
            .then(response => response.json())
            .then(data => {
                document.getElementById('name').textContent = data.dtu.name;
                document.getElementById('dtuProducing').textContent = data.dtu.producing === 1 ? "Produzieren" : "Standby";
                document.getElementById('dtuPowerDC').textContent = `${Math.abs(data.dtu.power_dc) < 2 ? 0 : Math.abs(data.dtu.power_dc).toFixed(2)} W`;
                document.getElementById('dtuPowerAC').textContent = `${Math.abs(data.dtu.power).toFixed(2)} W`;
                let shellyStatus = data.shelly.total_act_power < 0 ? "Einspeisung" : "Bezug";
                document.getElementById('shellyPower').textContent = `${shellyStatus}: ${Math.abs(data.shelly.total_act_power).toFixed(2)} W`;
                document.getElementById('currentLimit').textContent = data.current_limit !== 'N/A' ? `${data.current_limit} W` : 'N/A';
                let totalConsumption = Math.abs(data.dtu.power) + Math.abs(data.shelly.total_act_power);
                document.getElementById('totalConsumption').textContent = `${totalConsumption.toFixed(2)} W`;
                document.getElementById('shellyTypeHeader').textContent = data.shelly.type;
                updateAutoModeButton(data.auto_mode);
                updateGridArrow(data.shelly.total_act_power);
            });
    }

    function updateAutoModeButton(auto_mode) {
        const autoModeButton = document.getElementById('autoModeButton');
        const manualLimitButton = document.getElementById('setManualLimitButton');
        if (auto_mode) {
            autoModeButton.textContent = 'AUTO-Modus stoppen';
            autoModeButton.classList.remove('btn-success');
            autoModeButton.classList.add('btn-danger');
            manualLimitButton.disabled = true;
            manualLimitButton.classList.add('disabled');
        } else {
            autoModeButton.textContent = 'AUTO-Modus starten';
            autoModeButton.classList.remove('btn-danger');
            autoModeButton.classList.add('btn-success');
            manualLimitButton.disabled = false;
            manualLimitButton.classList.remove('disabled');
        }
    }

    function updateGridArrow(power) {
        const gridArrow = document.getElementById('gridArrow');
        if (power < 0) {
            gridArrow.classList.remove('to-shelly');
            gridArrow.classList.add('from-shelly');
        } else {
            gridArrow.classList.remove('from-shelly');
            gridArrow.classList.add('to-shelly');
        }
    }

    function toggleAutoMode() {
        const button = document.getElementById('autoModeButton');
        const isAutoMode = button.textContent === 'AUTO-Modus stoppen';
        fetch(isAutoMode ? '/stop_auto' : '/start_auto', { method: 'POST' })
            .then(() => {
                setTimeout(updateFlowDiagram, 1000);
            });
    }

    function setManualLimit() {
        const manualLimit = document.querySelector('input[name="manual_limit"]').value;
        fetch('/set_manual_limit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ limit: parseInt(manualLimit) })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                toastr.success('Manuelles Limit erfolgreich gesetzt.');
                updateFlowDiagram();
            } else {
                if (data.reason.includes('Auto mode is enabled')) {
                    toastr.error('Manuelles Limit kann nicht gesetzt werden, da der AUTO-Modus aktiviert ist.');
                } else if (data.reason.includes('unreachable')) {
                    toastr.error('Manuelles Limit kann nicht gesetzt werden, da der Wechselrichter nicht erreichbar ist.');
                } else {
                    toastr.error('Manuelles Limit konnte nicht gesetzt werden.');
                }
            }
        })
        .catch(error => {
            toastr.error('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');
        });
    }

    setInterval(updateFlowDiagram, 1000);
    updateFlowDiagram();

    window.toggleAutoMode = toggleAutoMode;
    window.setManualLimit = setManualLimit;
});
