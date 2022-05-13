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
        install(package) { Installer.install(package, this.updatePackages) },
        uninstall(package) { Installer.uninstall(package, this.updatePackages) },

        updatePackages() {
            fetch(this.api + "/installed")
                .then(response => response.json())
                .then(data => this.installedPresentation = data);

            fetch(this.api + "/available")
                .then(response => response.json())
                .then(data => this.availablePackages = data);
        },
    }

}).mount("#appcenter");
