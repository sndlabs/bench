// SND-Bench Model Comparison JavaScript

// Comparison data storage
let comparisonData = {
    allRuns: [],
    selectedModels: new Set(),
    sortColumn: 'accuracy',
    sortDirection: 'desc'
};

// Chart instances for comparison
let radarChart = null;
let barChart = null;
let scatterChart = null;

// Initialize comparison page
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname.includes('compare.html')) {
        loadComparisonData();
        setupComparisonEventListeners();
    }
});

// Load comparison data
async function loadComparisonData() {
    try {
        // Load all run data
        const runDirs = await getRunDirectories();
        comparisonData.allRuns = [];
        
        for (const runDir of runDirs) {
            try {
                const dataResponse = await fetch(`runs/${runDir}/data.json`);
                if (dataResponse.ok) {
                    const runData = await dataResponse.json();
                    comparisonData.allRuns.push({
                        ...runData,
                        runDir: runDir
                    });
                }
            } catch (error) {
                console.error(`Error loading run ${runDir}:`, error);
            }
        }

        // Sort by timestamp
        comparisonData.allRuns.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        populateModelSelection();
        updateComparisonView();
    } catch (error) {
        console.error('Error loading comparison data:', error);
    }
}

// Populate model selection checkboxes
function populateModelSelection() {
    const container = document.getElementById('modelSelection');
    container.innerHTML = '';

    // Get unique models with their latest runs
    const modelMap = new Map();
    comparisonData.allRuns.forEach(run => {
        const modelName = run.model?.name || 'Unknown';
        if (!modelMap.has(modelName) || new Date(run.timestamp) > new Date(modelMap.get(modelName).timestamp)) {
            modelMap.set(modelName, run);
        }
    });

    // Create checkboxes for each model
    modelMap.forEach((run, modelName) => {
        const div = document.createElement('div');
        div.className = 'flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `model-${modelName}`;
        checkbox.value = modelName;
        checkbox.className = 'model-checkbox';
        checkbox.addEventListener('change', handleModelSelection);

        const label = document.createElement('label');
        label.htmlFor = `model-${modelName}`;
        label.className = 'flex-1 cursor-pointer';
        
        const modelShortName = modelName.split('/').pop();
        const accuracy = (run.average_accuracy * 100).toFixed(1);
        
        label.innerHTML = `
            <div class="font-medium text-gray-900">${modelShortName}</div>
            <div class="text-sm text-gray-500">Accuracy: ${accuracy}% | ${formatRelativeTime(run.timestamp)}</div>
        `;

        div.appendChild(checkbox);
        div.appendChild(label);
        container.appendChild(div);
    });
}

// Handle model selection
function handleModelSelection(event) {
    const modelName = event.target.value;
    
    if (event.target.checked) {
        comparisonData.selectedModels.add(modelName);
    } else {
        comparisonData.selectedModels.delete(modelName);
    }
    
    updateSelectionCount();
    updateComparisonView();
}

// Update selection count
function updateSelectionCount() {
    const count = comparisonData.selectedModels.size;
    document.getElementById('selectionCount').textContent = `${count} model${count !== 1 ? 's' : ''} selected`;
}

// Update comparison view
function updateComparisonView() {
    updateComparisonTable();
    updateComparisonCharts();
}

