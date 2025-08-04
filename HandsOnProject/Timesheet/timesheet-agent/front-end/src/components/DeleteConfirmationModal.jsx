import React from "react";
import { IoWarningOutline } from "react-icons/io5";

export const DeleteConfirmationModal = ({
  isOpen,
  onClose,
  onConfirm,
  message,
}) => {
  if (!isOpen) return null;

  return (
    <div className="delete-modal-overlay">
      <div className="delete-modal-content">
        <div className="delete-model-header">
          <h3>
           Warning
          </h3>
        </div>
        <p>{message}</p>
        <div className="delete-form-actions">
          <button className="delete-cancel-button" onClick={onClose}>
            Cancel
          </button>
          <button className="delete-delete-button" onClick={onConfirm}>
            Delete
          </button>
        </div>
      </div>
    </div>
  );
};