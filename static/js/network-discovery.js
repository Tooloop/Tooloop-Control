const NetworkDiscovery = Vue.createApp({
    name: "Network Discovery",
    delimiters: ['[[', ']]'],

    data() {
        return {
            api: "/tooloop/api/v1.0/networkdiscovery/servers",
            servers: []
        }
    },

    created() {
        // set initial data
        this.servers = servers;

        // start polling for updates
        let controller = new AbortController();
        setInterval(() => {
            fetch(this.api, { signal: controller.signal })
                .then(response => response.json())
                .then(data => this.servers = data);
        }, 5000);
        window.onunload = function () {
            controller.abort();
        }
    },


}).mount("#network-discovery");