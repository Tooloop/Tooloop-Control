const ControlPanel = Vue.createApp({
    name: "App Center",
    delimiters: ['[[', ']]'],

    data() {
        return {
            api: '/tooloop/api/v1.0',
            installedPresentation: null,
            availablePackages: [],
            sections: [
                { id: 'tooloop/addon', name: 'Addons' },
                { id: 'tooloop/presentation', name: 'Presentations' },
            ],
            filter: {
                sections: ['tooloop/addon', 'tooloop/presentation'],
                installedOnly: false,
                query: ""
            },
            installer: {
                isActive: false,
                progress: 0,
                isFinished: false,
                success: true,
                title: "",
                package: null,
                log: "",
                lastMessage: "",
                progressEventSource: null,
            }
        }
    },

    computed: {
        filteredPackages() {
            let filtersPackages = this.availablePackages;

            // fuzzy search for query
            if (this.filter.query !== "") {
                const results = fuzzysort.go(this.filter.query, this.availablePackages, { keys: ['name', 'summary'] });
                filtersPackages = results.map((result) => result.obj);
            }

            // filter
            filtersPackages = filtersPackages.filter((package) => {
                // by type
                let isInSections = this.filter.sections.includes(package.section);
                // is installed
                let isInstalled = this.filter.installedOnly ? package.isInstalled : true;

                return isInSections && isInstalled;
            });

            return filtersPackages;
        },
    },

    created() {
        this.installedPresentation = installedPresentation;
        this.availablePackages = availablePackages;
    },

    mounted() {
        console.log(this.$refs.log);
    },

    methods: {

        install(package) {
            this.performInstall("install", package);

        },

        uninstall(package) {
            this.performInstall("uninstall", package);
        },

        performInstall(method, package) {
            // Reset installer states
            this.installer.package = package;
            this.installer.isFinished = false;
            this.installer.success = true;
            this.installer.progress = 0;
            this.installer.title = this.capitalize(method) + "ing " + package.name;
            this.installer.log = "";
            this.installer.lastMessage = "";

            // Show modal
            this.installer.isActive = true;

            // Perform installation
            fetch(this.api + "/appcenter/" + method + "/" + package.packageName)
                .then(response => {
                    if (response.status != 200) this.installer.success = false;
                    return response.json()
                })
                .then(data => { this.finishInstallation(data.message) })
                .catch((error) => {
                    this.installer.success = false;
                    this.finishInstallation(error);
                });

            // Listen to progress updates
            this.installer.progressEventSource = new EventSource("/tooloop/api/v1.0/appcenter/progress");
            this.installer.progressEventSource.onmessage = this.updateProgress;
        },

        capitalize(s) {
            if (typeof s !== 'string') return ''
            return s.charAt(0).toUpperCase() + s.slice(1)
        },

        updatePackages() {
            fetch(this.api + '/reload')
                .then(response => response.json())
                .then(data => {
                    fetch(this.api + "/appcenter/installed")
                        .then(response => response.json())
                        .then(data => this.installedPresentation = data);

                    fetch(this.api + "/appcenter/available")
                        .then(response => response.json())
                        .then(data => this.availablePackages = data);
                });
        },

        updateProgress(event) {
            progress = JSON.parse(event.data);
            this.installer.progress = progress.percent;
            this.log(progress.task);

        },

        finishInstallation(message) {
            this.installer.progressEventSource.close();
            this.installer.isFinished = true;
            this.installer.progress = 100;

            let icon = this.installer.success ?
                '<span class="icon has-text-success"><i class="fas fa-check"></i></span>' :
                '<span class="icon has-text-danger"><i class="fas fa-xmark"></i></span>';

            this.log(`<p class="icon-text has-text-light mt-5">${icon}${message}</p>`);

            this.updatePackages();
        },

        log(message) {
            if (this.installer.lastMessage != message) {
                this.installer.lastMessage = message;
                if (this.installer.log != "") this.installer.log += "<br>";
                this.installer.log += message;
                // scrolling needed to wait a little for some reason
                // maybe the DOM had to catch up to update scrollTopMax?!
                setTimeout(() => {
                    this.$refs.log.scrollTop = this.$refs.log.scrollTopMax;
                }, 16);
            }
        }

    }


}).mount("#appcenter");
