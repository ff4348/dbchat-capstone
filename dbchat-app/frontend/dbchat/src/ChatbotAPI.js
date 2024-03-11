const ChatbotAPI = {
  GetChatbotResponse: async message => {
    return new Promise(async function(resolve, reject) {
      console.log("ChatBotAPI loaded...")
      setTimeout(async function() {
        if (message === "load welcome message") {
          console.log("Loading welcome message...")
          resolve("Welcome to chatbot!");
        } else {
          try {
            console.log("MESSAGE RECEIVED:",message)
            const response = await fetch('http://localhost:8000/query', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ question: message }), 
            });
            console.log("API envoked...")
            const responseData = await response.json();
            console.log("Response fetched...",responseData)
            resolve(responseData);
          } catch (error) {
            console.error('Error:', error);
            resolve("An error occurred while fetching the response."); // You can customize the error message as needed
          }
        }
      }, 2000);
    });
  }
};

export default ChatbotAPI;
