const ControlPanel = Vue.createApp({
    name: "Package Detail",
    delimiters: ['[[', ']]'],

    data() {
        return {
            api: '/tooloop/api/v1.0/appcenter/package/',
            package: null
        }
    },

    computed: {
        htmlDescription() {
            return marked.parse(this.package.description);
        }
    },

    created() {
        this.package = package;
    },

    methods: {
        install(package) {
            Installer.install(package, this.updatePackage);
        },
        uninstall(package) {
            Installer.uninstall(package, this.updatePackage);
        },

        updatePackage() {
            fetch(this.api + this.package.packageName)
                .then(response => response.json())
                .then(data => this.package = data);
        },
    }

}).mount("#package-detail");
