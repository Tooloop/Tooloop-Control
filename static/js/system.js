const System = Vue.createApp({
    name: "System",
    delimiters: ['[[', ']]'],

    data() {
        return {
            api: '/tooloop/api/v1.0/system',
            hostname: null,
            uptime: null,
            timezone: null,
            oldPassword: "",
            newPassword: "",
            repeatNewPassword: "",
        }
    },

    created() {
        this.hostname = hostname;
        this.uptime = uptime;
        this.timezone = timezone;
    },

    computed: {
        uptimeString() {
            let uptimeDate = new Date(this.uptime);
            return "running since " + (uptimeDate.toDateString() == new Date().toDateString() ? "" : uptimeDate.toLocaleDateString() + ", ") + uptimeDate.toLocaleTimeString();
        }
    },

    methods: {

        saveHostname() {
            fetch(this.api + '/hostname', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ "hostname": this.hostname })
            })
                .then(response => response.json())
                .then(data => {
                    this.hostname = data.hostname;
                });
        },

        savePassword() {
            if (this.oldPassword == "" || this.newPassword == "" || this.repeatNewPassword == "") {
                alert("Please fill all fields.");
                return;
            }

            if (this.newPassword != this.repeatNewPassword) {
                alert("New passwords don’t match.")
                return;
            }

            fetch(this.api + '/password', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ "oldPassword": this.oldPassword, "newPassword": this.newPassword })
            })
                .then(response => console.log(response))
                // .then(response => response.json())
                .then(data => {
                })
                .catch(error => {
                    console.error(error);
                });
        },

        getUptime() {
            fetch(this.api + '/uptime')
                .then(response => response.json())
                .then(data => {
                    this.uptime = data.uptime;
                });
        },

        saveTimezone() {
            fetch(this.api + '/timezone', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ "timezone": this.timezone })
            })
                .then(response => response.json())
                .then(data => {
                    this.timezone = data.timezone;
                    // let some time pass so the uptime is calculated correctly
                    setTimeout(this.getUptime, 500);
                });
        },

    },
}).mount("#system");