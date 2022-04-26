const ControlPanel = Vue.createApp({
    name: "Control Panel",
    delimiters: ['[[', ']]'],

    data() {
        return {
            api: '/tooloop/api/v1.0/',
            displayState: true,
            audio: {
                volume: 100,
                enabled: true
            },
            modal: null
        }
    },

    mounted() {
        this.displayState = this.$refs.displaySwitch.dataset.state.toLowerCase() == 'on';
        this.audio.enabled = !JSON.parse(this.$refs.muteSwitch.dataset.mute.toLowerCase());
        this.audio.volume = parseInt(this.$refs.volumeSlider.dataset.volume);
        this.modal = document.getElementById('modal');
    },

    watch: {
        'audio.enabled': function () {
            this.setAudioMute(!this.audio.enabled);
        },
        
        'audio.volume': function (newValue, oldValue) {
            this.setAudioVolume(newValue);
        },

        displayState(newState, oldState) {
            this.setDisplayState(newState ? 'on' : 'off');
        }

    },

    methods: {
        poweroff() {
            if (confirm("Are you sure, you want to power off the machine?")) {
                fetch(this.api + 'system/poweroff');
                this.modal.classList.toggle('is-active', true);
            }
        },

        reboot() {
            if (confirm("Are you sure, you want to power off the machine?")) {
                fetch(this.api + 'system/reboot');
                this.modal.classList.toggle('is-active', true);
            }
        },

        startPresentation() {
            fetch(this.api + 'presentation/start')
                .then((respone) => {
                    setTimeout(Screenshots.grabScreenshot, 1000);
                    setTimeout(Screenshots.grabScreenshot, 3000);
                    setTimeout(Screenshots.grabScreenshot, 5000);
                });
        },

        stopPresentation() {
            fetch(this.api + 'presentation/stop')
                .then((respone) => setTimeout(Screenshots.grabScreenshot, 1000));
        },

        setDisplayState(state) {
            this.putData(this.api + 'system/displaystate', { state: state })
            .then(data => this.displayState = data.state.toLowerCase() == 'on');
        },

        setAudioMute(mute) {
            this.putData(this.api + 'system/audiomute', { mute: mute })
                .then(data => this.audio.enabled = !data.mute);
        },

        onAudioMute() {
            // this.setAudioMute()
            console.log(this.audio.enabled);
        },

        setAudioVolume(volume) {
            this.putData(this.api + 'system/audiovolume', { volume: volume })
                // .then(data => this.audio.volume = data.volume);
        },

        async putData(uri, data) {
            const response = await fetch(uri, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            return response.json();

        }
    },

}).mount("#control-panel");