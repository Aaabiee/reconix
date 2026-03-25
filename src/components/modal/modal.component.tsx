'use client';

import React, { ReactNode, useEffect, useRef, useCallback } from 'react';
import { X } from 'lucide-react';
import './modal.component.scss';

interface ModalProps {
  isOpen: boolean;
  title: string;
  children: ReactNode;
  onClose: () => void;
  onConfirm?: () => void;
  confirmText?: string;
  cancelText?: string;
  isLoading?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  title,
  children,
  onClose,
  onConfirm,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  isLoading = false,
  size = 'md',
}) => {
  const dialogRef = useRef<HTMLDivElement>(null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isLoading) {
        onClose();
      }
    },
    [onClose, isLoading]
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
      dialogRef.current?.focus();
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  const sizeClasses: Record<string, string> = {
    sm: 'max-w-sm',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
  };

  return (
    <div
      className="modal-overlay fixed inset-0 z-50 flex items-center justify-center p-4"
      role="presentation"
    >
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm animate-fade-in"
        onClick={() => { if (!isLoading) onClose(); }}
      />

      <div
        ref={dialogRef}
        className={`
          modal-dialog ${sizeClasses[size]} w-full relative
          bg-white rounded-material-lg shadow-elevation-5
          animate-scale-in
        `}
        role="dialog"
        aria-labelledby="modal-title"
        aria-modal="true"
        tabIndex={-1}
      >
        <div className="flex items-center justify-between px-6 py-5 border-b border-surface-200">
          <h2 id="modal-title" className="text-lg font-bold text-default">
            {title}
          </h2>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="p-1.5 rounded-material text-gray-400 hover:text-gray-600 hover:bg-surface-100
                       transition-all duration-150 disabled:opacity-50"
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        </div>

        <div className="px-6 py-5 max-h-[60vh] overflow-y-auto">{children}</div>

        {(onConfirm || cancelText) && (
          <div className="flex gap-3 px-6 py-4 border-t border-surface-200 justify-end bg-surface-50 rounded-b-material-lg">
            <button
              onClick={onClose}
              disabled={isLoading}
              className="px-5 py-2.5 rounded-material font-medium text-gray-700
                         border-2 border-surface-200 hover:bg-surface-100
                         transition-all duration-150
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {cancelText}
            </button>
            {onConfirm && (
              <button
                onClick={onConfirm}
                disabled={isLoading}
                className="btn-primary min-w-[100px]"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Processing...
                  </span>
                ) : (
                  confirmText
                )}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
