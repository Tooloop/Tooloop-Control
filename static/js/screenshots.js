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
            thumbnail: '/static/img/placeholder.png',
            thumbnailRatio: null
        }
    },

    created() {
        this.serviceRunning = screenshotServiceRunning;
        this.displayState = displayState;
        if (!this.serviceRunning) return;
        this.loadLatestThumbnail();
        setInterval(this.loadLatestThumbnail, 5000);
    },

    mounted() {
        if (!this.serviceRunning) return;
        this.$refs.thumbnail.onload = this.calculateRatio;
    },

    watch: {
        'latest.thumbnail_url': function (newValue, oldValue) {
            this.thumbnail = newValue;
        }
    },

    methods: {
        loadLatestThumbnail() {
            if (!this.serviceRunning) return;
            fetch(this.api + 'latest')
                .then(response => response.json())
                .then(data => this.latest = data);

        },

        grabScreenshot() {
            if (!this.serviceRunning) return;
            fetch(this.api + 'grab')
                .then(response => response.json())
                .then(data => this.latest = data);
        },

        calculateRatio() {
            if (!this.serviceRunning) return;
            this.thumbnailRatio = this.$refs.thumbnail.naturalWidth / this.$refs.thumbnail.naturalHeight;
        }
    },

}).mount("#screenshots");