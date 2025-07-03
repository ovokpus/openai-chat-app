import { API_ENDPOINTS } from '../../constants';
import type { UploadResponse } from '../../types';

export const uploadDocument = async (
  file: File,
  apiKey: string,
  sessionId?: string
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('api_key', apiKey);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  const response = await fetch(API_ENDPOINTS.UPLOAD, {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
};

export const deleteDocument = async (
  sessionId: string,
  documentName: string,
  apiKey: string
): Promise<{
  success: boolean;
  message: string;
  remaining_documents?: string[];
  document_count?: number;
}> => {
  const response = await fetch(
    `${API_ENDPOINTS.DELETE_DOCUMENT}/${sessionId}/${encodeURIComponent(documentName)}?api_key=${apiKey}`,
    {
      method: 'DELETE',
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}; 