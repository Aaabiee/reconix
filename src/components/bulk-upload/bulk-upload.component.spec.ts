import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { BulkUploadForm } from './bulk-upload.component';

jest.mock('@/services/recycled-sims.service', () => ({
  recycledSimsService: {
    bulkUploadRecycledSims: jest.fn(),
    getUploadStatus: jest.fn(),
  },
}));

jest.mock('@/components/loading-spinner/loading-spinner.component', () => ({
  LoadingSpinner: () => React.createElement('div', { 'data-testid': 'loading-spinner' }),
}));

jest.mock('lucide-react', () => ({
  Upload: () => React.createElement('span', null, 'upload'),
  AlertCircle: () => React.createElement('span', null, 'alert'),
  CheckCircle: () => React.createElement('span', null, 'check'),
}));

describe('BulkUploadForm', () => {
  it('renders the drop zone', () => {
    render(React.createElement(BulkUploadForm));
    expect(screen.getByText('Drag and drop your CSV file here')).toBeInTheDocument();
  });

  it('renders the browse files button', () => {
    render(React.createElement(BulkUploadForm));
    expect(screen.getByText('Browse Files')).toBeInTheDocument();
  });

  it('has a file input with CSV accept attribute', () => {
    render(React.createElement(BulkUploadForm));
    const fileInput = screen.getByLabelText('Select CSV file');
    expect(fileInput).toHaveAttribute('accept', '.csv');
  });

  it('renders upload button in disabled state when no file selected', () => {
    render(React.createElement(BulkUploadForm));
    const uploadButton = screen.getByText('Upload');
    expect(uploadButton).toBeDisabled();
  });

  it('shows selected file info when file is chosen', () => {
    render(React.createElement(BulkUploadForm));
    const fileInput = screen.getByLabelText('Select CSV file');
    const testFile = new File(['test,data'], 'test.csv', { type: 'text/csv' });
    fireEvent.change(fileInput, { target: { files: [testFile] } });
    expect(screen.getByText(/Selected file: test.csv/)).toBeInTheDocument();
  });

  it('shows file format requirement text', () => {
    render(React.createElement(BulkUploadForm));
    expect(screen.getByText('CSV file with phone number, NIN, BVN columns')).toBeInTheDocument();
  });
});
