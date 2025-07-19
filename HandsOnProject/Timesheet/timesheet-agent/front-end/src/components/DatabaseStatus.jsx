import React, { useState, useEffect, useRef } from "react";
import {
  IoIosCheckmarkCircleOutline,
  IoIosCheckmarkCircle,
} from "react-icons/io";
import { IoChevronDown } from "react-icons/io5";


export const DatabaseStatus = () => {
  const labelStatus = "Not connected";
  const isConnected = labelStatus === "Connected";

  const [isOpen, setIsOpen] = useState(false);
  const [selectedDb, setSelectedDb] = useState("TimesheetDB");
  const dropdownRef = useRef(null);

  const databases = ["TimesheetDB", "BikeStores", "AdventureWorks2022"];

  const handleToggle = () => {
    setIsOpen(!isOpen);
  };

  const handleSelect = (db) => {
    setSelectedDb(db);
    setIsOpen(false);
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <div id="database-status-widget" className="status-container">
      <div className="status-content">
        <h3>Database Status</h3>
        <div
          className={`status-indicator ${
            isConnected ? "connected" : "not-connected"
          }`}
        >
          <span className="status-icon">
            <IoIosCheckmarkCircleOutline
              className={`check-mark ${
                isConnected ? "connected" : "not-connected"
              }`}
            />
          </span>
          <div
            className={`status-label ${
              isConnected ? "connected" : "not-connected"
            }`}
          >
            {labelStatus}
          </div>
        </div>
      </div>
      <div className="db-selection">
        <div className="container">
          <span className="choose-label">Current Database</span>
          <div
            className={`database-selector ${isOpen ? "selector-active" : ""}`}
            onClick={handleToggle}
            ref={dropdownRef}
            tabIndex={1}
          >
            <div className="select-box">
              <span className="selected-db">{selectedDb}</span>
              <IoChevronDown className="select-arrow" />
            </div>
            <input type="hidden" name="database" value={selectedDb} />
            <ul className="menu-list">
              {databases.map((db) => (
                <li key={db} id={db} onClick={() => handleSelect(db)}>
                  {db}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
