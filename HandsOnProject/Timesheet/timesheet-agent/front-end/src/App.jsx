import React, { useState, useEffect } from "react";
import { SideBar } from "./components/SideBar";
import { MainContent } from "./components/MainContent";
import { DatabaseConnectionModal } from "./components/DatabaseConnectionModal";

function App() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newChatTrigger, setNewChatTrigger] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [databases, setDatabases] = useState([]);
  const [selectedDb, setSelectedDb] = useState(null);

  useEffect(() => {
    const storedDatabases = JSON.parse(localStorage.getItem("databases")) || [];
    setDatabases(storedDatabases);
  }, []);

  const handleNewChat = () => {
    setNewChatTrigger((prev) => prev + 1);
  };

  const handleConnectionChange = (status, dbName) => {
    setIsConnected(status);
    if (status) {
      setSelectedDb(dbName);
    }
  };

  const addDatabase = (dbDetails) => {
    const newDatabases = [...databases, dbDetails];
    setDatabases(newDatabases);
    localStorage.setItem("databases", JSON.stringify(newDatabases));
  };

  const handleDatabaseSelection = async (dbName) => {
    const dbDetails = databases.find((db) => db.dbName === dbName);
    if (dbDetails) {
      try {
        const response = await fetch("http://localhost:5000/connect", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(dbDetails),
        });

        if (response.ok) {
          handleConnectionChange(true, dbName);
        } else {
          handleConnectionChange(false, null);
          alert("Failed to connect to the selected database. Please check the credentials or the database status.");
        }
      } catch (error) {
        handleConnectionChange(false, null);
        alert("Failed to connect to the selected database. Please check the credentials or the database status.");
      }
    }
  };

  return (
    <>
      <SideBar
        setIsModalOpen={setIsModalOpen}
        handleNewChat={handleNewChat}
        isConnected={isConnected}
        databases={databases.map((db) => db.dbName)}
        selectedDb={selectedDb}
        handleDatabaseSelection={handleDatabaseSelection}
      />
      <MainContent newChatTrigger={newChatTrigger} />
      {isModalOpen && (
        <DatabaseConnectionModal
          setIsModalOpen={setIsModalOpen}
          handleConnectionChange={handleConnectionChange}
          addDatabase={addDatabase}
        />
      )}
    </>
  );
}

export default App;
