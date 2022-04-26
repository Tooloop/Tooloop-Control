const Schedule = Vue.createApp({
    name: "Schedule",
    delimiters: ['[[', ']]'],

    data() {
        return {
            api: '/tooloop/api/v1.0/system',
            weekdays: [
                { num: 1, name: "Mo" },
                { num: 2, name: "Tu" },
                { num: 3, name: "We" },
                { num: 4, name: "Th" },
                { num: 5, name: "Fr" },
                { num: 6, name: "Sa" },
                { num: 0, name: "Su" },
            ],
            schedule: {
                startup: {
                    enabled: false,
                    weekdays: [],
                    time: { hours: 8, minutes: 0 }
                },
                shutdown: {
                    enabled: false,
                    weekdays: [],
                    time: { hours: 20, minutes: 0 }
                }
            }
        }
    },

    created() {
        this.getSchedule();
    },

    mounted() {
        // let schedule = this.$refs.scheduleOnLoad.dataset.schedule;
        // console.log(schedule);
        // this.schedule = this.$refs.scheduleOnLoad.dataset.schedule;
    },

    methods: {

        pad(num, digits) {
            return String(num).padStart(digits, '0');
        },

        toggleDay(schedule, day) {
            const index = this.schedule[schedule].weekdays.indexOf(day);
            if (index > -1) {
                this.schedule[schedule].weekdays.splice(index, 1);
            } else {
                this.schedule[schedule].weekdays.push(day);
            }
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
                body: JSON.stringify(this.schedule)
            })
                .then(response => response.json())
                .then(data => {
                    this.schedule = data;
                });
        }

    },
}).mount("#schedule");