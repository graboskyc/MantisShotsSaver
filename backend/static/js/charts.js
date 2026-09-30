function init() {
    return {
        async loadList() {
            const response = await fetch(`/api/stats/shots-over-time`);
            const data = await response.json();
            this.renderChart(data);
        },

        renderChart(data) {
            const options = {
                chart: {
                    type: 'line',
                    height: 350,
                    toolbar: {
                        show: false
                    }
                },
                series: [{
                    name: 'Shots',
                    data: data.map(d => d.total_shots)
                }],
                xaxis: {
                    categories: data.map(d => d._id)
                },
                tooltip: {
                    enabled: true
                }
            };

            const chart = new ApexCharts(document.querySelector("#chart"), options);
            chart.render();
        }
    }
}