const Services = Vue.createApp({
    name: "Services",
    delimiters: ['[[', ']]'],

    data() {
        return {
            api: '/tooloop/api/v1.0/services',
            vnc: true,
            ssh: true,
            controlCenter: true,
            screenshots: true
        }
    },

    created() {
        this.setServices(services);
    },

    methods: {
        getStatus() {
            fetch(this.api)
                .then(response => response.json())
                .then(data => {
                    this.setServices(data);
                });
        },

        setServices(services) {
            this.vnc = services.vnc;
            this.ssh = services.ssh;
            this.controlCenter = services.control_center;
            this.screenshots = services.screenshot_service;
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