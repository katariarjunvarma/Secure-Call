// This file contains chart-related utilities that can be reused across the application

/**
 * Creates a chart for log activity
 * @param {string} canvasId - The ID of the canvas element
 * @param {Object} data - The chart data
 * @param {string} type - The chart type (bar, line, pie, etc.)
 * @param {Object} options - Chart options
 */
function createActivityChart(canvasId, data, type = 'bar', options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Default options for activity charts
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: 'Command Execution Activity'
            },
        }
    };
    
    // Merge default options with provided options
    const chartOptions = {...defaultOptions, ...options};
    
    return new Chart(ctx, {
        type: type,
        data: data,
        options: chartOptions
    });
}

/**
 * Fetch log data from the API and create a chart
 * @param {string} apiUrl - The URL to fetch log data from
 * @param {string} canvasId - The ID of the canvas element
 * @param {string} type - The chart type
 * @param {Object} options - Chart options
 */
function fetchAndCreateChart(apiUrl, canvasId, type = 'bar', options = {}) {
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            createActivityChart(canvasId, data, type, options);
        })
        .catch(error => {
            console.error('Error fetching chart data:', error);
            document.getElementById(canvasId).parentNode.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>Failed to load chart data: ${error.message}
                </div>
            `;
        });
}

/**
 * Create a distribution chart (pie/doughnut) for command statuses
 * @param {string} canvasId - The ID of the canvas element
 * @param {Object} data - Status data with counts
 */
function createStatusDistributionChart(canvasId, data) {
    const statusColors = {
        'Success': 'rgba(40, 167, 69, 0.8)',
        'Error': 'rgba(220, 53, 69, 0.8)',
        'Denied': 'rgba(255, 193, 7, 0.8)',
        'Timeout': 'rgba(108, 117, 125, 0.8)'
    };
    
    const labels = Object.keys(data);
    const values = Object.values(data);
    const backgroundColor = labels.map(label => statusColors[label] || 'rgba(0, 123, 255, 0.8)');
    
    const chartData = {
        labels: labels,
        datasets: [{
            data: values,
            backgroundColor: backgroundColor,
            borderWidth: 1
        }]
    };
    
    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'right',
            },
            title: {
                display: true,
                text: 'Command Status Distribution'
            }
        }
    };
    
    createActivityChart(canvasId, chartData, 'doughnut', options);
}
