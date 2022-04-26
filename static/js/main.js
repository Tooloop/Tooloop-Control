// var TooloopControl = Vue.createApp({
//     name: "Tooloop Control",

//     data() {
//         return {
//         }
//     }
    
// }).mount("#app");h



//     el: '#app',
//     delimiters: ['[[', ']]'],
//     data: {
//         status: {},
//     },
//     mounted: function () {
//         // status
//         this.getStatus();
//         setInterval(this.getStatus, 5000);
//     },
//     updated: function () {
//     },
//     watch: {
//     },
//     methods: {
//         getStatus() {
//             fetch("/status")
//                 .then(response => response.json())
//                 .then(response => {
//                     this.status = response;
//                 })
//                 .catch(error => console.error(error));
//         },
//     }
// });
