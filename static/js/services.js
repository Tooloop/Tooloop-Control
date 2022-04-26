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
            var command = this.vnc ? 'enable' : 'disable';
            fetch(this.api + '/vnc/' + command)
                .then(response => response.json())
                .then(this.getStatus);
        },

        setSsh() {
            if (!this.ssh) {
                if (!confirm('Are you sure?\nYou might need to have physical access to switch SSH back on.')) {
                    this.ssh = true;
                    return;
                }
            }
            var command = this.ssh ? 'enable' : 'disable';
            fetch(this.api + '/ssh/' + command)
                .then(response => response.json())
                .then(this.getStatus);
        },

        setControlCenter() {
            if (!this.controlCenter) {
                if (!confirm('Are you sure?\nYou might need to have physical access to switch the Control Center back on.')) {
                    this.controlCenter = true;
                    return;
                }
            }
            var command = this.controlCenter ? 'enable' : 'disable';
            fetch(this.api + '/controlcenter/' + command)
                .then(response => response.json())
                .then(this.getStatus);
        },

        setScreenshots() {
            var command = this.screenshots ? 'enable' : 'disable';
            fetch(this.api + '/screenshots/' + command)
                .then(response => response.json())
                .then(this.getStatus);
        },
    },
}).mount("#services");