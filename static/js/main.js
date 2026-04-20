
// ============================================================
// TOAST NOTIFICATION SYSTEM
// ============================================================
window.showToast = function(title, message, type = 'info', duration = 5000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const colors = {
        'success': { bg: 'rgba(16,185,129,0.15)', border: '#10b981', icon: '✅' },
        'warning': { bg: 'rgba(234,179,8,0.15)',  border: '#eab308', icon: '⚠️' },
        'error':   { bg: 'rgba(239,68,68,0.15)',  border: '#ef4444', icon: '🚨' },
        'info':    { bg: 'rgba(99,102,241,0.15)', border: '#6366f1', icon: 'ℹ️'  }
    };

    const c = colors[type] || colors['info'];

    const toast = document.createElement('div');
    toast.style.cssText = `
        position: relative;
        background: ${c.bg};
        border: 1px solid ${c.border};
        border-left: 4px solid ${c.border};
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        max-width: 380px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        animation: toastSlideIn 0.3s ease;
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    `;

    toast.innerHTML = `
        <div style="display:flex; align-items:flex-start; gap:10px;">
            <span style="font-size:1.2em;">${c.icon}</span>
            <div style="flex:1;">
                <strong style="display:block; margin-bottom:2px; font-size:0.95em;">${title}</strong>
                <span style="font-size:0.85em; color:#cbd5e1; white-space:pre-line;">${message}</span>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" style="background:none; border:none; color:#94a3b8; cursor:pointer; font-size:1.1em; padding:0; line-height:1;">✕</button>
        </div>
    `;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.4s ease';
        setTimeout(() => toast.remove(), 400);
    }, duration);
};

