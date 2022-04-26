const Menu = Vue.createApp({
    name: "Menu",

    data() {
        return {
            main: null,
            isActive: false
        }
    },

    created() {
        this.main = document.getElementById('main');
        // this.isActive = true;
    },

    watch: {
        isActive(newValue, oldValue) {
            this.main.classList.toggle('menu-active', newValue);

            if (newValue) {
                this.main.addEventListener("click", this.onClickMain);
            } else {
                this.main.removeEventListener("click", this.onClickMain);
            }
        }
    },

    methods: {
        onClickMain() {
            this.isActive = false;
        }
    }

}).mount("#menu");