import React, { useState, useRef, useCallback } from 'react'
import { CloudArrowUpIcon, DocumentIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { uploadDocument } from '../../services/chatApi'
import type { MultiDocumentUploadResponse } from '../../types'
import { logger } from '../../utils/logger'
import './DocumentUpload.css'

interface DocumentUploadProps {
  apiKey: string
  sessionId?: string
  onUploadSuccess: (response: MultiDocumentUploadResponse) => void
  onUploadError: (error: string) => void
  disabled?: boolean
}

// Comprehensive list of supported file types for the knowledge base
const SUPPORTED_DOCUMENT_EXTENSIONS = [
  '.pdf', '.docx', '.xlsx', '.xls', '.pptx', '.ppt', 
  '.csv', '.sql', '.py', '.js', '.ts', '.md', '.txt'
]

// Human-readable descriptions for each supported file type
const DOCUMENT_TYPE_DESCRIPTIONS = {
  '.pdf': 'PDF Documents',
  '.docx': 'Word Documents', 
  '.xlsx': 'Excel Spreadsheets',
  '.xls': 'Legacy Excel Spreadsheets',
  '.pptx': 'PowerPoint Presentations',
  '.ppt': 'Legacy PowerPoint Presentations',
  '.csv': 'Comma-Separated Values',
  '.sql': 'SQL Database Scripts',
  '.py': 'Python Source Code',
  '.js': 'JavaScript Source Code',
  '.ts': 'TypeScript Source Code',
  '.md': 'Markdown Documentation',
  '.txt': 'Plain Text Files'
}

// Maximum file size allowed for upload (10MB)
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
const MAX_FILE_SIZE_DISPLAY = '10MB'

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  apiKey,
  sessionId,
  onUploadSuccess,
  onUploadError,
  disabled = false
}) => {
  const [isUploadingDocument, setIsUploadingDocument] = useState(false)
  const [isDragOverUploadArea, setIsDragOverUploadArea] = useState(false)
  const documentInputRef = useRef<HTMLInputElement>(null)

  /**
   * Validates if the provided file name has a supported extension
   */
  const isDocumentTypeSupported = useCallback((fileName: string): boolean => {
    const fileExtension = fileName.toLowerCase().substring(fileName.lastIndexOf('.'))
    return SUPPORTED_DOCUMENT_EXTENSIONS.includes(fileExtension)
  }, [])

  /**
   * Gets a human-readable description for the file type
   */
  const getDocumentTypeDescription = useCallback((fileName: string): string => {
    const fileExtension = fileName.toLowerCase().substring(fileName.lastIndexOf('.'))
    return DOCUMENT_TYPE_DESCRIPTIONS[fileExtension as keyof typeof DOCUMENT_TYPE_DESCRIPTIONS] || 'Unknown file type'
  }, [])

  /**
   * Validates file size against the maximum allowed size
   */
  const isFileSizeValid = useCallback((fileSize: number): boolean => {
    return fileSize <= MAX_FILE_SIZE_BYTES
  }, [])

  /**
   * Handles the core file upload process with comprehensive validation
   */
  const handleDocumentSelection = useCallback(async (selectedFile: File) => {
    // Validate file type support
    if (!isDocumentTypeSupported(selectedFile.name)) {
      const supportedTypes = SUPPORTED_DOCUMENT_EXTENSIONS.join(', ')
      onUploadError(`Unsupported file type. Supported formats: ${supportedTypes}`)
      return
    }

    // Validate file size
    if (!isFileSizeValid(selectedFile.size)) {
      onUploadError(`File size exceeds ${MAX_FILE_SIZE_DISPLAY} limit. Please choose a smaller file.`)
      return
    }

    setIsUploadingDocument(true)
    
    try {
      logger.debug('DocumentUpload: Starting document upload process', {
        fileName: selectedFile.name,
        fileSize: selectedFile.size,
        fileType: selectedFile.type
      })

      const uploadResponse = await uploadDocument(selectedFile, apiKey, sessionId)
      
      logger.info('DocumentUpload: Document successfully uploaded to knowledge base', {
        fileName: uploadResponse.filename,
        sessionId: uploadResponse.session_id,
        documentCount: uploadResponse.document_count
      })

      onUploadSuccess(uploadResponse)
    } catch (uploadError) {
      logger.error('DocumentUpload: Failed to upload document', {
        fileName: selectedFile.name,
        error: uploadError
      })
      
      const errorMessage = uploadError instanceof Error 
        ? uploadError.message 
        : 'Failed to upload document. Please try again.'
      
      onUploadError(errorMessage)
    } finally {
      setIsUploadingDocument(false)
    }
  }, [apiKey, sessionId, onUploadSuccess, onUploadError, isDocumentTypeSupported, isFileSizeValid])

  /**
   * Handles drag and drop file events
   */
  const handleDragDropFileSelection = useCallback((dragEvent: React.DragEvent) => {
    dragEvent.preventDefault()
    setIsDragOverUploadArea(false)
    
    const droppedFiles = dragEvent.dataTransfer.files
    if (droppedFiles.length > 0) {
      const firstFile = droppedFiles[0]
      handleDocumentSelection(firstFile)
    }
  }, [handleDocumentSelection])

  /**
   * Handles drag over events for visual feedback
   */
  const handleDragOverUploadArea = useCallback((dragEvent: React.DragEvent) => {
    dragEvent.preventDefault()
    setIsDragOverUploadArea(true)
  }, [])

  /**
   * Handles drag leave events to remove visual feedback
   */
  const handleDragLeaveUploadArea = useCallback((dragEvent: React.DragEvent) => {
    dragEvent.preventDefault()
    setIsDragOverUploadArea(false)
  }, [])

  /**
   * Handles file input selection from the file browser
   */
  const handleFileInputChange = useCallback((inputEvent: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = inputEvent.target.files
    if (selectedFiles && selectedFiles.length > 0) {
      const selectedFile = selectedFiles[0]
      handleDocumentSelection(selectedFile)
    }
  }, [handleDocumentSelection])

  /**
   * Triggers the file browser when the upload area is clicked
   */
  const handleUploadAreaClick = useCallback(() => {
    if (!disabled && !isUploadingDocument) {
      documentInputRef.current?.click()
    }
  }, [disabled, isUploadingDocument])

  return (
    <div className="document-upload-container">
      <div
        className={`document-upload-area ${isDragOverUploadArea ? 'drag-over' : ''} ${isUploadingDocument ? 'uploading' : ''} ${disabled ? 'disabled' : ''}`}
        onDrop={handleDragDropFileSelection}
        onDragOver={handleDragOverUploadArea}
        onDragLeave={handleDragLeaveUploadArea}
        onClick={handleUploadAreaClick}
        role="button"
        tabIndex={0}
        aria-label="Upload document to knowledge base"
      >
        <input
          ref={documentInputRef}
          type="file"
          accept={SUPPORTED_DOCUMENT_EXTENSIONS.join(',')}
          onChange={handleFileInputChange}
          style={{ display: 'none' }}
          disabled={disabled || isUploadingDocument}
          aria-label="Select document file"
        />
        
        {isUploadingDocument ? (
          <div className="document-upload-loading-state">
            <div className="document-upload-spinner"></div>
            <p className="upload-loading-message">Processing document and adding to knowledge base...</p>
          </div>
        ) : (
          <div className="document-upload-content">
            <CloudArrowUpIcon className="document-upload-icon" />
            <div className="document-upload-text-container">
              <h3 className="document-upload-title">Add Documents to Knowledge Base</h3>
              <p className="document-upload-description">
                Drop files here or <span className="document-upload-link">browse your device</span>
              </p>
            </div>
            <p className="document-upload-hint">
              Supports: Documents, Spreadsheets, Presentations, Code files, and more (Max: {MAX_FILE_SIZE_DISPLAY})
            </p>
          </div>
        )}
      </div>
      
      <div className="supported-document-types">
        <details>
          <summary>View all supported file formats</summary>
          <div className="document-types-grid">
            {Object.entries(DOCUMENT_TYPE_DESCRIPTIONS).map(([fileExtension, description]) => (
              <div key={fileExtension} className="document-type-item">
                <code className="file-extension">{fileExtension}</code> 
                <span className="file-description">{description}</span>
              </div>
            ))}
          </div>
        </details>
      </div>
    </div>
  )
}

// Export with both names for backward compatibility during transition
export { DocumentUpload as FileUpload }
export default DocumentUpload 