// Update comparison table
function updateComparisonTable() {
    const tbody = document.getElementById('comparisonTableBody');
    tbody.innerHTML = '';

    if (comparisonData.selectedModels.size === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="px-6 py-8 text-center text-gray-500">
                    Select models to compare
                </td>
            </tr>
        `;
        return;
    }

    // Get data for selected models
    const showLatestOnly = document.getElementById('showLatestOnly').checked;
    const selectedRuns = [];
    
    comparisonData.selectedModels.forEach(modelName => {
        const modelRuns = comparisonData.allRuns.filter(run => run.model?.name === modelName);
        if (showLatestOnly && modelRuns.length > 0) {
            selectedRuns.push(modelRuns[0]);
        } else {
            selectedRuns.push(...modelRuns);
        }
    });

    // Sort runs
    selectedRuns.sort((a, b) => {
        let aVal, bVal;
        
        switch (comparisonData.sortColumn) {
            case 'accuracy':
                aVal = a.average_accuracy || 0;
                bVal = b.average_accuracy || 0;
                break;
            case 'perplexity':
                aVal = a.results?.perplexity?.accuracy || 0;
                bVal = b.results?.perplexity?.accuracy || 0;
                break;
            case 'size':
                aVal = parseFloat(a.model?.size) || 0;
                bVal = parseFloat(b.model?.size) || 0;
                break;
            case 'quantization':
                aVal = extractQuantization(a.model?.name || '');
                bVal = extractQuantization(b.model?.name || '');
                break;
            default:
                aVal = a.model?.name || '';
                bVal = b.model?.name || '';
        }
        
        if (comparisonData.sortDirection === 'asc') {
            return aVal > bVal ? 1 : -1;
        } else {
            return aVal < bVal ? 1 : -1;
        }
    });

    // Populate table
    selectedRuns.forEach(run => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';
        
        const modelName = run.model?.name || 'Unknown';
        const modelShortName = modelName.split('/').pop();
        const quantization = extractQuantization(modelName);
        const accuracy = (run.average_accuracy * 100).toFixed(2);
        const perplexity = run.results?.perplexity?.accuracy?.toFixed(2) || 'N/A';
        const size = run.model?.size || 'Unknown';
        
        let wandbUrl = '#';
        if (run.wandb_history && run.wandb_history.length > 0) {
            wandbUrl = run.wandb_history[0].url;
        }
        
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 sticky left-0 bg-white">
                ${modelShortName}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <span class="badge badge-blue">${quantization}</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${accuracy}%
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${perplexity}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${size}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
                ${wandbUrl !== '#' ? `
                    <a href="${wandbUrl}" target="_blank" class="text-purple-600 hover:text-purple-900">
                        <i class="fas fa-external-link-alt"></i> View
                    </a>
                ` : '-'}
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Update comparison charts
function updateComparisonCharts() {
    if (comparisonData.selectedModels.size === 0) {
        // Clear charts
        if (radarChart) radarChart.destroy();
        if (barChart) barChart.destroy();
        if (scatterChart) scatterChart.destroy();
        return;
    }

    updateRadarChart();
    updateBarChart();
    updateScatterChart();
}

// Update radar chart
function updateRadarChart() {
    const ctx = document.getElementById('radarChart').getContext('2d');
    
    // Get latest run for each selected model
    const modelData = [];
    comparisonData.selectedModels.forEach(modelName => {
        const runs = comparisonData.allRuns.filter(run => run.model?.name === modelName);
        if (runs.length > 0) {
            modelData.push({
                model: modelName.split('/').pop(),
                run: runs[0]
            });
        }
    });

    // Prepare datasets
    const datasets = modelData.map((data, index) => {
        const colors = ['#2563eb', '#7c3aed', '#10b981', '#f59e0b', '#ef4444'];
        const color = colors[index % colors.length];
        
        return {
            label: data.model,
            data: [
                data.run.average_accuracy * 100,
                data.run.results?.perplexity?.accuracy || 0,
                100 - (parseFloat(data.run.model?.size) || 0) * 10, // Inverse size score
                data.run.total_tasks || 0,
                50 // Placeholder for speed metric
            ],
            borderColor: color,
            backgroundColor: color + '33',
            pointBackgroundColor: color,
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: color
        };
    });

    if (radarChart) {
        radarChart.destroy();
    }

    radarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Accuracy', 'Perplexity', 'Efficiency', 'Coverage', 'Speed'],
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Update bar chart
function updateBarChart() {
    const ctx = document.getElementById('barChart').getContext('2d');
    const metric = document.getElementById('metricSelect').value;
    
    // Get data for selected models
    const labels = [];
    const data = [];
    const backgroundColors = [];
    const borderColors = [];
    
    comparisonData.selectedModels.forEach((modelName, index) => {
        const runs = comparisonData.allRuns.filter(run => run.model?.name === modelName);
        if (runs.length > 0) {
            const run = runs[0];
            labels.push(modelName.split('/').pop());
            
            let value = 0;
            switch (metric) {
                case 'accuracy':
                    value = run.average_accuracy * 100;
                    break;
                case 'perplexity':
                    value = run.results?.perplexity?.accuracy || 0;
                    break;
                case 'size':
                    value = parseFloat(run.model?.size) || 0;
                    break;
                default:
                    value = run.average_accuracy * 100;
            }
            
            data.push(value);
            
            const colors = ['#2563eb', '#7c3aed', '#10b981', '#f59e0b', '#ef4444'];
            const color = colors[index % colors.length];
            backgroundColors.push(color + 'CC');
            borderColors.push(color);
        }
    });

    if (barChart) {
        barChart.destroy();
    }

    barChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: metric.charAt(0).toUpperCase() + metric.slice(1),
                data: data,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            if (metric === 'accuracy' || metric === 'perplexity') {
                                return value + '%';
                            } else if (metric === 'size') {
                                return value + 'GB';
                            }
                            return value;
                        }
                    }
                }
            }
        }
    });
}

// Update scatter chart
function updateScatterChart() {
    const ctx = document.getElementById('scatterChart').getContext('2d');
    
    // Prepare data points
    const datasets = [];
    const colorMap = {};
    const colors = ['#2563eb', '#7c3aed', '#10b981', '#f59e0b', '#ef4444'];
    
    let colorIndex = 0;
    comparisonData.selectedModels.forEach(modelName => {
        const runs = comparisonData.allRuns.filter(run => run.model?.name === modelName);
        const modelShortName = modelName.split('/').pop();
        const color = colors[colorIndex % colors.length];
        colorMap[modelName] = color;
        colorIndex++;
        
        const data = runs.map(run => ({
            x: parseFloat(run.model?.size) || 0,
            y: run.average_accuracy * 100,
            label: modelShortName
        }));
        
        datasets.push({
            label: modelShortName,
            data: data,
            backgroundColor: color + '99',
            borderColor: color,
            borderWidth: 1,
            pointRadius: 6,
            pointHoverRadius: 8
        });
    });

    if (scatterChart) {
        scatterChart.destroy();
    }

    scatterChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}% @ ${context.parsed.x.toFixed(1)}GB`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Model Size (GB)'
                    },
                    beginAtZero: true
                },
                y: {
                    title: {
                        display: true,
                        text: 'Accuracy (%)'
                    },
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

// Setup comparison event listeners
function setupComparisonEventListeners() {
    // Select all button
    document.getElementById('selectAllBtn')?.addEventListener('click', function() {
        document.querySelectorAll('.model-checkbox').forEach(checkbox => {
            checkbox.checked = true;
            comparisonData.selectedModels.add(checkbox.value);
        });
        updateSelectionCount();
        updateComparisonView();
    });

    // Clear selection button
    document.getElementById('clearSelectionBtn')?.addEventListener('click', function() {
        document.querySelectorAll('.model-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        comparisonData.selectedModels.clear();
        updateSelectionCount();
        updateComparisonView();
    });

    // Latest only checkbox
    document.getElementById('showLatestOnly')?.addEventListener('change', function() {
        updateComparisonView();
    });

    // Metric select
    document.getElementById('metricSelect')?.addEventListener('change', function() {
        updateComparisonCharts();
    });

    // Sort columns
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.addEventListener('click', function() {
            const column = this.dataset.sort;
            
            // Update sort direction
            if (comparisonData.sortColumn === column) {
                comparisonData.sortDirection = comparisonData.sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                comparisonData.sortColumn = column;
                comparisonData.sortDirection = 'desc';
            }
            
            // Update UI
            document.querySelectorAll('th[data-sort]').forEach(header => {
                header.classList.remove('sort-asc', 'sort-desc');
            });
            
            this.classList.add(comparisonData.sortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
            
            updateComparisonTable();
        });
    });

    // Export button
    document.getElementById('exportBtn')?.addEventListener('click', exportComparisonData);

    // Refresh button (reuse from dashboard)
    document.getElementById('refreshBtn')?.addEventListener('click', function() {
        this.querySelector('i').classList.add('fa-spin');
        loadComparisonData().then(() => {
            this.querySelector('i').classList.remove('fa-spin');
        });
    });
}

// Export comparison data
function exportComparisonData() {
    if (comparisonData.selectedModels.size === 0) {
        alert('Please select models to export');
        return;
    }

    // Prepare export data
    const exportData = {
        timestamp: new Date().toISOString(),
        selectedModels: Array.from(comparisonData.selectedModels),
        runs: []
    };

    comparisonData.selectedModels.forEach(modelName => {
        const runs = comparisonData.allRuns.filter(run => run.model?.name === modelName);
        exportData.runs.push(...runs.map(run => ({
            model: run.model?.name,
            runId: run.run_id,
            timestamp: run.timestamp,
            accuracy: run.average_accuracy,
            perplexity: run.results?.perplexity?.accuracy,
            size: run.model?.size,
            tasks: run.total_tasks,
            wandbUrl: run.wandb_history?.[0]?.url
        })));
    });

    // Download JSON file
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `snd-bench-comparison-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    // Add animation to button
    const exportBtn = document.getElementById('exportBtn');
    exportBtn.classList.add('export-animation');
    setTimeout(() => {
        exportBtn.classList.remove('export-animation');
    }, 2000);
}