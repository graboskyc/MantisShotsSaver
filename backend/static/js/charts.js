function init() {
    // Gauge configuration: each scope (all time / last N) gets accuracy, shot time,
    // and holster-only shot time gauges. Query params map to the generic endpoints.
    const scopes = [
        { suffix: '', label: 'All Time', params: '' },
        { suffix: 'last50', label: 'Last 50 Sess', params: '?last=50' },
        { suffix: 'last10', label: 'Last 10 Sess', params: '?last=10' },
    ];

    const gaugeGroups = scopes.map(scope => ({
        title: `Accuracy and Time (${scope.label})`,
        gauges: [
            { id: `gauge-chart${scope.suffix ? '-' + scope.suffix : ''}`, type: 'accuracy', title: `Avg Accuracy (${scope.label})`, url: `/api/stats/average-accuracy${scope.params}` },
            { id: `time-gauge-chart${scope.suffix ? '-' + scope.suffix : ''}`, type: 'time', title: `Avg Shot Time (${scope.label})`, url: `/api/stats/average-shot-time${scope.params}` },
            { id: `time-gauge-chart-holster${scope.suffix ? '-' + scope.suffix : ''}`, type: 'time', title: `Avg Shot Time (Holster, ${scope.label})`, url: `/api/stats/average-shot-time${scope.params ? scope.params + '&' : '?'}drill=holster` },
        ]
    }));

    return {
        gaugeGroups,

        async loadList() {
            const response = await fetch(`/api/stats/shots-over-time`);
            const data = await response.json();
            this.renderChart(data);

            const sessionResponse = await fetch(`/api/stats/session-scores`);
            const sessionData = await sessionResponse.json();
            this.renderCandlestickChart(sessionData);

            await this.renderGauges();

            const distData = await (await fetch(`/api/stats/shot-distribution`)).json();
            this.renderDistributionChart(distData);

            const distLast10Data = await (await fetch(`/api/stats/shot-distribution-last10`)).json();
            this.renderDistributionChartLast10(distLast10Data);

            const consData = await (await fetch(`/api/stats/shot-consistency`)).json();
            this.renderConsistencyChart(consData);

            const drillData = await (await fetch(`/api/stats/drill-performance`)).json();
            this.renderDrillChart(drillData);

            const corrData = await (await fetch(`/api/stats/time-accuracy-correlation`)).json();
            this.renderCorrelationChart(corrData);
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

        async renderGauges() {
            // Wait for Alpine to render the template-driven gauge divs
            await this.$nextTick();
            await Promise.all(this.gaugeGroups.flatMap(group =>
                group.gauges.map(async gauge => {
                    const result = await (await fetch(gauge.url)).json();
                    if (gauge.type === 'accuracy') {
                        this.renderAccuracyGaugeInto(gauge.id, result.accuracy, gauge.title);
                    } else {
                        this.renderTimeGaugeInto(gauge.id, result.time, gauge.title);
                    }
                })
            ));
        },

        renderAccuracyGaugeInto(id, accuracy, title) {
            const color = accuracy >= 100 ? '#800080' : accuracy < 80 ? '#FF0000' : accuracy <= 90 ? '#FFB200' : '#00A100';
            const options = {
                chart: {
                    type: 'radialBar',
                    height: 350
                },
                colors: [color],
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
                labels: [title],
                title: {
                    text: title,
                    align: 'center'
                }
            };

            new ApexCharts(document.querySelector(`#${id}`), options).render();
        },

        renderTimeGaugeInto(id, time, title) {
            new ApexCharts(document.querySelector(`#${id}`), this.buildTimeGaugeOptions(time, title)).render();
        },

        buildTimeGaugeOptions(time, title) {
            const clamped = Math.max(0, Math.min(time, 5));
            return {
                series: [clamped],
                chart: {
                    height: 350,
                    type: 'gauge',
                },
                plotOptions: {
                    radialBar: {
                        shape: 'needle',
                        startAngle: -90,
                        endAngle: 90,
                        min: 0,
                        max: 5,
                        bands: [
                            { from: 0,    to: 1.5,  color: '#00A100' },
                            { from: 1.5,  to: 2.25, color: '#FFB200' },
                            { from: 2.25, to: 3,    color: '#FF7F00' },
                            { from: 3,    to: 5,    color: '#FF0000' },
                        ],
                        ticks: {
                            show: true,
                            major: {
                                count: 5,
                                length: 8,
                                width: 2,
                                color: '#334155',
                                placement: 'outside',
                            },
                            minor: {
                                count: 0,
                            },
                            labels: {
                                show: true,
                                offset: 6,
                                fontSize: '11px',
                                color: '#334155',
                                formatter: function(val) { return Number(val).toFixed(2); },
                            },
                        },
                        needle: {
                            color: '#0F172A',
                            length: '60%',
                            baseWidth: 6,
                            tipWidth: 1,
                        },
                        hollow: {
                            margin: 0,
                            size: '70%',
                        },
                        dataLabels: {
                            name: { show: false },
                            value: {
                                offsetY: 32,
                                fontSize: '28px',
                                fontWeight: 700,
                                formatter: function() { return time + 's' },
                            },
                        },
                    },
                },
                labels: ['Avg Shot Time'],
                title: { text: title, align: 'center' },
                responsive: [
                    {
                        breakpoint: 576,
                        options: {
                            chart: { height: 300 },
                            plotOptions: {
                                radialBar: {
                                    dataLabels: {
                                        value: { offsetY: 10, fontSize: '22px' },
                                    },
                                    ticks: {
                                        labels: { fontSize: '9px', offset: 2 },
                                    },
                                },
                            },
                        },
                    },
                ],
            };
        },

        renderDistributionChart(data) {
            this.renderDistributionChartInto("#distribution-chart", data, 'Shot Distribution');
        },

        renderDistributionChartLast10(data) {
            this.renderDistributionChartInto("#distribution-chart-last10", data, 'Shot Distribution (Last 20)');
        },

        renderDistributionChartInto(selector, data, title) {
            // Group data for heatmap format
            const xCoords = [...new Set(data.map(d => d.x))].sort((a,b) => a-b);
            const yCoords = [...new Set(data.map(d => d.y))].sort((a,b) => a-b);
            const series = yCoords.map(y => ({
                name: y.toString(),
                data: xCoords.map(x => {
                    const item = data.find(d => d.x === x && d.y === y);
                    return { x: x.toString(), y: item ? item.count : 0 };
                })
            }));

            var ranges = [
                { from: 0, to: 5, name: 'Very Low', color: '#006400' },
                { from: 6, to: 15, name: 'Low', color: '#00A100' },
                { from: 16, to: 30, name: 'Moderate', color: '#128FD9' },
                { from: 31, to: 60, name: 'High', color: '#FFB200' },
                { from: 61, to: 100, name: 'Very High', color: '#FF4500' },
                { from: 101, to: 1000, name: 'Extreme', color: '#800080' }
            ];

            if (title.includes('Last 20')) {
                ranges = [
                    { from: 0, to: 2, name: 'Very Low', color: '#006400' },
                    { from: 3, to: 5, name: 'Low', color: '#00A100' },
                    { from: 6, to: 10, name: 'Moderate', color: '#128FD9' },
                    { from: 11, to: 15, name: 'High', color: '#FFB200' },
                    { from: 16, to: 20, name: 'Very High', color: '#FF4500' },
                    { from: 21, to: 1000, name: 'Extreme', color: '#800080' }
                ];
            }

            const options = {
                chart: { type: 'heatmap', height: 600, toolbar: { show: false } },
                series: series,
                plotOptions: {
                    heatmap: {
                        shape: 'hexagon',
                        enableShades: true,
                        shadeIntensity: 0.5,
                        distributed: false,
                        colorScale: {
                            ranges: ranges
                        }
                    }
                },
                stroke: { width: 2, colors: ['#fff'] },
                title: { text: title, align: 'center' }
            };
            new ApexCharts(document.querySelector(selector), options).render();
        },

        renderConsistencyChart(data) {
            const options = {
                chart: { type: 'area', height: 350, toolbar: { show: false } },
                series: [{ name: 'Avg Score', data: data.map(d => d.avg_score) }],
                dataLabels: {
                    enabled: true,
                    formatter: function(val) { return val.toFixed(1); },
                    style: { colors: ['#000000'] }
                },
                xaxis: { categories: data.map(d => d.date) },
                yaxis: {
                    labels: {
                        formatter: function(val) { return val.toFixed(1); }
                    }
                },
                title: { text: 'Shot Consistency (Avg Score)', align: 'center' }
            };
            new ApexCharts(document.querySelector("#consistency-chart"), options).render();
        },

        renderDrillChart(data) {
            const options = {
                chart: { type: 'bar', height: 350, toolbar: { show: false } },
                series: [{ name: 'Avg Score', data: data.map(d => d.avg_score) }],
                dataLabels: {
                    enabled: true,
                    formatter: function(val) { return val.toFixed(1); },
                    style: { colors: ['#000000'] }
                },
                xaxis: { 
                    categories: data.map(d => d.drill),
                    labels: { rotate: -45 }
                },
                yaxis: {
                    labels: {
                        formatter: function(val) { return val.toFixed(1); }
                    }
                },
                title: { text: 'Drill Performance (Avg Score)', align: 'center' }
            };
            new ApexCharts(document.querySelector("#drill-chart"), options).render();
        },

        renderCorrelationChart(data) {
            // Group data for heatmap format: x = Time (steps of 0.5s), y = Score
            const xCoords = [...new Set(data.map(d => d.x))].sort((a,b) => a-b);
            const yCoords = [...new Set(data.map(d => d.y))].sort((a,b) => b-a); // Score descending
            const series = yCoords.map(y => ({
                name: y.toString(),
                data: xCoords.map(x => {
                    const item = data.find(d => d.x === x && d.y === y);
                    return { x: (x / 2).toFixed(1) + 's', y: item ? item.count : 0 };
                })
            }));

            const options = {
                chart: { type: 'heatmap', height: 350, toolbar: { show: false } },
                series: series,                
                xaxis: { title: { text: 'Time (s)' } },                
                plotOptions: {
                    heatmap: {
                        enableShades: true,
                        shadeIntensity: 0.5,
                        colorScale: {
                            ranges: [{ from: 0, to: 5, name: 'Low', color: '#00A100' },
                                     { from: 6, to: 15, name: 'Medium', color: '#128FD9' },
                                     { from: 16, to: 1000, name: 'High', color: '#FFB200' }]
                        }
                    }
                },
                title: { text: 'Time vs Accuracy (Heatmap)', align: 'center' }
            };
            new ApexCharts(document.querySelector("#correlation-chart"), options).render();
        }
    }
}