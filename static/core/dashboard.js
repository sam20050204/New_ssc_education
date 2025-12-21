document.addEventListener("DOMContentLoaded", () => {
    const pieCtx = document.getElementById("pieChart");
    const barCtx = document.getElementById("barChart");

    if (pieCtx) {
        new Chart(pieCtx, {
            type: "pie",
            data: {
                labels: ["MSCIT", "KLIC"],
                datasets: [{
                    data: [10, 5],
                    backgroundColor: ["#3498db", "#27ae60"]
                }]
            }
        });
    }

    if (barCtx) {
        new Chart(barCtx, {
            type: "bar",
            data: {
                labels: ["Jan", "Feb", "Mar"],
                datasets: [{
                    label: "Admissions",
                    data: [2, 5, 3],
                    backgroundColor: "#3498db"
                }]
            }
        });
    }
});
