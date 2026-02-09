import axios from 'axios';

const API_BASE_URL = '/api';

export interface Language {
    code: string;
    name: string;
}

export interface LanguagesResponse {
    languages: Language[];
    default: string;
}

export interface TaskResponse {
    task_id: string;
    status: string;
    message: string;
    progress: number;
}

export interface TaskStatusResponse {
    task_id: string;
    status: string;
    message: string;
    progress: number;
    vtt_url: string | null;
    error: string | null;
    duration_seconds?: number;
    segments_count?: number;
}

export const api = {
    // Get supported languages
    getLanguages: async (): Promise<LanguagesResponse> => {
        const response = await axios.get(`${API_BASE_URL}/languages`);
        return response.data;
    },

    // Transcribe YouTube URL
    transcribeYouTube: async (url: string, languageCode: string): Promise<TaskResponse> => {
        const response = await axios.post(`${API_BASE_URL}/transcribe/youtube`, {
            url,
            language_code: languageCode,
        });
        return response.data;
    },

    // Transcribe uploaded file
    transcribeUpload: async (file: File, languageCode: string): Promise<TaskResponse> => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('language_code', languageCode);

        const response = await axios.post(`${API_BASE_URL}/transcribe/upload`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    // Get task status
    getTaskStatus: async (taskId: string): Promise<TaskStatusResponse> => {
        const response = await axios.get(`${API_BASE_URL}/task/${taskId}`);
        return response.data;
    },

    // Download VTT file
    downloadVtt: (taskId: string): string => {
        return `${API_BASE_URL}/task/${taskId}/download`;
    },
};
