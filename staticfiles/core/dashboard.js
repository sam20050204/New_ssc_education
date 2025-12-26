document.addEventListener("DOMContentLoaded", () => {
    const pieCtx = document.getElementById("pieChart");
    const barCtx = document.getElementById("barChart");

    // ===================== PIE CHART - COURSE DISTRIBUTION =====================
    if (pieCtx && typeof courseDistribution !== 'undefined') {
        // Convert course distribution object to arrays
        const courseLabels = Object.keys(courseDistribution);
        const courseData = Object.values(courseDistribution);
        
        // Generate colors for each course
        const colors = [
            "#667eea", // Purple
            "#f093fb", // Pink
            "#4facfe", // Blue
            "#43e97b", // Green
            "#fa709a", // Red
            "#fee140", // Yellow
            "#30cfd0", // Cyan
            "#a8edea", // Light cyan
            "#fbc2eb", // Light pink
            "#fdcbf1", // Very light pink
            "#e0c3fc", // Lavender
            "#8ec5fc"  // Sky blue
        ];
        
        // Create pie chart
        new Chart(pieCtx, {
            type: "pie",
            data: {
                labels: courseLabels.length > 0 ? courseLabels : ["No Data"],
                datasets: [{
                    data: courseData.length > 0 ? courseData : [1],
                    backgroundColor: courseLabels.length > 0 ? colors.slice(0, courseLabels.length) : ["#e0e0e0"],
                    borderWidth: 2,
                    borderColor: "#fff"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: {
                                size: 12,
                                weight: '600'
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} students (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    // ===================== BAR CHART - MONTHLY ADMISSIONS =====================
    if (barCtx && typeof monthlyData !== 'undefined') {
        // Month labels
        const monthLabels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        
        // Convert monthly data object to array (months 1-12)
        const monthlyValues = [];
        for (let i = 1; i <= 12; i++) {
            monthlyValues.push(monthlyData[i.toString()] || 0);
        }
        
        // Calculate max value for better y-axis scaling
        const maxValue = Math.max(...monthlyValues);
        const yAxisMax = maxValue > 0 ? Math.ceil(maxValue * 1.2) : 10;
        
        // Create bar chart
        new Chart(barCtx, {
            type: "bar",
            data: {
                labels: monthLabels,
                datasets: [{
                    label: selectedYear ? `Admissions in ${selectedYear}` : "Admissions (Current Year)",
                    data: monthlyValues,
                    backgroundColor: "rgba(102, 126, 234, 0.8)",
                    borderColor: "#667eea",
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: {
                                size: 12,
                                weight: '600'
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y} student${context.parsed.y !== 1 ? 's' : ''}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: yAxisMax,
                        ticks: {
                            stepSize: Math.ceil(yAxisMax / 10),
                            callback: function(value) {
                                return Number.isInteger(value) ? value : '';
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }
    
    // ===================== SHOW MESSAGE IF NO DATA =====================
    if (pieCtx && (!courseDistribution || Object.keys(courseDistribution).length === 0)) {
        console.log("No course distribution data available");
    }
    
    if (barCtx && (!monthlyData || Object.values(monthlyData).every(v => v === 0))) {
        console.log("No monthly admission data available");
    }
});