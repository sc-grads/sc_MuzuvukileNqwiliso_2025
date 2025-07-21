import React, { useState } from "react";
import { SideBar } from "./components/SideBar";
import { MainContent } from "./components/MainContent";
import { DatabaseConnectionModal } from "./components/DatabaseConnectionModal";

function App() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [chatKey, setChatKey] = useState(0);

  const handleNewChat = () => {
    setChatKey((prevKey) => prevKey + 1);
  };

  return (
    <>
      <SideBar setIsModalOpen={setIsModalOpen} handleNewChat={handleNewChat} />
      <MainContent key={chatKey} />
      {isModalOpen && <DatabaseConnectionModal setIsModalOpen={setIsModalOpen} />}
    </>
  );
}

export default App;
