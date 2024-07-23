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
                dataLabels: {
                    enabled: true,
                    formatter: function (val) {
                        return val.toFixed(1) + " %"
                    }
                },
                series: [],
                labels: ['Free', 'Data', 'Logs', 'Packages', 'Presentation', 'Screenshots'],
                noData: { text: 'Loading...' },
                legend: { position: 'right' },
            }
        }
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
        let controller = new AbortController();
        setInterval(() => {
            fetch(this.api, { signal: controller.signal })
                .then(response => response.json())
                .then(data => this.pushData(data));
        }, 1000);
        window.onunload = function () {
            controller.abort();
        }

    },

    methods: {
        pushData(data) {
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
                this.toGb(data.hd.size - data.hd.data - data.hd.logs - data.hd.presentation - data.hd.screenshots),
                this.toGb(data.hd.data),
                this.toGb(data.hd.logs),
                this.toGb(data.hd.packages),
                this.toGb(data.hd.presentation),
                this.toGb(data.hd.screenshots)
            ], false);
        },

        toGb(bytes) {
            return (bytes / (1000 * 1000 * 1000));
        }
    },

}).mount("#usage");