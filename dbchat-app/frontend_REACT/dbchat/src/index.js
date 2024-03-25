import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom";

import BotMessage from "./components/BotMessage";
import UserMessage from "./components/UserMessage";
import Messages from "./components/Messages";
import Input from "./components/Input";

import ChatbotAPI from "./ChatbotAPI";

import "./styles.css";
import Header from "./components/Header";

let messageId = 0;

function Chatbot() {
  console.log("DB Chatbot loaded...");

  const [messages, setMessages] = useState([]);
  console.log("Messages state is set...",messages);

  const timestamp = Date.now();
  console.log("Set timestamp for key...",timestamp);

  useEffect(() => {
    async function loadWelcomeMessage() {
      console.log("Load welcome message hook loaded...");
      const welcomeMessage = await ChatbotAPI.GetChatbotResponse("load welcome message");
      console.log("Welcome message retrieved from API...",welcomeMessage);
      messageId += 1;
      console.log("Load message unique key:",`bot-${timestamp+messageId}-${messageId}`);
      setMessages([{ 
        key: `bot-${timestamp+messageId}-${messageId}`, 
        type: 'bot', 
        user_friendly: welcomeMessage,
        query: '', 
        csv_download_link: '' 
      }]);
    }
    loadWelcomeMessage();
  }, []);

  const send = async text => {
    console.log("Define send function...");
    
    messageId += 1;
    console.log("User message unique key:",`user-${timestamp+messageId}-${messageId}`);
    const newUserMessage = {
      key: `user-${timestamp+messageId}-${messageId}`,
      type: 'user',
      user_friendly: text,
      query: '',
      csv_download_link: ''
    };
    console.log("Define newUserMessage...", newUserMessage);

    messageId += 1;
    console.log("Loading message unique key:",`bot-${timestamp+messageId}-${messageId}`);
    const loadingMessage = {
      key: `bot-${timestamp+messageId}-${messageId}`,
      type: 'bot',
      user_friendly: "...",
      query: '',
      csv_download_link: ''
    };
    console.log("Define loadingMessage...", loadingMessage);
    const withoutLoadingMessage = [...messages, newUserMessage];

  
    // Update the state immediately with the user's message
    setMessages(messages => [...messages, newUserMessage, loadingMessage]);

    // Then, asynchronously get the bot's response
    const botResponse = await ChatbotAPI.GetChatbotResponse(text);
    console.log("Retrieved bot response successfully...", botResponse);
    messageId += 1;
    console.log("Bot response unique key:",`bot-${timestamp+messageId}-${messageId}`);
    const newBotMessage = {
      key: `bot-${timestamp+messageId}-${messageId}`,
      type: 'bot',
      user_friendly: botResponse.user_friendly,
      query: botResponse.query,
      csv_download_link: botResponse.csv_download_link,
    };
    console.log("Define newBotMessage...", newBotMessage);

    setMessages(messages => [...withoutLoadingMessage, newBotMessage]);
  };
  

  return (
    <div className="chatbot">
      <Header />
      <Messages messages={messages.map((msg) =>
      msg.type === 'user' ? 
      <UserMessage key={msg.key} user_friendly={msg.user_friendly} query={msg.query} csv_download_link={msg.csv_download_link} /> :
      <BotMessage 
        key={msg.key} 
        user_friendly={msg.user_friendly}
        query={msg.query} 
        csv_download_link={msg.csv_download_link}
  />
)} />
    <Input onSend={send} />
    </div>
  );

}

const rootElement = document.getElementById("root");
ReactDOM.render(<Chatbot />, rootElement);
