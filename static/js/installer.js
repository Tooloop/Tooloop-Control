const Installer = Vue.createApp({
    name: "Installer",
    delimiters: ['[[', ']]'],

    data() {
        return {
            api: '/tooloop/api/v1.0',
            isActive: false,
            progress: 0,
            isFinished: false,
            success: true,
            title: "",
            package: null,
            messages: "",
            lastMessage: "",
            progressEventSource: null,
            onFinished: null
        }
    },

    methods: {

        install(package, finishedCallback) {
            this.performInstall("install", package, finishedCallback);
        },

        uninstall(package, finishedCallback) {
            this.performInstall("uninstall", package, finishedCallback);
        },

        performInstall(method, package, finishedCallback) {
            // Reset installer states
            this.package = package;
            this.isFinished = false;
            this.success = true;
            this.progress = 0;
            this.title = this.capitalize(method) + "ing " + package.name;
            this.messages = "";
            this.lastMessage = "";
            this.onFinished = finishedCallback;

            // Show modal
            this.isActive = true;

            // Listen to progress updates
            this.progressEventSource = new EventSource(this.api + "/appcenter/progress");
            this.progressEventSource.onmessage = this.updateProgress;

            // Perform installation
            fetch(this.api + "/appcenter/" + method + "/" + package.packageName)
                .then(response => {
                    if (response.status != 200) this.success = false;
                    return response.json()
                })
                .then(data => {
                    this.finishInstallation(data.message);
                })
                .catch((error) => {
                    this.success = false;
                    this.finishInstallation(error);

                });

        },

        capitalize(s) {
            if (typeof s !== 'string') return ''
            return s.charAt(0).toUpperCase() + s.slice(1)
        },

        updateProgress(event) {
            progress = JSON.parse(event.data);
            this.progress = progress.percent;
            this.log(progress.task);
        },

        finishInstallation(message) {
            // stop listening to server events (progress)
            this.progressEventSource.close();

            // set progress states
            this.isFinished = true;
            this.progress = 100;

            // print final message
            let icon = this.success ?
                '<span class="icon has-text-success"><i class="fas fa-check"></i></span>' :
                '<span class="icon has-text-danger"><i class="fas fa-xmark"></i></span>';
            this.log(`<p class="icon-text has-text-light mt-5">${icon}${message}</p>`);

            // reload server, so the apt cache is reloaded, too
            fetch(this.api + '/reload')
                .then(response => response.json())
                .then(data => {
                    // with the new cache loaded, 
                    // call callback so the vue can reload its’ data
                    if (this.onFinished) this.onFinished();
                });
        },

        log(message) {
            if (this.lastMessage != message) {
                this.lastMessage = message;
                if (this.messages != "") this.messages += "<br>";
                this.messages += message;
                // scrolling needed to wait a little for some reason
                // maybe the DOM had to catch up to update scrollTopMax?!
                setTimeout(() => {
                    this.$refs.log.scrollTop = this.$refs.log.scrollTopMax;
                }, 16);
            }
        }

    },
    template: `
    <div class="modal" v-bind:class="{'is-active': isActive}">
        <div class="modal-background"></div>
        <div class="modal-card">
            <header class="modal-card-head">
                <p class="modal-card-title">[[title]]</p>
            </header>
            <section ref="log" class="modal-card-body has-background-dark">
                <code class="has-background-dark has-text-grey-light p-0" v-html="messages"></code>
            </section>
            <footer class="modal-card-foot">
                <div class="field is-grouped is-flex-grow-1">

                    <div class="control is-expanded is-flex is-align-items-center">
                        <progress class="progress"
                            v-bind:class="{'is-success': isFinished && success, 'is-danger': isFinished && !success}"
                            v-bind:value="progress" max="100">[[progress]]
                            %</progress>
                    </div>
                    <div class="control">
                        <button class="button" style="width: 6rem;" v-bind:class="{'is-loading': !isFinished}"
                            v-bind:disabled="!isFinished"
                            v-on:click="isActive = false">Close</button>
                    </div>
                </div>
            </footer>
        </div>
    </div>
    `

}).mount("#installer");
