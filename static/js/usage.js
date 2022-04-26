const Usage = Vue.createApp({
    name: "Usage",

    data() {
        return {
            api: '/tooloop/api/v1.0/system/usage',
            maxLength: 2 * 1 * 60,
            cpuUsage: [],
            cpuUsageChart: null,
            cpuTemperature: [],
            cpuTemperatureChart: null,
            memoryUsage: [],
            memoryUsageChart: null,

            lineChartOptions: {
                chart: {
                    type: 'line',
                    toolbar: {
                        show: false
                    },
                    height: '240px',
                    animations: {
                        enabled: true,
                        easing: 'linear',
                        dynamicAnimation: {
                            speed: 1000
                        }
                    }
                },
                stroke: {
                    // colors: ['#e5017b'],
                    width: 1,
                    curve: 'smooth',
                },
                series: [],
                xaxis: {
                    type: "datetime",
                    range: 1 * 60 * 1000 // 5 minutes
                },
                yaxis: {
                    min: 0,
                    max: 100,
                    labels: {
                        formatter: function (value) {
                            return value.toFixed(0);
                        }
                    },
                },
                noData: { text: 'Loading...' },
                legend: { position: 'right' },
            },
            donutChartOptions: {
                chart: {
                    type: 'donut',
                    toolbar: {
                        show: false
                    },
                    height: '240px',
                },
                series: [],
                labels: ['Free', 'Data', 'Logs', 'Packages', 'Presentation', 'Screenshots'],
                noData: { text: 'Loading...' },
                legend: { position: 'right' },
            }
        }
    },

    created() {
    },

    mounted() {
        // =====================================================================
        // Init graphs
        // =====================================================================
        this.cpuUsageChart = new ApexCharts(this.$refs.cpuUsage, this.lineChartOptions);
        this.cpuUsageChart.render();

        this.cpuTemperatureChart = new ApexCharts(this.$refs.cpuTemperature, this.lineChartOptions);
        this.cpuTemperatureChart.render();
        this.cpuTemperatureChart.updateOptions({
            yaxis: {
                min: 20,
                max: 100,
                labels: {
                    formatter: function (value) {
                        return value.toFixed(0);
                    }
                },
            }
        })

        this.memoryUsageChart = new ApexCharts(this.$refs.memoryUsage, this.lineChartOptions);
        this.memoryUsageChart.render();

        this.hdUsageChart = new ApexCharts(this.$refs.hdUsage, this.donutChartOptions);
        this.hdUsageChart.render();

        // =====================================================================
        // Update data
        // =====================================================================
        setInterval(() => {
            fetch(this.api)
                .then(response => response.json())
                .then((data) => {
                    // ---------------------------------------------------------
                    // CPU usage
                    // ---------------------------------------------------------
                    let i = 0;
                    for (const core in data.cpu.usage_percent) {

                        // create empty series for each core
                        if (!this.cpuUsage[i]) {
                            this.cpuUsage.push({
                                name: core,
                                data: []
                            });
                        }

                        // add new data
                        this.cpuUsage[i].data.push({
                            x: data.cpu.timestamp,
                            y: data.cpu.usage_percent[core]
                        });

                        if (this.cpuUsage[i].length >= this.maxLength) {
                            this.cpuUsage[i] = this.cpuUsage[i].slice(this.cpuUsage[i].length / 2, -1);
                        }

                        i++;
                    }
                    this.cpuUsageChart.updateSeries(this.cpuUsage);

                    // ---------------------------------------------------------
                    // CPU temperature
                    // ---------------------------------------------------------
                    this.cpuTemperature.push({
                        x: data.cpu.timestamp,
                        y: data.cpu.temperature
                    });

                    if (this.cpuTemperature.length >= this.maxLength) {
                        this.cpuTemperature = this.cpuTemperature.slice(this.cpuTemperature.length / 2, -1);
                    }
                    this.cpuTemperatureChart.updateSeries([{
                        data: this.cpuTemperature
                    }]);

                    // ---------------------------------------------------------
                    // Memory usage
                    // ---------------------------------------------------------
                    this.memoryUsage.push({
                        x: data.memory.timestamp,
                        y: data.memory.usage_percent
                    });

                    if (this.memoryUsage.length >= this.maxLength) {
                        this.memoryUsage = this.memoryUsage.slice(this.memoryUsage.length / 2, -1);
                    }
                    this.memoryUsageChart.updateSeries([{
                        data: this.memoryUsage
                    }]);

                    // ---------------------------------------------------------
                    // HD usage
                    // ---------------------------------------------------------
                    this.hdUsageChart.updateSeries([
                        105089261568, // "free"
                        4096, // "data"
                        4096, // "logs"
                        4096, // "packages"
                        12288, // "presentation"
                        352727040  // "screenshots"
                    ], false);
                });
        }, 1000);
    },

}).mount("#usage");