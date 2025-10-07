document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById('statusPieChart');

    // Ensure the canvas exists before rendering the chart
    if (!ctx) return;

    const availableVehicles = parseInt(ctx.dataset.available) || 0;
    const soldVehicles = parseInt(ctx.dataset.sold) || 0;

    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Available', 'Sold'],
            datasets: [{
                data: [availableVehicles, soldVehicles],
                backgroundColor: [
                    'rgba(25, 135, 84, 0.7)',   // Bootstrap green
                    'rgba(108, 117, 125, 0.7)'  // Bootstrap gray
                ],
                borderColor: [
                    'rgba(25, 135, 84, 1)',
                    'rgba(108, 117, 125, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                title: {
                    display: false
                }
            }
        }
    });
});
