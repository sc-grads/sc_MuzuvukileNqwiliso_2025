import React, { useState } from "react";
import { SideBar } from "./components/SideBar";
import { MainContent } from "./components/MainContent";
import { DatabaseConnectionModal } from "./components/DatabaseConnectionModal";

function App() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <SideBar setIsModalOpen={setIsModalOpen} />
      <MainContent />
      {isModalOpen && <DatabaseConnectionModal setIsModalOpen={setIsModalOpen} />}
    </>
  );
}

export default App;
