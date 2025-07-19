import React, { useState, useEffect, useRef } from "react";
import { IoIosClose } from "react-icons/io";
import { ThreeDots } from "react-loader-spinner";

export const DatabaseConnectionModal = ({ setIsModalOpen }) => {
  const [connectionDetails, setConnectionDetails] = useState({
    hostname: "",
    port: "",
    dbName: "",
    username: "",
    password: "",
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const modalRef = useRef(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setConnectionDetails((prevDetails) => ({
      ...prevDetails,
      [name]: value,
    }));
    // Clear error on change
    if (errors[name]) {
      setErrors((prevErrors) => ({ ...prevErrors, [name]: null }));
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!connectionDetails.hostname)
      newErrors.hostname = "Hostname is required.";
    if (!connectionDetails.port) newErrors.port = "Port is required.";
    if (!connectionDetails.dbName)
      newErrors.dbName = "Database name is required.";
    if (!connectionDetails.username)
      newErrors.username = "Username is required.";
    return newErrors;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsLoading(true);
    // Simulate a network request
    setTimeout(() => {
      setIsLoading(false);
      console.log("Connection Details:", connectionDetails);
      setIsModalOpen(false); // Close modal on success
    }, 2000);
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (modalRef.current && !modalRef.current.contains(event.target)) {
        setIsModalOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [setIsModalOpen]);

  return (
    <div className="modal-overlay">
      <div className="modal-content" ref={modalRef}>
        <div className="model-header">
          <h3>Database Connection</h3>
          <IoIosClose
            role="button"
            className="close-model"
            onClick={() => setIsModalOpen(false)}
          />
        </div>
        <form onSubmit={handleSubmit} className="model-form">
          <div className="form-control">
            <label htmlFor="hostname">Hostname/IP</label>
            <input
              type="text"
              name="hostname"
              id="hostname"
              className={`hostname-input ${
                errors.hostname ? "input-error" : ""
              }`}
              value={connectionDetails.hostname}
              placeholder="Hostname"
              onChange={handleChange}
            />
            {errors.hostname && (
              <span className="error-message">{errors.hostname}</span>
            )}
          </div>
          <div className="form-control">
            <label htmlFor="port">Port</label>
            <input
              type="text"
              name="port"
              id="port"
              className={errors.port ? "input-error" : ""}
              value={connectionDetails.port}
              placeholder="Port"
              onChange={handleChange}
            />
            {errors.port && (
              <span className="error-message">{errors.port}</span>
            )}
          </div>
          <div className="form-control">
            <label htmlFor="dbName">Database Name</label>
            <input
              type="text"
              name="dbName"
              id="dbName"
              className={errors.dbName ? "input-error" : ""}
              value={connectionDetails.dbName}
              placeholder="Database name"
              onChange={handleChange}
            />
            {errors.dbName && (
              <span className="error-message">{errors.dbName}</span>
            )}
          </div>
          <div className="form-control">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              name="username"
              id="username"
              className={errors.username ? "input-error" : ""}
              value={connectionDetails.username}
              placeholder="Username"
              onChange={handleChange}
            />
            {errors.username && (
              <span className="error-message">{errors.username}</span>
            )}
          </div>
          <div className="form-control">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              name="password"
              id="password"
              value={connectionDetails.password}
              placeholder="Password"
              onChange={handleChange}
            />
          </div>
          <div className="form-actions">
            {isLoading && (
              <ThreeDots
                height="30"
                width="30"
                radius="9"
                color="var(--dark-clr)"
                ariaLabel="three-dots-loading"
                wrapperStyle={{}}
                wrapperClassName=""
                visible={true}
              />
            )}
            <button
              type="submit"
              className="connect-button"
              disabled={isLoading}
            >
              <span className="button-text">
                {isLoading ? "Connecting..." : "Connect"}
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
