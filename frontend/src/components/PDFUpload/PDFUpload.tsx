import React, { useState, useRef } from 'react'
import { CloudArrowUpIcon, DocumentIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { uploadPDF } from '../../services/chatApi'
import type { UploadResponse } from '../../types'
import './PDFUpload.css'

interface PDFUploadProps {
  apiKey: string
  sessionId?: string
  onUploadSuccess: (response: UploadResponse) => void
  onUploadError: (error: string) => void
  disabled?: boolean
}

export const PDFUpload: React.FC<PDFUploadProps> = ({
  apiKey,
  sessionId,
  onUploadSuccess,
  onUploadError,
  disabled = false
}) => {
  const [isUploading, setIsUploading] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (file: File) => {
    if (!file.type.includes('pdf')) {
      onUploadError('Please select a PDF file')
      return
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      onUploadError('File size must be less than 10MB')
      return
    }

    setIsUploading(true)
    
    try {
      const response = await uploadPDF(file, apiKey, sessionId)
      console.log('PDFUpload: Upload successful', response) // Debug log
      onUploadSuccess(response)
    } catch (error) {
      console.error('PDFUpload: Upload failed', error) // Debug log
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
          accept=".pdf"
          onChange={handleFileInputChange}
          style={{ display: 'none' }}
          disabled={disabled || isUploading}
        />
        
        {isUploading ? (
          <div className="upload-loading">
            <div className="upload-spinner"></div>
            <p>Processing PDF...</p>
          </div>
        ) : (
          <div className="upload-content">
            <CloudArrowUpIcon className="upload-icon" />
            <p className="upload-text">
              Drop your PDF here or <span className="upload-link">click to browse</span>
            </p>
            <p className="upload-hint">Maximum file size: 10MB</p>
          </div>
        )}
      </div>
    </div>
  )
} 