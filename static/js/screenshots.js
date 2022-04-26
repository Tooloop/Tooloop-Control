const Screenshots = Vue.createApp({
    name: "Screenshots",
    delimiters: ['[[', ']]'],

    data() {
        return {
            api: '/tooloop/api/v1.0/screenshot/',
            modalActive: false,
            serviceRunning: true,
            displayState: 'on',
            latest: {},
            thumbnail: '/static/img/placeholder.png'
        }
    },

    created() {
        this.loadLatestThumbnail();
        setInterval(this.loadLatestThumbnail, 5000);
    },

    mounted() {
        this.displayState = this.$refs.root.dataset.displaystate;
        this.serviceRunning = JSON.parse(this.$refs.root.dataset.servicerunning.toLowerCase());
    },

    watch: {
        'latest.thumbnail_url': function (newValue, oldValue) {
            this.thumbnail = newValue;
        }
    },

    methods: {
        loadLatestThumbnail() {
            fetch(this.api + 'latest')
                .then(response => response.json())
                .then(data => this.latest = data);

        },

        grabScreenshot() {
            fetch(this.api + 'grab')
                .then(response => response.json())
                .then(data => this.latest = data);
        },
    },

}).mount("#screenshots");