document.addEventListener('DOMContentLoaded', function() {
    const configForm = document.getElementById('configForm');
    const steps = document.querySelectorAll('.step');
    const prevStepButton = document.getElementById('prevStep');
    const nextStepButton = document.getElementById('nextStep');
    const submitButton = document.getElementById('submitConfig');
    const fetchInvertersButton = document.getElementById('fetchInvertersButton');
    const addInverterButton = document.getElementById('addInverterButton');
    const additionalInverters = document.getElementById('additionalInverters');
    const dtuIpInput = document.getElementById('dtu_ip');
    const dtuUserInput = document.getElementById('dtu_nutzer');
    const dtuPasswordInput = document.getElementById('dtu_passwort');
    let inverterCount = 0;
    let currentStep = 0;

    function showStep(step) {
        steps.forEach((s, index) => {
            s.classList.toggle('active', index === step);
        });
        prevStepButton.style.display = step > 0 ? 'inline-block' : 'none';
        nextStepButton.style.display = step < steps.length - 1 ? 'inline-block' : 'none';
        submitButton.style.display = step === steps.length - 1 ? 'inline-block' : 'none';
    }

    fetchInvertersButton.addEventListener('click', () => {
        const dtuIp = dtuIpInput.value;
        const dtuUser = dtuUserInput.value;
        const dtuPassword = dtuPasswordInput.value;

        if (!dtuIp || !dtuUser || !dtuPassword) {
            alert('Please enter the DTU IP, user, and password first.');
            return;
        }

        fetch('/api/livedata/status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ dtu_ip: dtuIp, dtu_user: dtuUser, dtu_password: dtuPassword }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error fetching data: ' + data.error);
                return;
            }

            data.inverters.forEach((inverter, index) => {
                inverterCount++;
                const newInverter = document.createElement('fieldset');
                newInverter.innerHTML = `
                    <legend>Inverter ${index + 1}</legend>
                    <div class="config-form">
                        <div class="form-group">
                            <label for="serial${inverterCount}" class="form-label">Seriennummer:</label>
                            <input type="text" id="serial${inverterCount}" class="form-control" value="${inverter.serial}" required>
                        </div>
                        <div class="form-group">
                            <label for="maximum_wr${inverterCount}" class="form-label">Maximale WR-Leistung:</label>
                            <input type="number" id="maximum_wr${inverterCount}" class="form-control" required>
                        </div>
                        <div class="form-group">
                            <label for="minimum_wr${inverterCount}" class="form-label">Minimale WR-Leistung:</label>
                            <input type="number" id="minimum_wr${inverterCount}" class="form-control" required>
                        </div>
                        <div class="form-group">
                            <label for="dtu_ip${inverterCount}" class="form-label">DTU IP:</label>
                            <input type="text" id="dtu_ip${inverterCount}" class="form-control" value="${dtuIp}" readonly>
                        </div>
                        <div class="form-group">
                            <label for="dtu_nutzer${inverterCount}" class="form-label">DTU Benutzer:</label>
                            <input type="text" id="dtu_nutzer${inverterCount}" class="form-control" value="${dtuUser}" readonly>
                        </div>
                        <div class="form-group">
                            <label for="dtu_passwort${inverterCount}" class="form-label">DTU Passwort:</label>
                            <input type="password" id="dtu_passwort${inverterCount}" class="form-control" value="${dtuPassword}" readonly>
                        </div>
                    </div>
                `;
                additionalInverters.appendChild(newInverter);
            });

            currentStep++;
            showStep(currentStep);
        })
        .catch(error => {
            alert('Error: ' + error.message);
        });
    });

    addInverterButton.addEventListener('click', () => {
        inverterCount++;
        const newInverter = document.createElement('fieldset');
        newInverter.innerHTML = `
            <legend>Inverter ${inverterCount}</legend>
            <div class="config-form">
                <div class="form-group">
                    <label for="serial${inverterCount}" class="form-label">Seriennummer:</label>
                    <input type="text" id="serial${inverterCount}" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="maximum_wr${inverterCount}" class="form-label">Maximale WR-Leistung:</label>
                    <input type="number" id="maximum_wr${inverterCount}" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="minimum_wr${inverterCount}" class="form-label">Minimale WR-Leistung:</label>
                    <input type="number" id="minimum_wr${inverterCount}" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="dtu_ip${inverterCount}" class="form-label">DTU IP:</label>
                    <input type="text" id="dtu_ip${inverterCount}" class="form-control" value="${dtuIpInput.value}" readonly>
                </div>
                <div class="form-group">
                    <label for="dtu_nutzer${inverterCount}" class="form-label">DTU Benutzer:</label>
                    <input type="text" id="dtu_nutzer${inverterCount}" class="form-control" value="${dtuUserInput.value}" readonly>
                </div>
                <div class="form-group">
                    <label for="dtu_passwort${inverterCount}" class="form-label">DTU Passwort:</label>
                    <input type="password" id="dtu_passwort${inverterCount}" class="form-control" value="${dtuPasswordInput.value}" readonly>
                </div>
            </div>
        `;
        additionalInverters.appendChild(newInverter);
    });

    nextStepButton.addEventListener('click', () => {
        if (currentStep < steps.length - 1) {
            currentStep++;
            showStep(currentStep);
        }
    });

    prevStepButton.addEventListener('click', () => {
        if (currentStep > 0) {
            currentStep--;
            showStep(currentStep);
        }
    });

    configForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const inverters = [];
        for (let i = 1; i <= inverterCount; i++) {
            const inverter = {
                serial: document.getElementById(`serial${i}`).value,
                maximum_wr: document.getElementById(`maximum_wr${i}`).value,
                minimum_wr: document.getElementById(`minimum_wr${i}`).value,
                dtu_ip: document.getElementById(`dtu_ip${i}`).value,
                dtu_nutzer: document.getElementById(`dtu_nutzer${i}`).value,
                dtu_passwort: document.getElementById(`dtu_passwort${i}`).value,
            };
            inverters.push(inverter);
        }
        const shelly_ip = document.getElementById('shelly_ip').value;
        const auto_mode = document.getElementById('auto_mode').checked;
        const config = { inverters, shelly_ip, auto_mode };

        fetch('/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config),
        }).then(response => {
            if (response.ok) {
                window.location.href = '/';
            } else {
                alert('Fehler beim Speichern der Konfiguration');
            }
        });
    });

    showStep(currentStep);
});
