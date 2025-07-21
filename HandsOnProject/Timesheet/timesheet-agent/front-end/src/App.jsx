import React, { useState } from "react";
import { SideBar } from "./components/SideBar";
import { MainContent } from "./components/MainContent";
import { DatabaseConnectionModal } from "./components/DatabaseConnectionModal";

function App() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newChatTrigger, setNewChatTrigger] = useState(0);

  const handleNewChat = () => {
    setNewChatTrigger((prev) => prev + 1);
  };

  return (
    <>
      <SideBar setIsModalOpen={setIsModalOpen} handleNewChat={handleNewChat} />
      <MainContent newChatTrigger={newChatTrigger} />
      {isModalOpen && (
        <DatabaseConnectionModal setIsModalOpen={setIsModalOpen} />
      )}
    </>
  );
}

export default App;
