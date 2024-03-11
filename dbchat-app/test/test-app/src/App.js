import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom";

import BotMessage from "./components/BotMessage";
import UserMessage from "./components/UserMessage";
import Messages from "./components/Messages";
import Input from "./components/Input";

import ChatbotAPI from "./ChatbotAPI";

import "./styles.css";
import Header from "./components/Header";

function Chatbot() {
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    async function loadWelcomeMessage() {
      const response = await API.GetChatbotResponse("load welcome message"); # this is not right fix it 
      setMessages([
        <BotMessage key="0" text={response.message} />,
      ]);
    }
    loadWelcomeMessage();
  }, []);

  const send = async text => {
    const userMessage = <UserMessage key={messages.length + 1} text={text} />;
    const botResponse = <BotMessage key={messages.length + 2} fetchMessage={async () => await API.GetChatbotResponse(text)} />;
    const newMessages = [...messages, userMessage, botResponse];
    setMessages(newMessages);
  };

  return (
    <div className="chatbot">
      <Header />
      <Messages messages={messages} />
      <Input onSend={send} />
    </div>
  );
}

const rootElement = document.getElementById("root");
ReactDOM.render(<Chatbot />, rootElement);
