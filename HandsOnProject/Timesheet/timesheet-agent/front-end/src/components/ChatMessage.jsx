import React from "react";
import logo from "../assets/logo.png";

export const ChatMessage = ({ text, sender }) => {
  const isUser = sender === "user";

  return (
    <div className={`chat-message ${isUser ? "user-message" : "agent-message"}`}>
      <div className="avatar-container">
        {!isUser && <img src={logo} alt="agent-avatar" className="avatar" />}
      </div>
      <div className="message-bubble">
        <p>{text}</p>
      </div>
      <div className="avatar-container">
        {isUser && <img src={logo} alt="user-avatar" className="avatar" />}
      </div>
    </div>
  );
};
