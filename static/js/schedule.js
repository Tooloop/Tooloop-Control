const Schedule = Vue.createApp({
    name: "Schedule",
    delimiters: ['[[', ']]'],

    data() {
        return {
            api: '/tooloop/api/v1.0/system',
            runtimeSchedule: {
                enabled: false,
                schedule: [
                    { num: 1, name: "Mo", startup: false, startupTime: { hours: 8, minutes: 0 }, shutdown: false, shutdownTime: { hours: 8, minutes: 0 } },
                    { num: 2, name: "Tu", startup: false, startupTime: { hours: 8, minutes: 0 }, shutdown: false, shutdownTime: { hours: 8, minutes: 0 } },
                    { num: 3, name: "We", startup: false, startupTime: { hours: 8, minutes: 0 }, shutdown: false, shutdownTime: { hours: 8, minutes: 0 } },
                    { num: 4, name: "Th", startup: false, startupTime: { hours: 8, minutes: 0 }, shutdown: false, shutdownTime: { hours: 8, minutes: 0 } },
                    { num: 5, name: "Fr", startup: false, startupTime: { hours: 8, minutes: 0 }, shutdown: false, shutdownTime: { hours: 8, minutes: 0 } },
                    { num: 6, name: "Sa", startup: false, startupTime: { hours: 8, minutes: 0 }, shutdown: false, shutdownTime: { hours: 8, minutes: 0 } },
                    { num: 0, name: "Su", startup: false, startupTime: { hours: 8, minutes: 0 }, shutdown: false, shutdownTime: { hours: 8, minutes: 0 } }
                ]
            }
        }
    },

    created() {
        this.runtimeSchedule = runtimeSchedule;
    },

    methods: {

        pad(num, digits) {
            return String(num).padStart(digits, '0');
        },

        getSchedule() {
            fetch(this.api + '/runtimeschedule')
                .then(response => response.json())
                .then(data => {
                    this.schedule = data;
                });
        },

        saveSchedule() {
            fetch(this.api + '/runtimeschedule', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.runtimeSchedule)
            })
                .then(response => response.json())
                .then(data => {
                    this.runtimeSchedule = data;
                });
        }

    },
}).mount("#schedule");