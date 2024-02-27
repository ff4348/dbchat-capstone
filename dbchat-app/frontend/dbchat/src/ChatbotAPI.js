import dbchat_api from './dbchat_api';

const API = {
  GetChatbotResponse: async message => {
    return new Promise(async function(resolve, reject) {
      setTimeout(async function() {
        if (message === "load welcome message") {
          resolve("Welcome to chatbot!");
        } else {
          try {
            const response = await dbchat_api.post('/query', { message });
            const responseData = response.data;

            // Extract metadata from response
            const { description, records_returned, csv_download_link } = responseData;

            // Construct the response message for the chatbot
            const responseMessage = `Description: ${description}\nRecords Returned: ${records_returned}\n\nWould you like to download the CSV data?`;

            // Construct the options for the user to download the CSV data
            const options = {
              downloadCSV: {
                label: "Download CSV",
                link: csv_download_link
              }
            };

            // Resolve with the response message and options
            resolve({ message: responseMessage, options });
          } catch (error) {
            console.error('Error:', error);
            resolve("An error occurred while fetching the response."); // You can customize the error message as needed
          }
        }
      }, 2000);
    });
  }
};

export default API;




// import dbchat_api from './dbchat_api'; 

// const API = {
//   GetChatbotResponse: async message => {
//     return new Promise(async function(resolve, reject) {
//       setTimeout(async function() {
//         if (message === "load welcome message") {
//           resolve("Welcome to chatbot!");
//         } else {
//           try {
//             const response = await dbchat_api.post('/predict', { message });
//             resolve(response.data.response); // Assuming your FastAPI returns the response in a JSON format with a key 'response'
//           } catch (error) {
//             console.error('Error:', error);
//             resolve("An error occurred while fetching the response."); // You can customize the error message as needed
//           }
//         }
//       }, 2000);
//     });
//   }
// };

// export default API;


// const API = {
//   GetChatbotResponse: async message => {
//     return new Promise(async function(resolve, reject) {
//       setTimeout(async function() {
//         try {
//           const response = await dbchat_api.post('/predict', { message });

//           // Check the content type of the response
//           const contentType = response.headers['content-type'];

//           if (contentType.includes('application/json')) {
//             // Parse JSON data
//             const responseData = await response.json();
//             resolve(responseData);
//           } else if (contentType.includes('text/html')) {
//             // Handle HTML content
//             const htmlContent = await response.text();
//             resolve(htmlContent);
//           } else if (contentType.includes('text/plain')) {
//             // Handle plain text content
//             const plainText = await response.text();
//             resolve(plainText);
//           } else if (contentType.includes('text/csv')) {
//             // Handle CSV file download
//             // You can trigger a file download here
//             resolve("CSV file download initiated...");
//           } else {
//             // Unsupported content type
//             resolve("Unsupported content type received from server");
//           }
//         } catch (error) {
//           console.error('Error:', error);
//           resolve("An error occurred while fetching the response."); // You can customize the error message as needed
//         }
//       }, 2000);
//     });
//   }
// };

// export default API;


















// import dbchat_api from "./dbchat_api";

// const API = {
//   GetChatbotResponse: async message => {
//     return new Promise(async function(resolve, reject) {
//       setTimeout(async function() {
//         if (message === "load welcome message") {
//           resolve("Welcome to chatbot!");
//         } else {
//           try {
//             const response = await fetch('http://localhost:8000/predict', {
//               method: 'POST',
//               headers: {
//                 'Content-Type': 'application/json',
//               },
//               body: JSON.stringify({ message }),
//             });
//             const response = async () => await API.GetChatbotResponse("load welcome message")
//             if (!response.ok) {
//               throw new Error('Network response was not ok');
//             }
//             const data = await response.json();
//             resolve(data.response); // Assuming your FastAPI returns the response in a JSON format with a key 'response'
//           } catch (error) {
//             console.error('Error:', error);
//             resolve("An error occurred while fetching the response."); // You can customize the error message as needed
//           }
//         }
//       }, 2000);
//     });
//   }
// };

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


