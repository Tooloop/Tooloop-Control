const ControlPanel = Vue.createApp({
    name: "App Center",
    delimiters: ['[[', ']]'],

    data() {
        return {
            api: '/tooloop/api/v1.0/appcenter',
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
                title: "",
                isActive: false,
                log: "",
                progress: 100,
                package: null
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
            this.showModal("Installing", package);
            fetch(this.api + "/install/" + package.packageName)
                .then(response => response.json())
                .then(data => { console.log(data) });
        },

        uninstall(package) {
            this.showModal("Uninstalling", package);
            fetch(this.api + "/uninstall/" + package.packageName)
                .then(response => response.json())
                .then(data => { console.log(data) });
        },

        showModal(title, package) {
            this.installer.isActive = true;
            this.installer.package = package;
            this.installer.progress = 0;
            this.installer.title = title + " " + package.name;
        }

    }


}).mount("#appcenter");
