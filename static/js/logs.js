const Logs = Vue.createApp({
    name: "Logs",
    delimiters: ['[[', ']]'],

    data() {
        return {
            api: '/tooloop/api/v1.0/logs',
            selected: null,
            logContent: null,
            logs: [],
            tail: true
        }
    },

    created() {
        if (Array.isArray(logData)) {
            this.logs = logData;
        }

        this.selected = this.logs[0];
        setInterval(() => { this.load(this.selected) }, 5000);
    },

    watch: {
        selected(newFile, oldFile) {
            this.load(newFile);
        },

        tail(newValue, oldValue) {
            if (newValue) {
                this.scrollDown();
            }
        }
    },

    methods: {
        load(filename) {
            fetch(this.api + "/" + filename)
                .then(response => response.json())
                .then(data => {
                    this.logContent = data;
                    if (this.tail) {
                        // wait a frame until the DOM elements scrollTopMax 
                        // was adjusted after changing the text content
                        window.requestAnimationFrame(this.scrollDown);
                    }
                });
        },

        scrollDown() {
            this.$refs.logContent.scrollTo(0, this.$refs.logContent.scrollTopMax);
        },

        async copyToClipboard() {
            try {
                await navigator.clipboard.writeText(this.logContent);
            } catch (error) {
                console.error(error.message);
            }
        },

        download() {
            if (!this.selected) return;

            document.location = this.api + "/download/" + this.selected;
        }
    },
}).mount("#logs");