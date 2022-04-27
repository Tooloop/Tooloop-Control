const System = Vue.createApp({
    name: "System",
    delimiters: ['[[', ']]'],

    data() {
        return {
            api: '/tooloop/api/v1.0/system',
            hostname: null,
            uptime: null,
            oldPassword: "",
            newPassword: "",
            repeatNewPassword: "",
        }
    },

    mounted() {
        // cache dom references
        this.hostname = this.$refs.hostname.dataset.hostname;

        let uptime = new Date(this.$refs.uptime.dataset.uptime);
        this.uptime = "running since " + (uptime.toDateString() == new Date().toDateString() ? "" : uptime.toLocaleDateString() + ", ") + uptime.toLocaleTimeString();
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
        }

    },
}).mount("#system");