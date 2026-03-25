'use client';

import React, { useState, useCallback } from 'react';
import { Upload, AlertCircle, CheckCircle } from 'lucide-react';
import { recycledSimsService } from '@/services/recycled-sims.service';
import { LoadingSpinner } from '@/components/loading-spinner/loading-spinner.component';
import './bulk-upload.component.scss';

interface UploadStatus {
  status: 'idle' | 'uploading' | 'processing' | 'completed' | 'error';
  message: string;
  progress?: number;
}

interface BulkUploadFormProps {
  onSuccess?: () => void;
}

const ALLOWED_FILE_TYPE = 'text/csv';
const MAX_POLL_ATTEMPTS = 60;
const POLL_INTERVAL_MS = 1000;

export const BulkUploadForm: React.FC<BulkUploadFormProps> = ({ onSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({
    status: 'idle',
    message: '',
  });

  const isValidCsvFile = (f: File): boolean => {
    return f.type === ALLOWED_FILE_TYPE || f.name.endsWith('.csv');
  };

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    e.currentTarget.classList.add('bg-primary-50', 'border-primary-500');
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    e.currentTarget.classList.remove('bg-primary-50', 'border-primary-500');
  }, []);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    e.currentTarget.classList.remove('bg-primary-50', 'border-primary-500');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const droppedFile = files[0];
      if (isValidCsvFile(droppedFile)) {
        setFile(droppedFile);
      } else {
        setUploadStatus({ status: 'error', message: 'Please upload a CSV file' });
      }
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const files = e.currentTarget.files;
    if (files && files.length > 0) {
      setFile(files[0]);
    }
  };

  const handleUpload = async (): Promise<void> => {
    if (!file) {
      setUploadStatus({ status: 'error', message: 'Please select a file' });
      return;
    }

    setUploadStatus({ status: 'uploading', message: 'Uploading file...' });

    try {
      const result = await recycledSimsService.bulkUploadRecycledSims(file);
      setUploadStatus({ status: 'processing', message: `Upload started: ${result.message}` });

      const uploadId = result.uploadId;
      let isComplete = false;
      let attempts = 0;

      while (!isComplete && attempts < MAX_POLL_ATTEMPTS) {
        attempts++;
        await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));

        const status = await recycledSimsService.getUploadStatus(uploadId);

        if (status.status === 'completed' || status.status === 'failed') {
          isComplete = true;

          if (status.status === 'completed') {
            setUploadStatus({
              status: 'completed',
              message: `Upload completed: ${status.successCount} records processed successfully, ${status.failureCount} failed`,
            });
            onSuccess?.();
          } else {
            setUploadStatus({
              status: 'error',
              message: `Upload failed: ${status.errors?.length || 0} errors encountered`,
            });
          }
        }
      }

      if (!isComplete) {
        setUploadStatus({ status: 'error', message: 'Upload processing timeout' });
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      setUploadStatus({ status: 'error', message: errorMessage });
    }
  };

  const isUploading = uploadStatus.status === 'uploading' || uploadStatus.status === 'processing';

  return (
    <div className="bulk-upload space-y-6">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className="bulk-upload__dropzone border-2 border-dashed border-secondary-300 rounded-lg p-8 text-center bg-page hover:border-primary-500 transition-colors cursor-pointer"
      >
        <Upload className="mx-auto mb-4 text-secondary-400" size={32} />
        <p className="text-default font-medium mb-1">Drag and drop your CSV file here</p>
        <p className="text-secondary-600 text-sm mb-4">or</p>
        <label className="inline-block">
          <input
            type="file"
            accept=".csv"
            onChange={handleFileSelect}
            className="hidden"
            aria-label="Select CSV file"
          />
          <span className="px-4 py-2 bg-primary-500 text-surface rounded-lg hover:bg-primary-600 inline-block cursor-pointer font-medium">
            Browse Files
          </span>
        </label>
        <p className="text-secondary-600 text-xs mt-4">CSV file with phone number, NIN, BVN columns</p>
      </div>

      {file && (
        <div className="bg-surface border border-secondary-200 rounded-lg p-4">
          <p className="font-medium text-default">Selected file: {file.name}</p>
          <p className="text-sm text-secondary-600 mt-1">{(file.size / 1024).toFixed(2)} KB</p>
        </div>
      )}

      {uploadStatus.message && (
        <div
          className={`p-4 rounded-lg border flex gap-3 ${
            uploadStatus.status === 'error'
              ? 'bg-error-50 border-error-200 text-error-800'
              : uploadStatus.status === 'completed'
                ? 'bg-success-50 border-success-200 text-success-800'
                : 'bg-primary-50 border-primary-200 text-primary-800'
          }`}
          role="alert"
        >
          {uploadStatus.status === 'error' ? (
            <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
          ) : uploadStatus.status === 'completed' ? (
            <CheckCircle size={20} className="flex-shrink-0 mt-0.5" />
          ) : (
            <LoadingSpinner size="sm" />
          )}
          <div>
            <p className="font-medium">{uploadStatus.message}</p>
          </div>
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!file || isUploading}
        className="w-full px-4 py-2 bg-primary-500 text-surface rounded-lg hover:bg-primary-600 disabled:opacity-50 font-medium transition-colors"
      >
        {isUploading ? 'Processing...' : 'Upload'}
      </button>
    </div>
  );
};
