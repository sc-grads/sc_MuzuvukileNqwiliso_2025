import React, { useState, useRef, useEffect } from "react";
import { IoMdSend } from "react-icons/io";

export const MainContent = () => {
  const [inputValue, setInputValue] = useState("");
  const textareaRef = useRef(null);
  const [isMultiLine, setIsMultiLine] = useState(false);
  const singleLineHeight = useRef(0);

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

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log("User question:", inputValue);
    setInputValue("");
    setIsMultiLine(false);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  return (
    <main className="main-content">
      <div className="content-header">
        <h2>Talk to Your Data</h2>
        <p>
          Connect your database and ask questions in plain English. Get accurate
          insights, instantly.
        </p>
      </div>
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
