// Charts and Data Visualization for AgriPredict
class AgriCharts {
    constructor() {
        this.chartColors = {
            primary: '#2d5016',
            secondary: '#4a7c59',
            accent: '#a4c969',
            success: '#40916c',
            warning: '#f77f00',
            danger: '#d62828'
        };
    }

    // Create yield prediction visualization
    createYieldChart(data) {
        const ctx = document.getElementById('yieldChart');
        if (!ctx) return;

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Predicted Yield', 'Average Yield', 'Optimal Yield'],
                datasets: [{
                    label: 'Yield (hg/ha)',
                    data: [data.predicted, data.average, data.optimal],
                    backgroundColor: [
                        this.chartColors.primary,
                        this.chartColors.secondary,
                        this.chartColors.accent
                    ],
                    borderColor: [
                        this.chartColors.primary,
                        this.chartColors.secondary,
                        this.chartColors.accent
                    ],
                    borderWidth: 2,
                    borderRadius: 10,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Yield Comparison',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Yield (hg/ha)'
                        }
                    }
                }
            }
        });
    }

    // Create weather trend chart
    createWeatherChart(data) {
        const ctx = document.getElementById('weatherChart');
        if (!ctx) return;

        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.years,
                datasets: [{
                    label: 'Rainfall (mm)',
                    data: data.rainfall,
                    borderColor: this.chartColors.primary,
                    backgroundColor: this.chartColors.primary + '20',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Rainfall Trend Analysis'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Rainfall (mm)'
                        }
                    }
                }
            }
        });
    }

    // Create NPK recommendation chart
    createNPKChart(data) {
        const ctx = document.getElementById('npkChart');
        if (!ctx) return;

        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Nitrogen (N)', 'Phosphorus (P)', 'Potassium (K)'],
                datasets: [{
                    data: [data.N, data.P, data.K],
                    backgroundColor: [
                        this.chartColors.success,
                        this.chartColors.warning,
                        this.chartColors.primary
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'NPK Composition'
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.agriCharts = new AgriCharts();
});