// Inject toast animation CSS
(function() {
    const style = document.createElement('style');
    style.textContent = `
        #toast-container {
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 9999;
            display: flex;
            flex-direction: column-reverse;
        }
        @keyframes toastSlideIn {
            from { opacity: 0; transform: translateX(60px); }
            to   { opacity: 1; transform: translateX(0); }
        }
    `;
    document.head.appendChild(style);
})();

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const tabs = document.querySelectorAll('.nav-links li');
    const sections = document.querySelectorAll('.view-section');
    const form = document.getElementById('stabilityForm');

    // Inputs
    const studyIdInput = document.getElementById('studyIdInput');
    const timeInput = document.getElementById('timeInput');
    const potencyInput = document.getElementById('potencyInput');
    const impurityInput = document.getElementById('impurityInput');


    const studySelect = document.getElementById('studySelect');
    const ootCount = document.getElementById('oot-count');
    const alertList = document.getElementById('recent-alerts');

    // Charts
    const charts = { main: null, prediction: null };

    // Initial Load
    initialize();

    async function initialize() {
        // Set visible loading status
        const sysStatus = document.querySelector('.system-status');
        if (sysStatus) sysStatus.innerHTML = '<span class="status-dot" style="background:orange; box-shadow:none;"></span> Loading Data...';

        try {
            console.log("Fetching studies...");
            const resp = await fetch('/api/studies');
            if (!resp.ok) throw new Error(`API Error: ${resp.status}`);

            const studies = await resp.json();
            console.log("Studies loaded:", studies);

            if (studySelect) {
                studySelect.innerHTML = studies.map(id => `<option value="${id}">${id}</option>`).join('');

                if (studies.length > 0) {
                    studyIdInput.value = studies[0];
                    await loadDashboardData(studies[0]);

                    // Success!
                    if (sysStatus) sysStatus.innerHTML = '<span class="status-dot"></span> System Operational';
                } else {
                    if (sysStatus) sysStatus.innerHTML = '<span class="status-dot" style="background:red;"></span> No Data Found';
                    window.showToast("No Data", "No stability studies found in database.", "warning");
                }
            }
        } catch (e) {
            console.error("Failed to load studies", e);
            if (sysStatus) sysStatus.innerHTML = '<span class="status-dot" style="background:red;"></span> Connection Failed';
            window.showToast("Connection Error", "Failed to connect to backend API. Please ensure app.py is running. Error: " + e.message, "error");
        }
    }

    // Tab Switching
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const target = tab.dataset.tab;
            sections.forEach(section => {
                section.classList.remove('active');
                if (section.id === target) section.classList.add('active');
            });

            // Update Header Title
            const headerTitle = document.querySelector('#pageTitle');
            const currentStudy = studySelect ? studySelect.value : null;
            if (headerTitle) {
                if (target === 'data-evaluation') {
                    headerTitle.innerText = 'Data Evaluation Overview';
                    if (currentStudy) loadDashboardData(currentStudy);
                }
                if (target === 'stability') {
                    headerTitle.innerText = 'Stability Analytics';
                    if (currentStudy) updateShelfLife(currentStudy);
                }
                if (target === 'new-study') {
                    headerTitle.innerText = 'New Study Entry';
                }
            }
        });
    });

    // Handle Window Resize for Charts
    window.addEventListener('resize', () => {
        if (charts.main) charts.main.resize();
        if (charts.prediction) charts.prediction.resize();
    });

    // Study Selection Change
    if (studySelect) {
        studySelect.addEventListener('change', (e) => {
            const selectedStudy = e.target.value;
            studyIdInput.value = selectedStudy;
            loadDashboardData(selectedStudy);
        });
    }

    // Form Submission (Real-Time Entry)
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const payload = {
                study_id: studyIdInput.value,
                time: timeInput.value,
                potency: potencyInput.value,
                impurities: impurityInput.value
                // Add logic for packaging/temp if inputs exist
            };

            try {
                const response = await fetch('/api/data', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const result = await response.json();

                if (result.error) {
                    window.showToast("Error", result.error, "error");
                } else {
                    handleSubmissionResult(result);
                    // Refresh Dashboard immediately
                    loadDashboardData(studySelect.value);

                    // Clear inputs except Study ID
                    timeInput.value = '';
                    potencyInput.value = '';
                    impurityInput.value = '';

                }

            } catch (error) {
                console.error('Error submitting data:', error);
                window.showToast("Submission Failed", "Failed to submit data. See console.", "error");
            }
        });
    }

    function handleSubmissionResult(result) {
        const resultBox = document.getElementById('analysisResult');
        if (!resultBox) return;

        resultBox.classList.remove('hidden');
        const oot = result.report || {};
        const prediction = result.next_prediction || {};

        let html = '';

        // 1. OOT Alert Section
        if (oot.is_oot) {
            // PLAY ALERT SOUND
            playAlertSound();

            let alertContent = '';

            // Handle Potency OOT
            if (oot.potency_info && oot.potency_info.severity !== 'Normal') {
                alertContent += `<p><strong>Potency OOT:</strong> Actual: <strong>${oot.potency_info.actual}%</strong> (Exp: ${oot.potency_info.expected}%)</p>`;
            }
            // Handle Impurity OOT
            if (oot.impurity_info && oot.impurity_info.severity !== 'Normal') {
                alertContent += `<p><strong>Impurity OOT:</strong> Actual: <strong>${oot.impurity_info.actual}%</strong> (Exp: ${oot.impurity_info.expected}%)</p>`;
            }

            // Fallback for general anomaly
            if (!alertContent) {
                if (oot.ml_anomaly) {
                    alertContent = `<p><strong>ML Algorithm Anomaly:</strong> Unusual degradation pattern identified.</p>`;
                } else if (oot.actual_potency) {
                    alertContent = `<p>Potency Deviation: <strong>${oot.actual_potency}%</strong> (Exp: ${oot.expected_potency}%)</p>`;
                } else {
                    alertContent = `<p>Significant deviation detected.</p>`;
                }
            }

            html += `
                <div class="alert oot-alert" style="background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                    <h3 style="color: #ef4444; margin: 0 0 10px 0;">⚠️ OOT Alert Detected!</h3>
                    ${alertContent}
                </div>`;

            // Find correct values for the alert log
            let alertActual = oot.potency_info ? oot.potency_info.actual : (oot.actual_potency || 'N/A');
            let alertExpected = oot.potency_info ? oot.potency_info.expected : (oot.expected_potency || 'N/A');

            // If the OOT was actually on impurity, we might want to log that instead
            if (oot.impurity_info && oot.impurity_info.severity !== 'Normal' && (!oot.potency_info || oot.potency_info.severity === 'Normal')) {
                addAlert(`Month ${timeInput.value}: Impurity OOT! Actual ${oot.impurity_info.actual}% (Limit: ${oot.impurity_info.expected}%)`);
            } else {
                addAlert(`Month ${timeInput.value}: OOT Detected! Potency ${alertActual}% (Exp: ${alertExpected}%)`);
            }
        } else {
            html += `
                <div class="alert success" style="background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; padding: 15px; border-radius: 12px; margin-bottom: 20px;">
                    <h3 style="color: #10b981; margin: 0 0 5px 0;">✅ Data Within Trend</h3>
                    <p>Potency is consistent with prediction. No OOT detected.</p>
                </div>`;
        }

        // 2. Next Prediction Section
        if (prediction.month) {
            html += `
                <div class="next-prediction" style="background: rgba(99, 102, 241, 0.15); border: 1px solid #6366f1; padding: 20px; border-radius: 12px;">
                    <h3 style="color: #cbd5e1; margin: 0 0 10px 0;">🔮 Automated Forecast Updated</h3>
                    <p>Based on this new data, the system predicts for <strong>Month ${prediction.month}</strong>:</p>
                    <div style="display: flex; gap: 20px; margin-top: 10px;">
                        <div>
                            <span style="display:block; font-size: 0.8em; color: #94a3b8;">Potency</span>
                            <span style="font-size: 1.2em; font-weight: bold; color: #fff;">${prediction.potency}%</span>
                        </div>
                        <div>
                            <span style="display:block; font-size: 0.8em; color: #94a3b8;">Impurities</span>
                            <span style="font-size: 1.2em; font-weight: bold; color: #fff;">${prediction.impurity}%</span>
                        </div>
                    </div>
                </div>
            `;
        }

        resultBox.innerHTML = html;
    }

    function addAlert(message, customColor = '#f87171') {
        if (!alertList) return;

        const li = document.createElement('li');
        li.style.padding = '12px';
        li.style.borderBottom = '1px solid rgba(255,255,255,0.1)';
        li.style.color = customColor;
        li.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong>: ${message}`;

        const empty = alertList.querySelector('.empty-state');
        if (empty) empty.remove();

        alertList.prepend(li);

        if (ootCount) {
            let count = parseInt(ootCount.innerText) || 0;
            ootCount.innerText = count + 1;
        }
    }

    // --- TRUE Real-Time WebSocket Synchronization (Socket.IO) ---
    const socket = io();

    socket.on('chart_update', (data) => {
        const currentStudy = studySelect ? studySelect.value : null;
        const isDataEvalActive = document.querySelector('#data-evaluation').classList.contains('active');
        
        // Only refresh if the update belongs to the active study and we are on the main view
        if (currentStudy && data.batch_id === currentStudy && isDataEvalActive) {
            console.log("⚡ True Real-Time Update: Data broadcasted by Flask server!");
            loadDashboardData(currentStudy); // Refresh charts dynamically
            
            // Visual cue for WebSocket sync
            const systemStatus = document.querySelector('.system-status');
            if (systemStatus) {
                const originalHtml = systemStatus.innerHTML;
                systemStatus.innerHTML = '<span class="status-dot" style="background:#10b981; box-shadow: 0 0 10px #10b981;"></span> Live Data Received ✨';
                setTimeout(() => { systemStatus.innerHTML = originalHtml; }, 2500);
            }
        }
    });

    socket.on('oot_alert', (data) => {
        console.warn("🚨 WebSocket OOT Alert Received:", data);
        
        const severityColors = {
            'Warning': '#eab308',     // Yellow
            'Investigate': '#f97316', // Orange
            'Critical': '#ef4444'     // Red
        };
        
        const color = severityColors[data.severity] || '#ef4444';
        
        if (data.severity === 'Critical') {
            playAlertSound();
            window.showToast("CRITICAL ANOMALY:", `Batch ${data.batch_id} at Month ${data.time}\nCheck Dashboard immediately!`, "error", 10000);
        }
        
        addAlert(`[${data.severity.toUpperCase()}] Month ${data.time}: Pot: ${data.potency}%, Imp: ${data.impurity}%`, color);
    });

    async function loadDashboardData(studyId) {
        if (!studyId) return;

        try {
            // Update the title dynamically
            const logTitle = document.getElementById('detailedDataLogTitle');
            if (logTitle) logTitle.innerText = `Detailed Data Log for ${studyId}`;
            
            const response = await fetch(`/api/data?study_id=${studyId}`);
            const data = await response.json(); // Array of dicts

            // Sort by time
            data.sort((a, b) => a.Time_Point_Month - b.Time_Point_Month);

            const labels = data.map(d => `M${d.Time_Point_Month}`);
            const potency = data.map(d => d['Potency_%']);
            const impurities = data.map(d => d['Impurity_%']);

            // Render Chart
            renderMainChart(labels, potency, impurities);

            // Update Detailed Data Table
            const tableBody = document.querySelector('#dataTable tbody');
            if (tableBody) {
                console.log("Updating Data Table with", data.length, "rows.");
                tableBody.innerHTML = '';
                // Reverse order for table (newest first)
                [...data].reverse().forEach(row => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${row.Time_Point_Month}</td>
                        <td>${row['Potency_%']}%</td>
                        <td>${row['Impurity_%']}%</td>
                        <td>${checkStatus(row)}</td>
                    `;
                    tableBody.appendChild(tr);
                });
            } else {
                console.warn("Table body not found!");
            }

            // Fetch and Update Alerts for this specific study
            const alertsResponse = await fetch(`/api/alerts?study_id=${studyId}`);
            if (alertsResponse.ok) {
                const alertsData = await alertsResponse.json();
                
                if (ootCount) {
                    ootCount.innerText = alertsData.length;
                }
                
                if (alertList) {
                    alertList.innerHTML = ''; // Clear previous
                    if (alertsData.length === 0) {
                        alertList.innerHTML = '<li class="empty-state">No active alerts</li>';
                    } else {
                        alertsData.forEach(alert => {
                            const severityColors = {
                                'Warning': '#eab308',
                                'Investigate': '#f97316',
                                'Critical': '#ef4444'
                            };
                            const color = severityColors[alert.severity] || '#ef4444';
                            const li = document.createElement('li');
                            li.style.padding = '12px';
                            li.style.borderBottom = '1px solid rgba(255,255,255,0.1)';
                            li.style.color = color;
                            
                            // Parse timestamp elegantly
                            const dt = new Date(alert.timestamp);
                            const tStr = dt.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                            const dStr = dt.toLocaleDateString();
                            
                            li.innerHTML = `<strong>${dStr} ${tStr}</strong>: [${alert.severity.toUpperCase()}] ${alert.attribute} - Actual: ${alert.actual_value}% (Exp: ${alert.expected_value}%)`;
                            alertList.appendChild(li);
                        });
                    }
                }
            }

            // Update Prediction Text & Chart
            await updateShelfLife(studyId);

        } catch (e) {
            console.error("Error loading dashboard data", e);
        }
    }

    async function updateShelfLife(studyId) {
        try {
            console.log("Fetching Shelf Life Prediction for:", studyId);

            // 1. Get Prediction Info
            const predResp = await fetch(`/api/predict?study_id=${studyId}`);
            if (!predResp.ok) throw new Error("Failed to fetch prediction");
            const predData = await predResp.json();
            console.log("Prediction Data:", predData);

            // 2. Get Historical Data for the Line
            // (Optimize: reuse data if possible, but fetching ensures freshness)
            const histResp = await fetch(`/api/data?study_id=${studyId}`);
            const histData = await histResp.json();
            histData.sort((a, b) => a.Time_Point_Month - b.Time_Point_Month);

            // Update Text
            const shelfLifeDisplay = document.getElementById('shelfLifeValue');
            if (shelfLifeDisplay) {
                // If the backend returns a string like "> 120 Months" or "24 Months", use it directly.
                // If it's a number, format it.
                shelfLifeDisplay.innerText = predData.shelf_life || "Stable";
                shelfLifeDisplay.style.color = '#6366f1'; // Indigo for total
            }

            const remainingShelfLifeDisplay = document.getElementById('remainingShelfLifeValue');
            if (remainingShelfLifeDisplay) {
                remainingShelfLifeDisplay.innerText = predData.remaining_months || "--";
            }

            // Update Avg Shelf Life Stat Card
            const statCards = document.querySelectorAll('.stat-card');
            statCards.forEach(card => {
                const h3 = card.querySelector('h3');
                if (h3 && h3.innerText.toLowerCase().includes('avg shelf life')) {
                    const valueEl = card.querySelector('.stat-value');
                    if (valueEl) valueEl.innerText = (predData.shelf_life || "--").replace('Months', 'm');
                }
            });

            // 3. Render Prediction Chart (Regression Line)
            renderPredictionChart(histData, predData);

        } catch (e) {
            console.error("Error fetching shelf life/chart data", e);
            const shelfLifeDisplay = document.getElementById('shelfLifeValue');
            if (shelfLifeDisplay) {
                shelfLifeDisplay.innerText = "Error";
                shelfLifeDisplay.style.color = '#ef4444';
            }
        }
    }

    function renderPredictionChart(histData, predData) {
        console.log("Rendering Prediction Chart with", histData.length, "points");
        const ctx = document.getElementById('predictionChart');
        if (!ctx) return;

        if (charts.prediction) {
            charts.prediction.destroy();
            charts.prediction = null;
        }

        // Prepare Data
        const actualPoints = histData.map(d => ({ x: d.Time_Point_Month, y: d['Potency_%'] }));

        // Calculate Trend Line Extension
        // We want to draw a line from the start to the future point
        // If we have a next potency prediction, we use it.
        const lastMonth = actualPoints.length > 0 ? actualPoints[actualPoints.length - 1].x : 0;
        const projectMonth = lastMonth + 12; // Project 1 year ahead

        // Simple linear extrapolation for visual if we have >= 2 points
        let trendPoints = [];
        if (actualPoints.length >= 2) {
            // Perform basic Linear Regression to match the backend ML prediction model
            let n = actualPoints.length;
            let sumX = 0, sumY = 0, sumXY = 0, sumXX = 0;
            actualPoints.forEach(p => {
                sumX += p.x;
                sumY += p.y;
                sumXY += p.x * p.y;
                sumXX += p.x * p.x;
            });
            let m = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
            let c = (sumY - m * sumX) / n;

            // Extract the predicted failure month from backend's response (e.g., "45 Months")
            let shelfLifeMatch = predData.shelf_life ? String(predData.shelf_life).match(/(\d+)/) : null;
            let failureMonth = shelfLifeMatch ? parseInt(shelfLifeMatch[1]) : lastMonth + 12;

            // Draw the Regression Line!
            // Start the dashed line from the beginning (Month 0) through the points
            let startMonth = 0;
            let endMonth = Math.max(lastMonth, failureMonth) + 3; // Extend a bit past the max
            
            let startY = m * startMonth + c;
            let endY = m * endMonth + c;

            // Provide a line from regression equation at x = startMonth to x = endMonth
            trendPoints = [
                { x: startMonth, y: startY },
                { x: endMonth, y: endY }
            ];
        }

        charts.prediction = new Chart(ctx.getContext('2d'), {
            type: 'scatter',
            data: {
                datasets: [
                    {
                        label: 'Actual Potency Measurements',
                        data: actualPoints,
                        backgroundColor: '#6366f1',
                        pointRadius: 6,
                        pointHoverRadius: 8
                    },
                    {
                        label: 'Projected Degradation Trend',
                        data: trendPoints,
                        type: 'line',
                        borderColor: '#f43f5e',
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: { target: 'origin', above: 'rgba(244, 63, 94, 0.05)' },
                        showLine: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        title: { display: true, text: 'Time (Months)', color: '#94a3b8' },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        title: { display: true, text: 'Potency (%)', color: '#94a3b8' },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8' },
                        suggestedMin: 85,
                        suggestedMax: 105
                    }
                },
                plugins: {
                    annotation: {
                        annotations: {
                            line1: {
                                type: 'line',
                                yMin: 90,
                                yMax: 90,
                                borderColor: 'rgba(255, 99, 132, 0.5)',
                                borderWidth: 2,
                                label: {
                                    content: 'Failure Limit (90%)',
                                    enabled: true,
                                    position: 'start',
                                    color: 'rgba(255, 99, 132, 0.8)'
                                }
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Regression Analysis & Forecast',
                        color: '#f8fafc',
                        font: { size: 16 }
                    }
                }
            }
        });
    }

    function checkStatus(row) {
        // Industry terminology check: Spec limit vs Trend limit
        if (row['Potency_%'] < 95.0 || row['Potency_%'] > 105.0) return '<span style="color:#ef4444; font-weight:bold;">OOS (Failed)</span>';
        if (row['Impurity_%'] > 1.0) return '<span style="color:#ef4444; font-weight:bold;">OOS (Failed)</span>';
        
        return '<span style="color:#10b981">Within Spec</span>';
    }

    function renderMainChart(labels, potencyData, impurityData) {
        const ctx = document.getElementById('mainTrendChart');
        if (!ctx) {
            console.error("CRITICAL: Main Trend Chart Canvas element NOT FOUND in DOM");
            return;
        }

        const width = ctx.clientWidth;
        const height = ctx.clientHeight;
        console.log(`Rendering Main Chart. Canvas Size: ${width}x${height}`);
        console.log("Data:", { labels, potencyData });

        if (width === 0 || height === 0) {
            console.warn("Canvas has 0 dimensions. Retrying in 100ms...");
            setTimeout(() => renderMainChart(labels, potencyData, impurityData), 100);
            return;
        }

        // Check if Chart.js is loaded
        if (typeof Chart === 'undefined') {
            console.error("Chart.js is NOT defined.");
            ctx.parentNode.innerHTML = '<div style="color:red; padding:20px; border:1px solid red;">Error: Chart.js library not loaded. Check internet connection.</div>';
            return;
        }

        // Destroy existing chart
        if (charts.main) {
            try {
                charts.main.destroy();
            } catch (e) {
                console.warn("Failed to destroy chart", e);
            }
            charts.main = null;
        }

        try {
            charts.main = new Chart(ctx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Potency (%)',
                            data: potencyData,
                            borderColor: '#8b5cf6',
                            backgroundColor: 'rgba(139, 92, 246, 0.15)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 4,
                            pointBackgroundColor: '#8b5cf6',
                            pointHoverRadius: 8,
                            pointHoverBackgroundColor: '#fff',
                            pointHoverBorderColor: '#8b5cf6',
                            yAxisID: 'y'
                        },
                        {
                            label: 'Impurities (%)',
                            data: impurityData,
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59, 130, 246, 0.15)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 4,
                            pointBackgroundColor: '#3b82f6',
                            pointHoverRadius: 8,
                            pointHoverBackgroundColor: '#fff',
                            pointHoverBorderColor: '#3b82f6',
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false, // Disable animation to force immediate render
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { color: '#94a3b8' }
                        },
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: { display: true, text: 'Potency (%)', color: '#6366f1' },
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { color: '#94a3b8' },
                            suggestedMin: 90,
                            suggestedMax: 105
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: { display: true, text: 'Impurities (%)', color: '#3b82f6' },
                            grid: { drawOnChartArea: false },
                            ticks: { color: '#3b82f6' },
                            suggestedMin: 0,
                            suggestedMax: 1.5  // Reduced from 3 so 0.1-0.6% data is clearly visible
                        }
                    },
                    plugins: {
                        legend: { labels: { color: '#cbd5e1' } }
                    }
                }
            });
            console.log("Main Chart Rendered Successfully");
        } catch (e) {
            console.error("Error creating chart:", e);
            ctx.parentNode.innerHTML = `<div style="color:red; padding:20px;">Chart Error: ${e.message}</div>`;
        }
    }

    async function loadDetailedData(studyId) {
        // Redundant as we load table in loadDashboardData, but keeping for tab switch logic
        loadDashboardData(studyId);
    }

    function playAlertSound() {
        // Ambulance Siren Effect (Hi-Lo alternating pitch)
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

        const playTone = (frequency, startTime, duration) => {
            const oscillator = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioCtx.destination);

            oscillator.type = 'square'; // Harsh warning sound
            oscillator.frequency.value = frequency;

            // Simple envelope to avoid clicks
            gainNode.gain.setValueAtTime(0.01, startTime);
            gainNode.gain.exponentialRampToValueAtTime(0.1, startTime + 0.05);
            gainNode.gain.setValueAtTime(0.1, startTime + duration - 0.05);
            gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + duration);

            oscillator.start(startTime);
            oscillator.stop(startTime + duration);
        };

        const now = audioCtx.currentTime;
        const noteDuration = 0.5; // Half a second per tone

        // Play Hi-Lo 3 times (Ambulance style)
        for (let i = 0; i < 3; i++) {
            playTone(900, now + (i * 2 * noteDuration), noteDuration);     // High pitch (Hi)
            playTone(700, now + (i * 2 * noteDuration) + noteDuration, noteDuration); // Low pitch (Lo)
        }
    }

    // --- Live Simulation Feature ---
    window.runLiveSimulation = async function () {
        // Find current Study ID
        // Priority: Input box -> Select Box -> Default
        let studyId = 'ST-NORMAL-001';
        if (studyIdInput && studyIdInput.value) studyId = studyIdInput.value;
        else if (studySelect && studySelect.value && studySelect.value !== 'Select Study') studyId = studySelect.value;

        console.log("Starting Live Simulation for:", studyId);

        try {
            const response = await fetch(`/api/data?study_id=${studyId}`);
            if (!response.ok) throw new Error("API Error");

            const fullData = await response.json();
            // Ensure sorted
            fullData.sort((a, b) => a.Time_Point_Month - b.Time_Point_Month);

            if (fullData.length === 0) {
                window.showToast("No Data", "No data to simulate! Please add data first.", "warning");
                return;
            }

            // Loop and add points one by one
            let currentIndex = 0;
            const totalPoints = fullData.length;

            // Loop function
            function nextStep() {
                if (currentIndex >= totalPoints) {
                    console.log("Simulation Complete");
                    // Restore final state
                    loadDashboardData(studyId);
                    return;
                }

                const subset = fullData.slice(0, currentIndex + 1);
                const labels = subset.map(d => `M${d.Time_Point_Month}`);
                const potency = subset.map(d => d['Potency_%']);
                const impurities = subset.map(d => d['Impurity_%']);

                // Render intermediate state
                renderMainChart(labels, potency, impurities);

                currentIndex++;
                // Speed: 800ms per point
                setTimeout(nextStep, 800);
            }

            // Start
            nextStep();

        } catch (e) {
            console.error("Simulation failed", e);
            window.showToast("Simulation Failed", e.message, "error");
        }
    };

    const downloadPdfBtn = document.getElementById('downloadPdfBtn');
    if (downloadPdfBtn) {
        downloadPdfBtn.addEventListener('click', () => {
            const currentStudy = studyIdInput ? studyIdInput.value : 'Report';

            const originalText = downloadPdfBtn.innerHTML;
            downloadPdfBtn.innerHTML = 'Generating Full Report...';

            // Scroll to top to prevent html2canvas offset issues
            window.scrollTo(0, 0); 

            // Show Print Header Date
            const printDateStr = document.getElementById('printDateStr');
            if (printDateStr) printDateStr.innerText = new Date().toLocaleString();
            const printHeader = document.getElementById('printHeader');
            if (printHeader) printHeader.style.display = 'block';

            // Enable Print Mode
            document.body.classList.add('print-mode');

            // Resize charts to fit standard width before capture
            if (charts.main) charts.main.resize();
            if (charts.prediction) charts.prediction.resize();

            const element = document.getElementById('printContent');
            const opt = {
                margin:       10,
                filename:     `StabilAi_Report_${currentStudy}.pdf`,
                image:        { type: 'jpeg', quality: 0.98 },
                html2canvas:  { 
                    scale: 2, 
                    useCORS: true, 
                    backgroundColor: '#0a0f18', // Force the dark background
                    scrollY: 0,
                    scrollX: 0
                },
                jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' },
                pagebreak:    { mode: ['avoid-all', 'css', 'legacy'] }
            };

            // Give the browser enough time to reflow and render the new layout and charts
            setTimeout(() => {
                html2pdf().set(opt).from(element).save().then(() => {
                    document.body.classList.remove('print-mode');
                    if (printHeader) printHeader.style.display = 'none';
                    downloadPdfBtn.innerHTML = originalText;
                }).catch(err => {
                    console.error("PDF generation failed:", err);
                    downloadPdfBtn.innerHTML = originalText;
                    document.body.classList.remove('print-mode');
                    if (printHeader) printHeader.style.display = 'none';
                });
            }, 1000); // Increased timeout to ensure charts are fully rendered
        });
    }
});
