import { API_ENDPOINTS, CHAT_CONFIG } from '../../constants';
import type { SessionInfo } from '../../types';

interface SessionBackup extends SessionInfo {
  lastSaved: number;
  documents: string[];
  apiKey?: string;
}

// localStorage keys
const SESSION_BACKUP_KEY = 'ragSessionBackup';
const SESSION_DOCUMENTS_KEY = 'ragSessionDocuments';

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

// Local storage backup utilities
export const saveSessionBackup = (sessionInfo: SessionInfo, documents?: string[]): void => {
  try {
    const backup: SessionBackup = {
      ...sessionInfo,
      lastSaved: Date.now(),
      documents: documents || sessionInfo.documents || []
    };
    
    localStorage.setItem(SESSION_BACKUP_KEY, JSON.stringify(backup));
    
    // Also save documents separately for easier access
    if (documents) {
      localStorage.setItem(SESSION_DOCUMENTS_KEY, JSON.stringify(documents));
    }
    
    console.log('💾 Session backup saved:', backup);
  } catch (error) {
    console.warn('Failed to save session backup:', error);
  }
};

export const getSessionBackup = (): SessionBackup | null => {
  try {
    const backup = localStorage.getItem(SESSION_BACKUP_KEY);
    if (!backup) return null;
    
    const parsed: SessionBackup = JSON.parse(backup);
    const age = Date.now() - parsed.lastSaved;
    
    // Only return backup if it's less than session timeout + 5 minutes buffer
    if (age < CHAT_CONFIG.SESSION_TIMEOUT + (5 * 60 * 1000)) {
      console.log('📂 Session backup found:', parsed);
      return parsed;
    } else {
      console.log('🗑️ Session backup expired, removing');
      clearSessionBackup();
      return null;
    }
  } catch (error) {
    console.warn('Failed to read session backup:', error);
    return null;
  }
};

export const clearSessionBackup = (): void => {
  try {
    localStorage.removeItem(SESSION_BACKUP_KEY);
    localStorage.removeItem(SESSION_DOCUMENTS_KEY);
    console.log('🗑️ Session backup cleared');
  } catch (error) {
    console.warn('Failed to clear session backup:', error);
  }
};

export const getBackupDocuments = (): string[] => {
  try {
    const documents = localStorage.getItem(SESSION_DOCUMENTS_KEY);
    return documents ? JSON.parse(documents) : [];
  } catch (error) {
    console.warn('Failed to read backup documents:', error);
    return [];
  }
};

export const isSessionBackupAvailable = (): boolean => {
  const backup = getSessionBackup();
  return backup !== null;
}; 