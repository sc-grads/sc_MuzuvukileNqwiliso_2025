import React, { useEffect, useRef, useState } from "react";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";

export const ChatContainer = ({ messages, isTyping }) => {
  const chatContainerRef = useRef(null);
  const chatEndRef = useRef(null);
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  const [scrollTimeout, setScrollTimeout] = useState(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const isScrolledToBottom = () => {
    if (!chatContainerRef.current) return true;

    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    // Consider "near bottom" as within 50px of the actual bottom
    return scrollHeight - scrollTop - clientHeight < 50;
  };

  const handleScroll = () => {
    if (!chatContainerRef.current) return;

    // Clear existing timeout
    if (scrollTimeout) {
      clearTimeout(scrollTimeout);
    }

    // Check if user is scrolling up from the bottom
    const isAtBottom = isScrolledToBottom();
    setIsUserScrolling(!isAtBottom);

    // Set a timeout to reset user scrolling state after they stop scrolling
    const newTimeout = setTimeout(() => {
      setIsUserScrolling(false);
    }, 1000);

    setScrollTimeout(newTimeout);
  };

  // Auto-scroll to bottom when new messages are added, but only if user hasn't manually scrolled up
  useEffect(() => {
    if (!isUserScrolling) {
      scrollToBottom();
    }
  }, [messages, isTyping, isUserScrolling]);

  // Clean up timeout on unmount
  useEffect(() => {
    return () => {
      if (scrollTimeout) {
        clearTimeout(scrollTimeout);
      }
    };
  }, [scrollTimeout]);

  return (
    <div
      className="chat-container"
      ref={chatContainerRef}
      onScroll={handleScroll}
    >
      <div className="message-list">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isTyping && <TypingIndicator isVisible={true} />}
        <div ref={chatEndRef} />
      </div>
    </div>
  );
};
