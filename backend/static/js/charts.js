function init() {
    return {
        async loadList() {
            const response = await fetch(`/api/stats/shots-over-time`);
            const data = await response.json();
            this.renderChart(data);

            const sessionResponse = await fetch(`/api/stats/session-scores`);
            const sessionData = await sessionResponse.json();
            this.renderCandlestickChart(sessionData);

            const accuracyResponse = await fetch(`/api/stats/average-accuracy`);
            const accuracyData = await accuracyResponse.json();
            this.renderGaugeChart(accuracyData.accuracy);

            const timeResponse = await fetch(`/api/stats/average-shot-time`);
            const timeData = await timeResponse.json();
            this.renderTimeGaugeChart(timeData.time);
        },

        renderChart(data) {
            const options = {
                chart: {
                    type: 'line',
                    height: 350,
                    toolbar: { show: false }
                },
                series: [{
                    name: 'Shots',
                    data: data.map(d => d.total_shots)
                }],
                xaxis: {
                    categories: data.map(d => d._id)
                },
                tooltip: { enabled: true }
            };

            const chart = new ApexCharts(document.querySelector("#chart"), options);
            chart.render();
        },

        renderCandlestickChart(data) {
            const options = {
                chart: {
                    type: 'candlestick',
                    height: 350,
                    toolbar: {
                        show: false
                    }
                },
                series: [{
                    name: 'Session Scores',
                    data: data
                }],
                xaxis: { type: 'datetime' }
            };

            const chart = new ApexCharts(document.querySelector("#candlestick-chart"), options);
            chart.render();
        },

        renderGaugeChart(accuracy) {
            const options = {
                chart: {
                    type: 'radialBar',
                    height: 350
                },
                series: [accuracy],
                plotOptions: {
                    radialBar: {
                        startAngle: -90,
                        endAngle: 90,
                        hollow: { size: '70%' },
                        dataLabels: {
                            name: { show: false },
                            value: {
                                fontSize: '22px',
                                formatter: function(val) { return val + '%' }
                            }
                        }
                    }
                },
                labels: ['Average Accuracy'],
                title: {
                    text: 'Average Accuracy',
                    align: 'center'
                }
            };

            const chart = new ApexCharts(document.querySelector("#gauge-chart"), options);
            chart.render();
        },

        renderTimeGaugeChart(time) {
            const options = {
                chart: {
                    type: 'radialBar',
                    height: 350
                },
                series: [(time / 5) * 100], // map 1s-5s to 0-100%
                plotOptions: {
                    radialBar: {
                        startAngle: -90,
                        endAngle: 90,
                        hollow: { size: '70%' },
                        dataLabels: {
                            name: { show: false },
                            value: {
                                fontSize: '22px',
                                formatter: function(val) { return time + 's' }
                            }
                        }
                    }
                },
                labels: ['Average Shot Time'],
                title: {
                    text: 'Average Shot Time',
                    align: 'center'
                }
            };

            const chart = new ApexCharts(document.querySelector("#time-gauge-chart"), options);
            chart.render();
        }
    }
}