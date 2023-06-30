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
        this.loadLatestThumbnail();
        setInterval(this.loadLatestThumbnail, 5000);
        this.displayState = displayState;
        this.serviceRunning = screenshotServiceRunning;
    },

    mounted() {
        this.$refs.thumbnail.onload = this.calculateRatio;
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

        calculateRatio() {
            this.thumbnailRatio = this.$refs.thumbnail.naturalWidth / this.$refs.thumbnail.naturalHeight;
        }
    },

}).mount("#screenshots");