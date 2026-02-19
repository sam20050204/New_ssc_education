document.addEventListener("DOMContentLoaded", () => {
    const clusteredBarCtx = document.getElementById("clusteredBarChart");
    const monthlyTotalCtx = document.getElementById("monthlyTotalChart");

    // ===================== CUSTOM PLUGIN TO DRAW DATA LABELS ON TOP OF BARS =====================
    const dataLabelsPlugin = {
        id: 'dataLabels',
        afterDatasetsDraw: function(chart) {
            const ctx = chart.ctx;
            chart.data.datasets.forEach(function(dataset, i) {
                const meta = chart.getDatasetMeta(i);
                if (!meta.hidden) {
                    meta.data.forEach(function(element, index) {
                        // Get the value
                        const value = dataset.data[index];
                        if (value > 0) {
                            // Set up font
                            ctx.font = 'bold 12px Arial';
                            ctx.fillStyle = '#333';
                            ctx.textAlign = 'center';
                            
                            // Get position and draw text on top of bar
                            const x = element.x;
                            const y = element.y - 5; // 5px above the top of bar
                            
                            ctx.fillText(value, x, y);
                        }
                    });
                }
            });
        }
    };

    // ===================== CLUSTERED BAR CHART - ADMISSIONS BY COURSE PER MONTH =====================
    if (clusteredBarCtx && typeof monthlyByCourse !== 'undefined') {
        // Month labels
        const monthLabels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        
        // Define colors for different courses
        const courseColors = {
            "MS-CIT": "rgba(102, 126, 234, 0.8)",
            "KLIC": "rgba(240, 147, 251, 0.8)",
            "JAVA": "rgba(79, 172, 254, 0.8)",
            "PYTHON": "rgba(67, 233, 123, 0.8)",
            "WEB": "rgba(250, 112, 154, 0.8)",
            "CCNA": "rgba(254, 193, 64, 0.8)"
        };
        
        const courseBorders = {
            "MS-CIT": "#667eea",
            "KLIC": "#f093fb",
            "JAVA": "#4facfe",
            "PYTHON": "#43e97b",
            "WEB": "#fa709a",
            "CCNA": "#fee140"
        };
        
        // Get all courses and their data
        const courses = Object.keys(monthlyByCourse);
        const datasets = [];
        
        courses.forEach((course, index) => {
            const monthlyValues = [];
            for (let i = 1; i <= 12; i++) {
                monthlyValues.push(monthlyByCourse[course][i.toString()] || 0);
            }
            
            // Assign color or use a default color array
            const colors = Object.values(courseColors);
            const borders = Object.values(courseBorders);
            const colorIndex = index % colors.length;
            
            datasets.push({
                label: course,
                data: monthlyValues,
                backgroundColor: colors[colorIndex],
                borderColor: borders[colorIndex],
                borderWidth: 2,
                borderRadius: 6
            });
        });
        
        // Calculate max value for better y-axis scaling
        const allValues = datasets.flatMap(d => d.data);
        const maxValue = Math.max(...allValues, 1);
        const yAxisMax = Math.ceil(maxValue * 1.2);
        
        // Create clustered bar chart
        new Chart(clusteredBarCtx, {
            type: "bar",
            data: {
                labels: monthLabels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                indexAxis: 'x',
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

    // ===================== BAR CHART - TOTAL MONTHLY ADMISSIONS =====================
    if (monthlyTotalCtx && typeof monthlyByCourse !== 'undefined') {
        const monthLabels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        
        // Calculate total admissions per month
        const totalMonthlyValues = [];
        for (let i = 1; i <= 12; i++) {
            let monthTotal = 0;
            const courses = Object.keys(monthlyByCourse);
            courses.forEach(course => {
                monthTotal += monthlyByCourse[course][i.toString()] || 0;
            });
            totalMonthlyValues.push(monthTotal);
        }
        
        // Calculate max value for better y-axis scaling
        const maxValue = Math.max(...totalMonthlyValues, 1);
        const yAxisMax = Math.ceil(maxValue * 1.2);
        
        // Create total monthly bar chart
        new Chart(monthlyTotalCtx, {
            type: "bar",
            data: {
                labels: monthLabels,
                datasets: [{
                    label: selectedYear ? `Total Admissions (${selectedYear})` : "Total Admissions",
                    data: totalMonthlyValues,
                    backgroundColor: "rgba(244, 120, 67, 0.8)",
                    borderColor: "#f47843",
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            plugins: [dataLabelsPlugin],
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
    if (clusteredBarCtx && (!monthlyByCourse || Object.keys(monthlyByCourse).length === 0)) {
        console.log("No monthly data by course available");
    }
});