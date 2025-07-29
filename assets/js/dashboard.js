// SND-Bench Dashboard JavaScript

// Global data storage
let benchmarkData = {
    metadata: null,
    runs: [],
    latestRun: null
};

// Chart instances
let performanceChart = null;
let modelChart = null;

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    setupEventListeners();
    setupAutoRefresh();
});

// Load dashboard data
async function loadDashboardData() {
    try {
        // Load metadata
        const metadataResponse = await fetch('metadata.json');
        if (metadataResponse.ok) {
            benchmarkData.metadata = await metadataResponse.json();
        }

        // Load runs index for quick overview
        const runsIndexResponse = await fetch('runs-index.json');
        if (runsIndexResponse.ok) {
            const runsIndex = await runsIndexResponse.json();
            
            // Use runs from index for initial display
            benchmarkData.runs = runsIndex.runs.map(run => ({
                ...run,
                runDir: run.run_id,
                // Set defaults for fields that might not be in index
                results: run.tasks ? Object.fromEntries(run.tasks.map(t => [t, {}])) : {},
                summary: run.has_summary ? 'Loading...' : null,
                wandb_history: run.has_wandb ? [{ url: run.wandb_url }] : []
            }));
            
            // Sort is already done in the index, but ensure it
            benchmarkData.runs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            
            if (benchmarkData.runs.length > 0) {
                benchmarkData.latestRun = benchmarkData.runs[0];
                
                // Lazy load full data for the latest run
                loadFullRunData(benchmarkData.latestRun.run_id);
            }
        } else {
            // Fallback to old method if runs index not available
            await loadRunsLegacy();
        }

        updateDashboard();
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError('Failed to load dashboard data');
    }
}

// Load full data for a specific run
async function loadFullRunData(runId) {
    try {
        const dataResponse = await fetch(`runs/${runId}/data.json`);
        if (dataResponse.ok) {
            const fullData = await dataResponse.json();
            
            // Update the run in our data
            const index = benchmarkData.runs.findIndex(r => r.run_id === runId);
            if (index !== -1) {
                benchmarkData.runs[index] = {
                    ...fullData,
                    runDir: runId
                };
                
                // Update latest run if it's the one we just loaded
                if (benchmarkData.latestRun && benchmarkData.latestRun.run_id === runId) {
                    benchmarkData.latestRun = benchmarkData.runs[index];
                    updateAISummary(); // Update AI summary with full data
                }
            }
        }
    } catch (error) {
        console.error(`Error loading full data for run ${runId}:`, error);
    }
}

// Legacy loading method for backwards compatibility
async function loadRunsLegacy() {
    const runDirs = await getRunDirectories();
    for (const runDir of runDirs) {
        try {
            const dataResponse = await fetch(`runs/${runDir}/data.json`);
            if (dataResponse.ok) {
                const runData = await dataResponse.json();
                benchmarkData.runs.push({
                    ...runData,
                    runDir: runDir
                });
            }
        } catch (error) {
            console.error(`Error loading run ${runDir}:`, error);
        }
    }
}

// Get run directories from runs index
async function getRunDirectories() {
    try {
        const response = await fetch('runs-index.json');
        if (response.ok) {
            const runsIndex = await response.json();
            // Extract run IDs from the index
            return runsIndex.runs.map(run => run.run_id);
        }
    } catch (error) {
        console.error('Error loading runs index:', error);
    }
    
    // Fallback to empty array if index not available
    return [];
}

// Update dashboard UI
function updateDashboard() {
    updateKPICards();
    updateRecentRunsTable();
    updateCharts();
    updateAISummary();
}

// Update KPI cards
function updateKPICards() {
    // Total benchmarks
    document.getElementById('totalBenchmarks').textContent = benchmarkData.runs.length;

    // Unique models tested
    const uniqueModels = new Set(benchmarkData.runs.map(run => run.model?.name)).size;
    document.getElementById('modelsTested').textContent = uniqueModels;

    // Average accuracy
    const validAccuracies = benchmarkData.runs
        .map(run => run.average_accuracy)
        .filter(acc => acc !== null && acc !== undefined && acc > 0);
    
    const avgAccuracy = validAccuracies.length > 0
        ? (validAccuracies.reduce((a, b) => a + b, 0) / validAccuracies.length * 100).toFixed(1)
        : '0';
    document.getElementById('avgAccuracy').textContent = `${avgAccuracy}%`;

    // Latest run
    if (benchmarkData.latestRun) {
        const modelName = benchmarkData.latestRun.model?.name || 'Unknown';
        document.getElementById('latestRun').textContent = modelName.split('/').pop();
        document.getElementById('latestRunTime').textContent = formatRelativeTime(benchmarkData.latestRun.timestamp);
    }
}

