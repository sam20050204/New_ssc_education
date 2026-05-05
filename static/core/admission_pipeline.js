(function() {
    const chartData = window.admissionPipelineCharts || {};
    const textColor = "#334155";
    const softGrid = "rgba(148, 163, 184, 0.18)";

    function baseOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: textColor,
                        usePointStyle: true,
                        boxWidth: 10,
                        padding: 18,
                    },
                },
            },
            scales: {
                x: {
                    ticks: { color: textColor },
                    grid: { color: softGrid, drawBorder: false },
                },
                y: {
                    ticks: { color: textColor },
                    grid: { color: softGrid, drawBorder: false },
                },
            },
        };
    }

    const funnelCanvas = document.getElementById("pipelineFunnelChart");
    if (funnelCanvas && chartData.pipeline) {
        new Chart(funnelCanvas, {
            type: "bar",
            data: {
                labels: chartData.pipeline.labels,
                datasets: [{
                    label: "Leads",
                    data: chartData.pipeline.values,
                    borderRadius: 12,
                    backgroundColor: [
                        "#6366f1",
                        "#38bdf8",
                        "#8b5cf6",
                        "#f59e0b",
                        "#f43f5e",
                        "#10b981",
                        "#64748b",
                    ],
                }],
            },
            options: {
                ...baseOptions(),
                indexAxis: "y",
                plugins: { legend: { display: false } },
            },
        });
    }

    const conversionCanvas = document.getElementById("conversionTrendChart");
    if (conversionCanvas && chartData.conversion) {
        new Chart(conversionCanvas, {
            type: "line",
            data: {
                labels: chartData.conversion.labels,
                datasets: [
                    {
                        label: "Inquiries",
                        data: chartData.conversion.inquiries,
                        borderColor: "#6366f1",
                        backgroundColor: "rgba(99, 102, 241, 0.14)",
                        tension: 0.35,
                        fill: true,
                    },
                    {
                        label: "Admissions",
                        data: chartData.conversion.admissions,
                        borderColor: "#10b981",
                        backgroundColor: "rgba(16, 185, 129, 0.10)",
                        tension: 0.35,
                        fill: true,
                    },
                ],
            },
            options: baseOptions(),
        });
    }

    const courseCanvas = document.getElementById("coursePopularityChart");
    if (courseCanvas && chartData.course) {
        new Chart(courseCanvas, {
            type: "doughnut",
            data: {
                labels: chartData.course.labels,
                datasets: [{
                    data: chartData.course.values,
                    backgroundColor: ["#6366f1", "#3b82f6", "#8b5cf6", "#14b8a6", "#f59e0b"],
                    borderWidth: 0,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "68%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            color: textColor,
                            usePointStyle: true,
                            boxWidth: 10,
                            padding: 16,
                        },
                    },
                },
            },
        });
    }

    const revenueCanvas = document.getElementById("revenueTrackingChart");
    if (revenueCanvas && chartData.revenue) {
        new Chart(revenueCanvas, {
            data: {
                labels: chartData.revenue.labels,
                datasets: [
                    {
                        type: "bar",
                        label: "Collected",
                        data: chartData.revenue.collected,
                        backgroundColor: "rgba(59, 130, 246, 0.8)",
                        borderRadius: 12,
                    },
                    {
                        type: "line",
                        label: "Projected",
                        data: chartData.revenue.projected,
                        borderColor: "#7c3aed",
                        backgroundColor: "rgba(124, 58, 237, 0.12)",
                        tension: 0.35,
                        fill: true,
                    },
                ],
            },
            options: baseOptions(),
        });
    }
})();
