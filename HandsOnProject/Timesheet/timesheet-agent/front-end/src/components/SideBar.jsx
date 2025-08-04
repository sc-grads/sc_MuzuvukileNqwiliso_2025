import React from "react";
import { DatabaseStatus } from "./DatabaseStatus";
import logo from "../assets/logo-1.png";
import { LiaEdit } from "react-icons/lia";
import { History } from "./History";
import { IoIosAdd } from "react-icons/io";
import { Link } from "react-router-dom";

export const SideBar = ({
  setIsModalOpen,
  handleNewChat,
  isConnected,
  databases,
  selectedDb,
  handleDatabaseSelection,
}) => {
  return (
    <>
      <div className="side-bar">
        <div className="logo-container">
          <Link to={"/"} className="logo-link">
            <img src={logo} alt="logo" className="logo-icon" />
          </Link>
        </div>
        <DatabaseStatus
          isConnected={isConnected}
          databases={databases}
          selectedDb={selectedDb}
          onSelect={handleDatabaseSelection}
        />
        <button className="new-chat-btn" onClick={handleNewChat}>
          <LiaEdit />
          New Chat
        </button>
        <History />
        <button className="add-database" onClick={() => setIsModalOpen(true)}>
          <IoIosAdd />
          Add Database
        </button>
      </div>
    </>
  );
};