// Pagination state
let currentPage = 1;
const runsPerPage = 10;

// Update recent runs table with pagination
function updateRecentRunsTable(page = 1) {
    const tbody = document.getElementById('runsTableBody');
    tbody.innerHTML = '';

    // Calculate pagination
    currentPage = page;
    const startIndex = (page - 1) * runsPerPage;
    const endIndex = startIndex + runsPerPage;
    const paginatedRuns = benchmarkData.runs.slice(startIndex, endIndex);
    const totalPages = Math.ceil(benchmarkData.runs.length / runsPerPage);

    paginatedRuns.forEach(run => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';

        const modelName = run.model?.name || 'Unknown';
        const quantization = extractQuantization(modelName);
        const accuracy = (run.average_accuracy * 100).toFixed(2);
        const tasks = run.total_tasks || 1;
        const timestamp = formatTimestamp(run.timestamp);
        
        // Format task names with localization
        const taskList = run.tasks || [];
        const formattedTasks = taskList.map(task => 
            window.i18n ? window.i18n.formatTaskName(task) : task
        ).join(', ');
        
        // Find W&B URL
        let wandbUrl = '#';
        if (run.wandb_history && run.wandb_history.length > 0) {
            wandbUrl = run.wandb_history[0].url;
        }

        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                ${modelName.split('/').pop()}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <span class="badge badge-blue">${quantization}</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${accuracy}%
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500" title="${formattedTasks}">
                ${tasks} tasks
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${timestamp}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
                <div class="flex space-x-2">
                    <a href="runs/${run.runDir}/index.html" class="text-blue-600 hover:text-blue-900">
                        <i class="fas fa-chart-line"></i> Details
                    </a>
                    ${wandbUrl !== '#' ? `
                        <a href="${wandbUrl}" target="_blank" class="text-purple-600 hover:text-purple-900">
                            <i class="fas fa-external-link-alt"></i> W&B
                        </a>
                    ` : ''}
                </div>
            </td>
        `;

        tbody.appendChild(row);
    });
    
    // Add pagination controls
    addPaginationControls(totalPages);
}

// Add pagination controls
function addPaginationControls(totalPages) {
    // Check if pagination container exists, if not create it
    let paginationContainer = document.getElementById('paginationControls');
    if (!paginationContainer) {
        const tableContainer = document.querySelector('.bg-white.rounded-xl.shadow-sm.border.border-gray-200.mb-8');
        paginationContainer = document.createElement('div');
        paginationContainer.id = 'paginationControls';
        paginationContainer.className = 'px-6 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between';
        tableContainer.appendChild(paginationContainer);
    }
    
    // Clear existing controls
    paginationContainer.innerHTML = '';
    
    // Only show pagination if more than one page
    if (totalPages <= 1) return;
    
    // Create pagination info
    const info = document.createElement('div');
    info.className = 'text-sm text-gray-700';
    const startItem = (currentPage - 1) * runsPerPage + 1;
    const endItem = Math.min(currentPage * runsPerPage, benchmarkData.runs.length);
    info.textContent = `Showing ${startItem} to ${endItem} of ${benchmarkData.runs.length} runs`;
    
    // Create pagination buttons
    const buttonsContainer = document.createElement('div');
    buttonsContainer.className = 'flex space-x-2';
    
    // Previous button
    const prevButton = document.createElement('button');
    prevButton.className = `px-3 py-1 text-sm font-medium rounded-md ${
        currentPage === 1 
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
            : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
    }`;
    prevButton.textContent = 'Previous';
    prevButton.disabled = currentPage === 1;
    prevButton.onclick = () => currentPage > 1 && updateRecentRunsTable(currentPage - 1);
    
    // Page numbers
    const pageNumbers = document.createElement('div');
    pageNumbers.className = 'flex space-x-1';
    
    // Calculate page range to show
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) {
        addPageButton(pageNumbers, 1);
        if (startPage > 2) {
            const dots = document.createElement('span');
            dots.className = 'px-2 py-1 text-gray-500';
            dots.textContent = '...';
            pageNumbers.appendChild(dots);
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        addPageButton(pageNumbers, i);
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            const dots = document.createElement('span');
            dots.className = 'px-2 py-1 text-gray-500';
            dots.textContent = '...';
            pageNumbers.appendChild(dots);
        }
        addPageButton(pageNumbers, totalPages);
    }
    
    // Next button
    const nextButton = document.createElement('button');
    nextButton.className = `px-3 py-1 text-sm font-medium rounded-md ${
        currentPage === totalPages 
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
            : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
    }`;
    nextButton.textContent = 'Next';
    nextButton.disabled = currentPage === totalPages;
    nextButton.onclick = () => currentPage < totalPages && updateRecentRunsTable(currentPage + 1);
    
    // Assemble pagination controls
    buttonsContainer.appendChild(prevButton);
    buttonsContainer.appendChild(pageNumbers);
    buttonsContainer.appendChild(nextButton);
    
    paginationContainer.appendChild(info);
    paginationContainer.appendChild(buttonsContainer);
}

// Helper function to add page button
function addPageButton(container, pageNum) {
    const button = document.createElement('button');
    button.className = `px-3 py-1 text-sm font-medium rounded-md ${
        pageNum === currentPage
            ? 'bg-blue-600 text-white'
            : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
    }`;
    button.textContent = pageNum;
    button.onclick = () => updateRecentRunsTable(pageNum);
    container.appendChild(button);
}

// Update charts
function updateCharts() {
    updatePerformanceChart();
    updateModelChart();
}

// Update performance over time chart
function updatePerformanceChart() {
    const ctx = document.getElementById('performanceChart').getContext('2d');
    
    // Prepare data
    const chartData = benchmarkData.runs
        .slice(0, 20) // Last 20 runs
        .reverse()
        .map(run => ({
            x: new Date(run.timestamp),
            y: run.average_accuracy * 100
        }));

    if (performanceChart) {
        performanceChart.destroy();
    }

    performanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Accuracy %',
                data: chartData,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Accuracy: ${context.parsed.y.toFixed(2)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'hour',
                        displayFormats: {
                            hour: 'MMM d, HH:mm'
                        }
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

// Update model performance distribution chart
function updateModelChart() {
    const ctx = document.getElementById('modelChart').getContext('2d');
    
    // Group by model and calculate average accuracy
    const modelPerformance = {};
    benchmarkData.runs.forEach(run => {
        const modelName = run.model?.name?.split('/').pop() || 'Unknown';
        if (!modelPerformance[modelName]) {
            modelPerformance[modelName] = {
                accuracies: [],
                count: 0
            };
        }
        modelPerformance[modelName].accuracies.push(run.average_accuracy * 100);
        modelPerformance[modelName].count++;
    });

    const labels = Object.keys(modelPerformance);
    const data = labels.map(model => {
        const accs = modelPerformance[model].accuracies;
        return accs.reduce((a, b) => a + b, 0) / accs.length;
    });

    if (modelChart) {
        modelChart.destroy();
    }

    modelChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Average Accuracy',
                data: data,
                backgroundColor: [
                    'rgba(37, 99, 235, 0.8)',
                    'rgba(124, 58, 237, 0.8)',
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ],
                borderColor: [
                    '#2563eb',
                    '#7c3aed',
                    '#10b981',
                    '#f59e0b',
                    '#ef4444'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const model = context.label;
                            const count = modelPerformance[model].count;
                            return [
                                `Accuracy: ${context.parsed.y.toFixed(2)}%`,
                                `Runs: ${count}`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

// Update AI summary
function updateAISummary() {
    const summaryDiv = document.getElementById('aiSummary');
    
    if (benchmarkData.latestRun && benchmarkData.latestRun.summary) {
        // Convert markdown to HTML (simple conversion)
        const html = convertMarkdownToHTML(benchmarkData.latestRun.summary);
        summaryDiv.innerHTML = html;
    } else {
        summaryDiv.innerHTML = '<p class="text-gray-500">No analysis available for the latest run.</p>';
    }
}

// Setup event listeners
function setupEventListeners() {
    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', function() {
        this.querySelector('i').classList.add('fa-spin');
        loadDashboardData().then(() => {
            this.querySelector('i').classList.remove('fa-spin');
        });
    });
}

// Setup auto-refresh
function setupAutoRefresh() {
    // Refresh every 60 seconds
    setInterval(() => {
        loadDashboardData();
    }, 60000);
}

// Utility functions
function extractQuantization(modelName) {
    const match = modelName.match(/q\d+_[a-z]+_[a-z]+|q\d+_[a-z]+|f16|f32/i);
    return match ? match[0].toUpperCase() : 'Unknown';
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatRelativeTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
}

function convertMarkdownToHTML(markdown) {
    // Simple markdown to HTML conversion
    let html = markdown
        .replace(/## (.*?)$/gm, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\[([^\]]+)\]\(([^\)]+)\)/g, '<a href="$2" target="_blank" class="text-blue-600 hover:text-blue-800 underline">$1</a>')
        .replace(/\n\n/g, '</p><p class="mb-3">')
        .replace(/\n/g, '<br>');
    
    return `<p class="mb-3">${html}</p>`;
}

function showError(message) {
    console.error(message);
    // Could implement a toast notification here
}