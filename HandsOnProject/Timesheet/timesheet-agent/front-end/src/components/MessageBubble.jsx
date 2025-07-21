import React from "react";

export const MessageBubble = ({ message }) => {
  const { text, sender } = message;

  return (
    <div
      className={`message-bubble ${
        sender === "user" ? "user-message" : "agent-message"
      }`}
    >
      <div className="message-text">{text}</div>
    </div>
  );
};
