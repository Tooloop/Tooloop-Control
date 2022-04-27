const Services = Vue.createApp({
    name: "Services",
    delimiters: ['[[', ']]'],

    data() {
        return {
            api: '/tooloop/api/v1.0/services',
            vnc: true,
            ssh: true,
            controlCenter: true,
            screenshots: false
        }
    },

    mounted() {
        this.vnc = JSON.parse(this.$refs.vncSwitch.dataset.state.toLowerCase());
        this.ssh = JSON.parse(this.$refs.sshSwitch.dataset.state.toLowerCase());
        this.controlCenter = JSON.parse(this.$refs.controlCenterSwitch.dataset.state.toLowerCase());
        this.screenshots = JSON.parse(this.$refs.screenshotsSwitch.dataset.state.toLowerCase());
    },

    methods: {
        getStatus() {
            fetch(this.api)
                .then(response => response.json())
                .then(data => {
                    this.vnc = data.vnc;
                    this.ssh = data.ssh;
                    this.controlCenter = data.control_center;
                    this.screenshots = data.screenshot_service;
                });
        },

        setVnc() {
            fetch(this.api + '/vnc', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ "vnc": this.vnc })
            })
                .then(response => response.json())
                .then(data => {
                    this.vnc = data.vnc;
                });
        },

        setSsh() {
            fetch(this.api + '/ssh', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ "ssh": this.ssh })
            })
                .then(response => response.json())
                .then(data => {
                    this.ssh = data.ssh;
                });
        },

        setControlCenter() {
            if (!this.controlCenter) {
                if (!confirm('Are you sure?\nThis will disable network access to the Control Center. You will need physical access to the machine to turn it back on.')) {
                    this.controlCenter = true;
                    return;
                }
            }
            fetch(this.api + '/controlcenter', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ "control_center": this.controlCenter })
            })
                .then(response => response.json())
                .then(data => {
                    this.controlCenter = data.control_center;
                });
        },

        setScreenshots() {
            fetch(this.api + '/screenshots', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ "screenshot_service": this.screenshots })
            })
                .then(response => response.json())
                .then(data => {
                    this.screenshots = data.screenshot_service;
                });
        },
    },
}).mount("#services");