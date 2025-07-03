import React, { useState, useRef } from 'react'
import { CloudArrowUpIcon, DocumentIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { uploadDocument } from '../../services/chatApi'
import type { UploadResponse } from '../../types'
import './DocumentUpload.css'

interface DocumentUploadProps {
  apiKey: string
  sessionId?: string
  onUploadSuccess: (response: UploadResponse) => void
  onUploadError: (error: string) => void
  disabled?: boolean
}

// Define supported file types
const SUPPORTED_FILE_TYPES = {
  '.pdf': 'PDF Document',
  '.docx': 'Word Document',
  '.txt': 'Text File',
  '.md': 'Markdown File',
  '.markdown': 'Markdown File',
  '.csv': 'CSV File',
  '.xlsx': 'Excel Spreadsheet',
  '.xls': 'Excel Spreadsheet (Legacy)',
  '.pptx': 'PowerPoint Presentation',
  '.html': 'HTML Document',
  '.htm': 'HTML Document'
}

const SUPPORTED_MIME_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
  'text/markdown',
  'text/csv',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'text/html',
  'application/html'
]

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

  const validateFile = (file: File): { isValid: boolean; error?: string } => {
    // Check file extension
    const fileExtension = file.name.toLowerCase().match(/\.[^.]+$/)?.[0]
    
    if (!fileExtension || !Object.keys(SUPPORTED_FILE_TYPES).includes(fileExtension)) {
      const supportedTypes = Object.entries(SUPPORTED_FILE_TYPES)
        .map(([ext, name]) => `${name} (${ext})`)
        .join(', ')
      
      return {
        isValid: false,
        error: `Unsupported file type. Supported types: ${supportedTypes}`
      }
    }

    // Check file size (15MB limit for documents, larger than PDF-only limit)
    if (file.size > 15 * 1024 * 1024) {
      return {
        isValid: false,
        error: 'File size must be less than 15MB'
      }
    }

    return { isValid: true }
  }

  const getFileTypeIcon = (filename: string): string => {
    const extension = filename.toLowerCase().match(/\.[^.]+$/)?.[0]
    
    switch (extension) {
      case '.pdf':
        return '📄'
      case '.docx':
        return '📝'
      case '.txt':
        return '📋'
      case '.md':
      case '.markdown':
        return '📖'
      case '.csv':
        return '📊'
      case '.xlsx':
      case '.xls':
        return '📈'
      case '.pptx':
        return '🎞️'
      case '.html':
      case '.htm':
        return '🌐'
      default:
        return '📄'
    }
  }

  const handleFileSelect = async (file: File) => {
    const validation = validateFile(file)
    
    if (!validation.isValid) {
      onUploadError(validation.error || 'Invalid file')
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

  const acceptedFileTypes = Object.keys(SUPPORTED_FILE_TYPES).join(',')
  const supportedTypesText = Object.entries(SUPPORTED_FILE_TYPES)
    .map(([ext, name]) => name)
    .join(', ')

  return (
    <div className="document-upload">
      <div
        className={`document-upload-area ${isDragOver ? 'drag-over' : ''} ${isUploading ? 'uploading' : ''} ${disabled ? 'disabled' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedFileTypes}
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
              Drop your document here or <span className="upload-link">click to browse</span>
            </p>
            <div className="supported-types">
              <p className="upload-hint">Supported formats: {supportedTypesText}</p>
              <p className="upload-hint">Maximum file size: 15MB</p>
            </div>
            <div className="file-type-icons">
              {Object.entries(SUPPORTED_FILE_TYPES).map(([ext, name]) => (
                <span key={ext} className="file-type-icon" title={name}>
                  {getFileTypeIcon(`file${ext}`)}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
} 