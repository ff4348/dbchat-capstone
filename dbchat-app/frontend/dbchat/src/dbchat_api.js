import axios from 'axios';

const dbchat_api = axios.create({
    baseURL: 'https://localhost:8000',
});

export default dbchat_api;

// export default API;
// const API = {
//   GetChatbotResponse: async message => {
//     return new Promise(function(resolve, reject) {
//       setTimeout(function() {
//         if (message === "load welcome message") resolve("Welcome to chatbot!");
//         else resolve("echo : " + message);
//       }, 2000);
//     });
//   }
// };

// export default API;
