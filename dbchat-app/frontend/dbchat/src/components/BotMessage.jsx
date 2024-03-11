import React, { useState, useEffect } from "react";

export default function BotMessage({query, user_friendly, csv_download_link}) {
  const [isLoading, setLoading] = useState(true);
  const [message, setMessage] = useState(null); // Start with null to accommodate any type

  useEffect(() => {
    async function loadMessage() {
      console.log('BotMessage.jsx loaded...');
      setMessage({query,user_friendly,csv_download_link});
      console.log('BotMessage updated...');
      setLoading(false);
      console.log('Loading set to false...');
    }
    loadMessage();
  });


  const isWelcomeMessage = (user_friendly) => {
    console.log("isWelcomeMessage function loaded...");
    console.log("isWelcomeMessage received value:",user_friendly);
    console.log("Type of this value:",typeof user_friendly);
    console.log(user_friendly === 'Welcome to chatbot!')
    return user_friendly === 'Welcome to chatbot!';
  };

  const isLoadingMessage = (user_friendly) => {
    console.log("isLoadingMessage function loaded...");
    console.log("isLoadingMessage received value:",user_friendly);
    console.log("Type of this value:",typeof user_friendly);
    console.log(user_friendly === '...')
    return user_friendly === '...';
  };

  const isDataAvailable = (csv_download_link) => {
    console.log("isDataAvailable function loaded...");
    console.log("isDataAvailable received value",csv_download_link);
    console.log("Type of this value:",typeof csv_download_link);
    console.log(csv_download_link === '')
    return !(csv_download_link === '')
  };

  const unableToAnswer = (user_friendly) => {
    console.log("unableToAnswer function loaded...");
    console.log("unableToAnswer received value",user_friendly);
    console.log("Type of this value:",typeof user_friendly);
    console.log(user_friendly === "I can't answer with the given information. Please refine the question or tell me which tables and columns I should use to answer.")
    return user_friendly === "I can't answer with the given information. Please refine the question or tell me which tables and columns I should use to answer.";
  };

  return (
    <div className="message-container">
      {isLoading ? (
        <div className="bot-message">"..."</div>
      ) : (
        <>
          { (isWelcomeMessage(message.user_friendly)) | (unableToAnswer(message.user_friendly)) | (isLoadingMessage(message.user_friendly))? (
            <div className="bot-message">{message.user_friendly}</div>
          ) : (
            <>
                <div className="bot-message">{message.user_friendly}</div>
                <div className="bot-message">Query: {message.query}</div>
                
                {isDataAvailable(message.csv_download_link) ? (
                  <div className="bot-message">
                    <a href={message.csv_download_link} download="query-results.csv" style={{ display: "block", marginTop: "8px" }}>
                        Download CSV
                    </a>
                  </div>
                ): (<div className="bot-message">No CSV To Download...</div>)}  

            </>
          ) }
        </>
      )}
    </div>
  );
}
