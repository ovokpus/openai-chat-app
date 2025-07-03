import { API_ENDPOINTS } from '../../constants';
import type { SessionInfo } from '../../types';

export const getSessionInfo = async (sessionId: string): Promise<SessionInfo> => {
  const response = await fetch(`${API_ENDPOINTS.SESSION_INFO}/${sessionId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
};

export const deleteSession = async (sessionId: string): Promise<void> => {
  const response = await fetch(`${API_ENDPOINTS.SESSION_INFO}/${sessionId}`, {
    method: 'DELETE'
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }
}; 