import React, { useState, useRef, useEffect } from "react";
import { IoMdTime } from "react-icons/io";

export const History = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const historyRef = useRef(null);

  const historyItems = [
    "Connected to TimesheetDB at 2025-07-19 07:30 AM",
    "Disconnected from BikeStores at 2025-07-19 07:15 AM",
    "Connected to AdventureWorks2022 at 2025-07-19 07:00 AM",
    "Query executed on TimesheetDB at 2025-07-19 06:45 AM",
    "Backup completed for BikeStores at 2025-07-19 06:30 AM",
    "Connected to TimesheetDB at 2025-07-19 06:15 AM",
    "Error in AdventureWorks2022 at 2025-07-19 06:00 AM",
  ];

  const displayedItems = showAll ? historyItems : historyItems.slice(0, 5);

  const handleToggle = () => {
    setIsOpen((prevIsOpen) => !prevIsOpen);
  };

  const handleShowAll = () => {
    setShowAll(true);
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      // Close if clicked outside the history container, but not on the button itself
      if (
        historyRef.current &&
        !historyRef.current.contains(event.target) &&
        !event.target.closest(".history-button")
      ) {
        setIsOpen(false);
        setShowAll(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  return (
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
              {item}
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
  );
};
