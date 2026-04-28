document.addEventListener("DOMContentLoaded", () => {
    const monthlyByCourseData = typeof monthlyByCourse !== "undefined" ? monthlyByCourse : {};
    const comparisonCanvas = document.getElementById("clusteredBarChart");
    const totalCanvas = document.getElementById("monthlyTotalChart");
    const monthLabels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const rootStyles = getComputedStyle(document.documentElement);
    const isDarkMode = document.body.classList.contains("dark-mode") || document.documentElement.getAttribute("data-theme") === "dark";
    const axisColor = isDarkMode ? "rgba(231, 241, 244, 0.72)" : "rgba(32, 53, 62, 0.72)";
    const gridColor = isDarkMode ? "rgba(255, 255, 255, 0.08)" : "rgba(19, 58, 74, 0.08)";
    const tooltipBg = isDarkMode ? "#1e2b31" : "#ffffff";
    const tooltipText = isDarkMode ? "#edf5f7" : "#163647";
    const palette = [
        { border: "#1e6f88", fill: "rgba(30, 111, 136, 0.18)" },
        { border: "#f28f3b", fill: "rgba(242, 143, 59, 0.18)" },
        { border: "#1a9b8e", fill: "rgba(26, 155, 142, 0.18)" },
        { border: "#8d5cf6", fill: "rgba(141, 92, 246, 0.18)" },
        { border: "#d84f70", fill: "rgba(216, 79, 112, 0.18)" },
        { border: "#3b82f6", fill: "rgba(59, 130, 246, 0.18)" }
    ];

    function buildYAxisMax(values) {
        const maxValue = Math.max(...values, 0);
        if (maxValue <= 5) return 5;
        if (maxValue <= 20) return Math.ceil(maxValue / 2) * 2 + 2;
        return Math.ceil(maxValue * 1.15);
    }

    function createEmptyState(canvas, message) {
        const wrapper = canvas.closest(".chart-canvas-wrap");
        if (!wrapper) return;

        wrapper.innerHTML = `<div class="chart-empty-state">${message}</div>`;
    }

    function baseScales(yAxisMax) {
        return {
            x: {
                ticks: {
                    color: axisColor,
                    font: {
                        size: 12,
                        weight: "600"
                    }
                },
                grid: {
                    display: false,
                    drawBorder: false
                }
            },
            y: {
                beginAtZero: true,
                max: yAxisMax,
                ticks: {
                    color: axisColor,
                    padding: 10,
                    stepSize: Math.max(1, Math.ceil(yAxisMax / 6)),
                    font: {
                        size: 12,
                        weight: "600"
                    },
                    callback(value) {
                        return Number.isInteger(value) ? value : "";
                    }
                },
                grid: {
                    color: gridColor,
                    drawBorder: false
                }
            }
        };
    }

    function basePlugins() {
        return {
            legend: {
                position: "bottom",
                labels: {
                    usePointStyle: true,
                    pointStyle: "circle",
                    boxWidth: 10,
                    boxHeight: 10,
                    padding: 18,
                    color: axisColor,
                    font: {
                        size: 12,
                        weight: "600"
                    }
                }
            },
            tooltip: {
                backgroundColor: tooltipBg,
                titleColor: tooltipText,
                bodyColor: tooltipText,
                borderColor: isDarkMode ? "rgba(255, 255, 255, 0.08)" : "rgba(22, 54, 71, 0.08)",
                borderWidth: 1,
                padding: 12,
                displayColors: true,
                boxPadding: 6
            }
        };
    }

    const courseNames = Object.keys(monthlyByCourseData);

    if (comparisonCanvas) {
        if (!courseNames.length) {
            createEmptyState(comparisonCanvas, "No course admission data available for this view.");
        } else {
            const comparisonDatasets = courseNames.map((course, index) => {
                const tones = palette[index % palette.length];
                const data = monthLabels.map((_, monthIndex) => monthlyByCourseData[course][String(monthIndex + 1)] || 0);

                return {
                    label: course,
                    data,
                    borderColor: tones.border,
                    backgroundColor: tones.fill,
                    pointBackgroundColor: tones.border,
                    pointBorderColor: "#ffffff",
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: tones.border,
                    borderWidth: 3,
                    tension: 0.35,
                    fill: false
                };
            });

            const allCourseValues = comparisonDatasets.flatMap((dataset) => dataset.data);
            const comparisonMax = buildYAxisMax(allCourseValues);

            new Chart(comparisonCanvas, {
                type: "line",
                data: {
                    labels: monthLabels,
                    datasets: comparisonDatasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: "index",
                        intersect: false
                    },
                    plugins: {
                        ...basePlugins(),
                        tooltip: {
                            ...basePlugins().tooltip,
                            callbacks: {
                                label(context) {
                                    return `${context.dataset.label}: ${context.parsed.y} student${context.parsed.y !== 1 ? "s" : ""}`;
                                }
                            }
                        }
                    },
                    scales: baseScales(comparisonMax)
                }
            });
        }
    }

    if (totalCanvas) {
        const totalMonthlyValues = monthLabels.map((_, monthIndex) => {
            return courseNames.reduce((sum, course) => {
                return sum + (monthlyByCourseData[course]?.[String(monthIndex + 1)] || 0);
            }, 0);
        });

        const hasTotals = totalMonthlyValues.some((value) => value > 0);

        if (!hasTotals) {
            createEmptyState(totalCanvas, "No total admission trend available for this view.");
        } else {
            const totalMax = buildYAxisMax(totalMonthlyValues);
            const gradient = totalCanvas.getContext("2d").createLinearGradient(0, 0, 0, 320);
            gradient.addColorStop(0, "rgba(242, 143, 59, 0.38)");
            gradient.addColorStop(1, "rgba(242, 143, 59, 0.04)");

            new Chart(totalCanvas, {
                type: "line",
                data: {
                    labels: monthLabels,
                    datasets: [{
                        label: selectedYear ? `Total Admissions (${selectedYear})` : "Total Admissions",
                        data: totalMonthlyValues,
                        borderColor: "#f28f3b",
                        backgroundColor: gradient,
                        pointBackgroundColor: "#f28f3b",
                        pointBorderColor: "#ffffff",
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 7,
                        borderWidth: 4,
                        fill: true,
                        tension: 0.35
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: "index",
                        intersect: false
                    },
                    plugins: {
                        ...basePlugins(),
                        tooltip: {
                            ...basePlugins().tooltip,
                            callbacks: {
                                label(context) {
                                    return `${context.dataset.label}: ${context.parsed.y} student${context.parsed.y !== 1 ? "s" : ""}`;
                                }
                            }
                        }
                    },
                    scales: baseScales(totalMax)
                }
            });
        }
    }
});
