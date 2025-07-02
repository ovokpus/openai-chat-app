import React, { useState, useRef } from 'react'
import { CloudArrowUpIcon, DocumentIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { uploadDocument } from '../../services/chatApi'
import type { MultiDocumentUploadResponse } from '../../types'
import './PDFUpload.css'

interface DocumentUploadProps {
  apiKey: string
  sessionId?: string
  onUploadSuccess: (response: MultiDocumentUploadResponse) => void
  onUploadError: (error: string) => void
  disabled?: boolean
}

// Supported file types for regulatory documents
const SUPPORTED_FILE_TYPES = [
  '.pdf', '.docx', '.xlsx', '.xls', '.pptx', '.ppt', 
  '.csv', '.sql', '.py', '.js', '.ts', '.md', '.txt'
]

const FILE_TYPE_DESCRIPTIONS = {
  '.pdf': 'PDF Documents',
  '.docx': 'Word Documents', 
  '.xlsx': 'Excel Spreadsheets',
  '.xls': 'Excel Spreadsheets',
  '.pptx': 'PowerPoint Presentations',
  '.ppt': 'PowerPoint Presentations',
  '.csv': 'CSV Files',
  '.sql': 'SQL Files',
  '.py': 'Python Files',
  '.js': 'JavaScript Files',
  '.ts': 'TypeScript Files',
  '.md': 'Markdown Files',
  '.txt': 'Text Files'
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  apiKey,
  sessionId,
  onUploadSuccess,
  onUploadError,
  disabled = false
}) => {
  const [isUploading, setIsUploading] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const isFileTypeSupported = (fileName: string): boolean => {
    const extension = fileName.toLowerCase().substring(fileName.lastIndexOf('.'))
    return SUPPORTED_FILE_TYPES.includes(extension)
  }

  const getFileTypeDescription = (fileName: string): string => {
    const extension = fileName.toLowerCase().substring(fileName.lastIndexOf('.'))
    return FILE_TYPE_DESCRIPTIONS[extension as keyof typeof FILE_TYPE_DESCRIPTIONS] || 'Unknown file type'
  }

  const handleFileSelect = async (file: File) => {
    if (!isFileTypeSupported(file.name)) {
      onUploadError(`Unsupported file type. Supported types: ${SUPPORTED_FILE_TYPES.join(', ')}`)
      return
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      onUploadError('File size must be less than 10MB')
      return
    }

    setIsUploading(true)
    
    try {
      const response = await uploadDocument(file, apiKey, sessionId)
      console.log('DocumentUpload: Upload successful', response) // Debug log
      onUploadSuccess(response)
    } catch (error) {
      console.error('DocumentUpload: Upload failed', error) // Debug log
      onUploadError(error instanceof Error ? error.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  const handleClick = () => {
    if (!disabled && !isUploading) {
      fileInputRef.current?.click()
    }
  }

  return (
    <div className="pdf-upload">
      <div
        className={`pdf-upload-area ${isDragOver ? 'drag-over' : ''} ${isUploading ? 'uploading' : ''} ${disabled ? 'disabled' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={SUPPORTED_FILE_TYPES.join(',')}
          onChange={handleFileInputChange}
          style={{ display: 'none' }}
          disabled={disabled || isUploading}
        />
        
        {isUploading ? (
          <div className="upload-loading">
            <div className="upload-spinner"></div>
            <p>Processing document...</p>
          </div>
        ) : (
          <div className="upload-content">
            <CloudArrowUpIcon className="upload-icon" />
            <p className="upload-text">
              Drop your regulatory document here or <span className="upload-link">click to browse</span>
            </p>
            <p className="upload-hint">
              Supports: PDF, Word, Excel, PowerPoint, CSV, SQL, Python, etc. (Max: 10MB)
            </p>
          </div>
        )}
      </div>
      
      <div className="supported-types">
        <details>
          <summary>Supported file types</summary>
          <div className="file-types-grid">
            {Object.entries(FILE_TYPE_DESCRIPTIONS).map(([ext, desc]) => (
              <div key={ext} className="file-type-item">
                <code>{ext}</code> - {desc}
              </div>
            ))}
          </div>
        </details>
      </div>
    </div>
  )
}

// Keep the old component name for backward compatibility
export const PDFUpload = DocumentUpload 