const System = Vue.createApp({
    name: "System",
    delimiters: ['[[', ']]'],

    data() {
        return {
            api: '/tooloop/api/v1.0/system',
            hostname: null,
            uptime: null,
        }
    },

    mounted() {
        // cache dom references
        this.hostname = this.$refs.hostname.dataset.hostname;

        let uptime = new Date(this.$refs.uptime.dataset.uptime);
        this.uptime = "running since " + (uptime.toDateString() == new Date().toDateString() ? "" : uptime.toLocaleDateString() + ", ") + uptime.toLocaleTimeString();
    },

    methods: {
        // getStatus() {
        //     fetch(this.api)
        //         .then(response => response.json())
        //         .then(data => {
        //             this.vnc = data.vnc;
        //             this.ssh = data.ssh;
        //             this.controlCenter = data.control_center;
        //             this.screenshots = data.screenshot_service;
        //         });
        // },

    },
}).mount("#system");