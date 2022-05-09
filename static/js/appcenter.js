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
                title: "",
                package: null,
                log: "",
                lastMessage: "",
                progressEventSource: null
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

    methods: {

        install(package) {
            // Show modal
            this.showModal("Installing", package);

            // Trigger installation
            fetch(this.api + "/appcenter/install/" + package.packageName)
                .then(response => response.json())
                .then(data => { this.finishInstallation(data.message) });

            // Listen to progress updates
            this.installer.progressEventSource = new EventSource("/tooloop/api/v1.0/appcenter/progress");
            this.installer.progressEventSource.onmessage = this.updateProgress;
        },

        uninstall(package) {
            // Show modal
            this.showModal("Uninstalling", package);

            // Trigger uninstallation
            fetch(this.api + "/appcenter/uninstall/" + package.packageName)
                .then(response => response.json())
                .then(data => { this.finishInstallation(data.message) });

            // Listen to progress updates
            this.installer.progressEventSource = new EventSource("/tooloop/api/v1.0/appcenter/progress");
            this.installer.progressEventSource.onmessage = this.updateProgress;
        },

        updatePackages() {
            fetch(this.api + '/reload')
                .then(response => response.json())
                .then(data => {
                    console.log(data.message)

                    fetch(this.api + "/appcenter/installed")
                        .then(response => response.json())
                        .then(data => this.installedPresentation = data);

                    fetch(this.api + "/appcenter/available")
                        .then(response => response.json())
                        .then(data => this.availablePackages = data);
                });
        },

        showModal(title, package) {
            this.installer.package = package;
            this.installer.isFinished = false;
            this.installer.progress = 0;
            this.installer.title = title + " " + package.name;
            this.installer.log = "";
            this.installer.lastMessage = "";
            this.installer.isActive = true;
        },

        updateProgress(event) {
            progress = JSON.parse(event.data);
            this.installer.progress = progress.percent;

            if (this.installer.lastMessage != progress.task) {
                this.installer.lastMessage = progress.task;
                this.installer.log += "\n" + progress.task;
            }
        },

        finishInstallation(message) {
            this.installer.progressEventSource.close();
            this.installer.log += "\n\n" + message;
            this.installer.isFinished = true;

            this.updatePackages();
        },

    }


}).mount("#appcenter");
