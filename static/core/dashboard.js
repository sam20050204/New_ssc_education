document.addEventListener("DOMContentLoaded", () => {
    const monthlyByCourseData = typeof monthlyByCourse !== "undefined" ? monthlyByCourse : {};
    const comparisonCanvas = document.getElementById("clusteredBarChart");
    const totalCanvas = document.getElementById("monthlyTotalChart");
    const statNumbers = document.querySelectorAll(".stat-number");
    const monthLabels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const isDarkMode = document.body.classList.contains("dark-mode") || document.documentElement.getAttribute("data-theme") === "dark";
    const axisColor = isDarkMode ? "rgba(231, 241, 244, 0.78)" : "rgba(27, 38, 59, 0.74)";
    const gridColor = isDarkMode ? "rgba(255, 255, 255, 0.08)" : "rgba(15, 23, 42, 0.08)";
    const tooltipBg = isDarkMode ? "#0f172a" : "#ffffff";
    const tooltipText = isDarkMode ? "#eff6ff" : "#162132";
    const palette = [
        { border: "#2563eb", fill: "rgba(37, 99, 235, 0.15)" },
        { border: "#0ea5e9", fill: "rgba(14, 165, 233, 0.15)" },
        { border: "#8b5cf6", fill: "rgba(139, 92, 246, 0.15)" },
        { border: "#f59e0b", fill: "rgba(245, 158, 11, 0.15)" },
        { border: "#10b981", fill: "rgba(16, 185, 129, 0.15)" },
        { border: "#ef4444", fill: "rgba(239, 68, 68, 0.15)" }
    ];

    function animateNumber(element) {
        const target = Number(String(element.textContent).replace(/[^\d.-]/g, ""));
        if (!Number.isFinite(target)) {
            return;
        }
        const duration = 900;
        const start = performance.now();
        function update(now) {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            element.textContent = Math.round(target * eased).toLocaleString();
            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                element.textContent = target.toLocaleString();
            }
        }
        requestAnimationFrame(update);
    }

    function buildYAxisMax(values) {
        const maxValue = Math.max(...values, 0);
        if (maxValue <= 5) return 5;
        if (maxValue <= 20) return Math.ceil(maxValue / 2) * 2 + 2;
        return Math.ceil(maxValue * 1.2);
    }

    function createEmptyState(canvas, message) {
        const wrapper = canvas.closest(".chart-canvas-wrap");
        if (!wrapper) return;
        wrapper.innerHTML = `<div class="chart-empty-state">${message}</div>`;
    }

    function baseScales(yAxisMax) {
        return {
            x: {
                ticks: { color: axisColor, font: { size: 12, weight: "700" } },
                grid: { display: false }
            },
            y: {
                beginAtZero: true,
                max: yAxisMax,
                ticks: {
                    color: axisColor,
                    stepSize: Math.max(1, Math.ceil(yAxisMax / 6)),
                    font: { size: 12, weight: "700" }
                },
                grid: { color: gridColor }
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
                    color: axisColor,
                    font: { size: 12, weight: "700" },
                    padding: 18
                }
            },
            tooltip: {
                backgroundColor: tooltipBg,
                titleColor: tooltipText,
                bodyColor: tooltipText,
                borderColor: isDarkMode ? "rgba(255,255,255,0.08)" : "rgba(15,23,42,0.08)",
                borderWidth: 1,
                padding: 12
            }
        };
    }

    statNumbers.forEach(animateNumber);

    const courseNames = Object.keys(monthlyByCourseData);

    if (comparisonCanvas) {
        if (!courseNames.length) {
            createEmptyState(comparisonCanvas, "No course admission data available for this view.");
        } else {
            const datasets = courseNames.map((course, index) => {
                const tones = palette[index % palette.length];
                return {
                    label: course,
                    data: monthLabels.map((_, monthIndex) => monthlyByCourseData[course][String(monthIndex + 1)] || 0),
                    borderColor: tones.border,
                    backgroundColor: tones.fill,
                    pointBackgroundColor: tones.border,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBorderColor: "#ffffff",
                    pointBorderWidth: 2,
                    borderWidth: 3,
                    fill: false,
                    tension: 0.32
                };
            });

            new Chart(comparisonCanvas, {
                type: "line",
                data: { labels: monthLabels, datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: "index", intersect: false },
                    plugins: basePlugins(),
                    scales: baseScales(buildYAxisMax(datasets.flatMap(dataset => dataset.data)))
                }
            });
        }
    }

    if (totalCanvas) {
        const totalMonthlyValues = monthLabels.map((_, monthIndex) =>
            courseNames.reduce((sum, course) => sum + (monthlyByCourseData[course]?.[String(monthIndex + 1)] || 0), 0)
        );

        if (!totalMonthlyValues.some(value => value > 0)) {
            createEmptyState(totalCanvas, "No total admission trend available for this view.");
        } else {
            const ctx = totalCanvas.getContext("2d");
            const gradient = ctx.createLinearGradient(0, 0, 0, 320);
            gradient.addColorStop(0, "rgba(37, 99, 235, 0.28)");
            gradient.addColorStop(1, "rgba(37, 99, 235, 0.03)");

            new Chart(totalCanvas, {
                type: "line",
                data: {
                    labels: monthLabels,
                    datasets: [{
                        label: selectedYear ? `Admissions (${selectedYear})` : "Admissions",
                        data: totalMonthlyValues,
                        borderColor: "#2563eb",
                        backgroundColor: gradient,
                        pointBackgroundColor: "#2563eb",
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
                    interaction: { mode: "index", intersect: false },
                    plugins: basePlugins(),
                    scales: baseScales(buildYAxisMax(totalMonthlyValues))
                }
            });
        }
    }
});
