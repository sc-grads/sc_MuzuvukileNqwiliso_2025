import React, { useState, useRef } from "react";
import { IoMdTime } from "react-icons/io";
import { MdDeleteOutline } from "react-icons/md";
import { DeleteConfirmationModal } from "./DeleteConfirmationModal";

export const History = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const [historyItems, setHistoryItems] = useState([
    "Connected to TimesheetDB at 2025-07-19 07:30 AM",
    "Disconnected from BikeStores at 2025-07-19 07:15 AM",
    "Connected to AdventureWorks2022 at 2025-07-19 07:00 AM",
    "Query executed on TimesheetDB at 2025-07-19 06:45 AM",
    "Backup completed for BikeStores at 2025-07-19 06:30 AM",
    "Connected to TimesheetDB at 2025-07-19 06:15 AM",
    "Error in AdventureWorks2022 at 2025-07-19 06:00 AM",
  ]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState(null);
  const historyRef = useRef(null);

  const displayedItems = showAll ? historyItems : historyItems.slice(0, 5);

  const handleToggle = () => {
    setIsOpen((prevIsOpen) => !prevIsOpen);
  };

  const handleShowAll = () => {
    setShowAll(true);
  };

  const handleDeleteClick = (index) => {
    setItemToDelete(index);
    setIsModalOpen(true);
  };

  const handleConfirmDelete = () => {
    setHistoryItems((prevItems) =>
      prevItems.filter((_, i) => i !== itemToDelete)
    );
    setIsModalOpen(false);
    setItemToDelete(null);
  };

  return (
    <>
      <div className="history-container" ref={historyRef}>
        <button className="history-button" onClick={handleToggle}>
          <IoMdTime /> History
        </button>
        <div
          className={`history-selector ${isOpen ? "selector-active" : ""}`}
          tabIndex={-1}
        >
          <ul className="history-list">
            {displayedItems.map((item, index) => (
              <li key={index} className="history-item">
                <span className="history-item-text">{item}</span>
                <MdDeleteOutline
                  className="delete-icon"
                  onClick={() => handleDeleteClick(index)}
                />
              </li>
            ))}
            {!showAll && historyItems.length > 5 && (
              <li className="show-all-item">
                <button className="show-all-button" onClick={handleShowAll}>
                  Show All
                </button>
              </li>
            )}
          </ul>
        </div>
      </div>
      <DeleteConfirmationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConfirm={handleConfirmDelete}
        message="Are you sure you want to delete this chat history?"
      />
    </>
  );
};
