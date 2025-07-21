import React from "react";

export const MessageBubble = ({ message }) => {
  const { text, sender, timestamp } = message;

  return (
    <div
      className={`message-bubble ${
        sender === "user" ? "user-message" : "agent-message"
      }`}
    >
      <div className="message-text">{text}</div>
      <div className="message-timestamp">
        {timestamp.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        })}
      </div>
    </div>
  );
};
