import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { api, TaskStatusResponse, Language } from '../api';
import { TABS, TabType, TASK_STATUS, POLLING, MESSAGES } from '../constants';

interface ProcessingState {
    isProcessing: boolean;
    taskId: string | null;
    status: string | null;
    message: string;
    progress: number;
    vttUrl: string | null;
    error: string | null;
}

export function useTranscription() {
    const [activeTab, setActiveTab] = useState<TabType>(TABS.YOUTUBE);
    const [youtubeUrl, setYoutubeUrl] = useState('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [selectedLanguage, setSelectedLanguage] = useState('th-TH');
    const [languages, setLanguages] = useState<Language[]>([]);
    const [processing, setProcessing] = useState<ProcessingState>({
        isProcessing: false,
        taskId: null,
        status: null,
        message: '',
        progress: 0,
        vttUrl: null,
        error: null,
    });

    const pollingIntervalRef = useRef<number | null>(null);
    const pollErrorCountRef = useRef<number>(0);

    // Fetch supported languages on mount
    useEffect(() => {
        api.getLanguages().then((data) => {
            setLanguages(data.languages);
            setSelectedLanguage(data.default);
        }).catch(console.error);
    }, []);
    // Poll task status
    const pollTaskStatus = useCallback(async (taskId: string) => {
        try {
            const status: TaskStatusResponse = await api.getTaskStatus(taskId);

            // Reset error count on success
            pollErrorCountRef.current = 0;

            setProcessing((prev) => ({
                ...prev,
                status: status.status,
                message: status.message,
                progress: status.progress,
                vttUrl: status.vtt_url,
                error: status.error,
            }));

            // Stop polling if completed or failed
            if (status.status === TASK_STATUS.COMPLETED || status.status === TASK_STATUS.FAILED) {
                if (pollingIntervalRef.current) {
                    clearInterval(pollingIntervalRef.current);
                    pollingIntervalRef.current = null;
                }
                setProcessing((prev) => ({ ...prev, isProcessing: false }));
            }
        } catch (error: unknown) {
            console.error('Error polling task status:', error);
            pollErrorCountRef.current += 1;

            // Check if it's a 404 (task not found) or too many consecutive errors
            const is404 = axios.isAxiosError(error) && error.response?.status === 404;
            const tooManyErrors = pollErrorCountRef.current >= POLLING.MAX_ERRORS;

            if (is404 || tooManyErrors) {
                // Stop polling
                if (pollingIntervalRef.current) {
                    clearInterval(pollingIntervalRef.current);
                    pollingIntervalRef.current = null;
                }
                const errorMsg = is404 ? MESSAGES.TASK_NOT_FOUND : MESSAGES.CONNECTION_LOST;
                setProcessing((prev) => ({
                    ...prev,
                    isProcessing: false,
                    status: TASK_STATUS.FAILED,
                    message: errorMsg,
                    error: errorMsg,
                }));
            }
        }
    }, []);

    // Start polling
    const startPolling = useCallback((taskId: string) => {
        // Clear any existing interval
        if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
        }

        // Reset error count
        pollErrorCountRef.current = 0;

        // Poll immediately
        pollTaskStatus(taskId);

        // Then poll every 2 seconds
        pollingIntervalRef.current = window.setInterval(() => {
            pollTaskStatus(taskId);
        }, POLLING.INTERVAL_MS);
    }, [pollTaskStatus]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
            }
        };
    }, []);

    // Handle YouTube transcription
    const handleYouTubeSubmit = async () => {
        if (!youtubeUrl.trim()) return;

        setProcessing({
            isProcessing: true,
            taskId: null,
            status: TASK_STATUS.PENDING,
            message: 'Starting transcription...',
            progress: 0,
            vttUrl: null,
            error: null,
        });

        try {
            const response = await api.transcribeYouTube(youtubeUrl, selectedLanguage);
            setProcessing((prev) => ({
                ...prev,
                taskId: response.task_id,
                status: response.status,
                message: response.message,
            }));
            startPolling(response.task_id);
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to start transcription';
            setProcessing({
                isProcessing: false,
                taskId: null,
                status: TASK_STATUS.FAILED,
                message: 'Failed to start transcription',
                progress: 0,
                vttUrl: null,
                error: errorMessage,
            });
        }
    };

    // Handle file upload transcription
    const handleFileSubmit = async () => {
        if (!selectedFile) return;

        setProcessing({
            isProcessing: true,
            taskId: null,
            status: TASK_STATUS.PENDING,
            message: 'Uploading file...',
            progress: 0,
            vttUrl: null,
            error: null,
        });

        try {
            const response = await api.transcribeUpload(selectedFile, selectedLanguage);
            setProcessing((prev) => ({
                ...prev,
                taskId: response.task_id,
                status: response.status,
                message: response.message,
            }));
            startPolling(response.task_id);
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to upload file';
            setProcessing({
                isProcessing: false,
                taskId: null,
                status: TASK_STATUS.FAILED,
                message: 'Failed to upload file',
                progress: 0,
                vttUrl: null,
                error: errorMessage,
            });
        }
    };

    // Reset state
    const reset = () => {
        if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
        }
        setProcessing({
            isProcessing: false,
            taskId: null,
            status: null,
            message: '',
            progress: 0,
            vttUrl: null,
            error: null,
        });
        setYoutubeUrl('');
        setSelectedFile(null);
    };

    // Download VTT
    const downloadVtt = () => {
        if (processing.taskId) {
            const url = api.downloadVtt(processing.taskId);
            window.open(url, '_blank');
        }
    };

    return {
        activeTab,
        setActiveTab,
        youtubeUrl,
        setYoutubeUrl,
        selectedFile,
        setSelectedFile,
        selectedLanguage,
        setSelectedLanguage,
        languages,
        processing,
        handleYouTubeSubmit,
        handleFileSubmit,
        reset,
        downloadVtt,
    };
}
