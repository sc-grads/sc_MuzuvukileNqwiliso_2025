import React, { useState, useRef, useEffect } from "react";
import { IoMdSend } from "react-icons/io";
import { ChatContainer } from "./ChatContainer";

export const MainContent = ({ newChatTrigger }) => {
  const [inputValue, setInputValue] = useState("");
  const textareaRef = useRef(null);
  const [isMultiLine, setIsMultiLine] = useState(false);
  const singleLineHeight = useRef(0);

  // Chat state management
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [chatHasStarted, setChatHasStarted] = useState(false);

  // Message ID generation function
  const generateMessageId = () => {
    return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
  };

  // Function to add a new message to the chat
  const addMessage = (text, sender) => {
    const newMessage = {
      id: generateMessageId(),
      text: text,
      sender: sender, // 'user' or 'agent'
      timestamp: new Date(),
    };

    setMessages((prevMessages) => [...prevMessages, newMessage]);
    return newMessage;
  };

  // Function to add user message
  const addUserMessage = (text) => {
    return addMessage(text, "user");
  };

  // Function to add agent message
  const addAgentMessage = (text) => {
    return addMessage(text, "agent");
  };

  // Function to clear all messages (for new chat functionality)
  const clearMessages = () => {
    setMessages([]);
    setIsTyping(false); // Reset typing indicator
    setChatHasStarted(false);
  };

  // Effect to handle new chat trigger from SideBar
  useEffect(() => {
    if (newChatTrigger > 0) {
      clearMessages();
      // Focus textarea after new chat
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    }
  }, [newChatTrigger]);

  useEffect(() => {
    if (textareaRef.current) {
      singleLineHeight.current = textareaRef.current.clientHeight;
    }
  }, []);

  const handleInput = (e) => {
    setInputValue(e.target.value);
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      const newScrollHeight = textarea.scrollHeight;
      textarea.style.height = `${newScrollHeight}px`;
      setIsMultiLine(newScrollHeight > singleLineHeight.current);
    }
  };

  // Function to generate mock agent response
  const generateMockResponse = () => {
    const mockResponses = [
      "I understand your question about the data. Let me analyze that for you.",
      "Based on your query, here's what I found in the database.",
      "That's an interesting question. Let me process the information.",
      "I can help you with that data analysis. Here are the results.",
      "Your query has been processed. Here's the information you requested.",
    ];

    // Select a random response
    const randomIndex = Math.floor(Math.random() * mockResponses.length);
    return mockResponses[randomIndex];
  };

  // Function to trigger mock agent response with delay
  const triggerMockAgentResponse = () => {
    // Show typing indicator
    setIsTyping(true);

    // Simulate processing delay (1.5-3 seconds)
    const delay = Math.random() * 1500 + 1500;

    setTimeout(() => {
      // Generate and add mock response
      const mockResponse = generateMockResponse();
      addAgentMessage(mockResponse);

      // Hide typing indicator
      setIsTyping(false);
    }, delay);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log("User question:", inputValue);

    // Add user message to chat
    if (inputValue.trim()) {
      const userMessage = inputValue.trim();
      addUserMessage(userMessage);

      // Start the chat and remove the header
      if (!chatHasStarted) {
        setChatHasStarted(true);
      }

      // Clear textarea after message submission
      setInputValue("");
      setIsMultiLine(false);
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }

      // Trigger mock agent response after user message
      triggerMockAgentResponse();
    }
  };

  return (
    <main className={`main-content ${chatHasStarted ? "chat-active" : ""}`}>
      {!chatHasStarted && (
        <div className="content-header">
          <h2>Talk to Your Data</h2>
          <p>
            Connect your database and ask questions in plain English. Get
            accurate insights, instantly.
          </p>
        </div>
      )}
      {chatHasStarted && (
        <ChatContainer messages={messages} isTyping={isTyping} />
      )}
      <form onSubmit={handleSubmit} className="prompt-form">
        <div className={`input-wrapper ${isMultiLine ? "align-bottom" : ""}`}>
          <textarea
            ref={textareaRef}
            className="prompt-input"
            placeholder="Type your question here..."
            value={inputValue}
            onInput={handleInput}
            rows={1}
          />
          <button type="submit" name="submit" className="send-button">
            <IoMdSend />
          </button>
        </div>
      </form>
    </main>
  );
};
