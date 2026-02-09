import { useState, useCallback, useRef, useEffect } from 'react';
import { api, TaskStatusResponse } from '../api';
import { POLLING, TASK_STATUS } from '../constants';

export type Status = 'idle' | 'processing' | 'completed' | 'error';

export interface Result {
    vtt_url: string;
    duration_seconds: number;
    segments_count: number;
}

export function useTranscription() {
    const [status, setStatus] = useState<Status>('idle');
    const [progress, setProgress] = useState(0);
    const [message, setMessage] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<Result | null>(null);

    const pollingIntervalRef = useRef<number | null>(null);

    const pollTaskStatus = useCallback(async (taskId: string) => {
        try {
            const response: TaskStatusResponse = await api.getTaskStatus(taskId);

            setProgress(response.progress);
            setMessage(response.message || '');

            if (response.status === TASK_STATUS.COMPLETED && response.vtt_url) {
                setStatus('completed');
                setResult({
                    vtt_url: response.vtt_url,
                    duration_seconds: response.duration_seconds || 0,
                    segments_count: response.segments_count || 0,
                });
                if (pollingIntervalRef.current) {
                    clearInterval(pollingIntervalRef.current);
                    pollingIntervalRef.current = null;
                }
            } else if (response.status === TASK_STATUS.FAILED) {
                setStatus('error');
                setError(response.error || 'Transcription failed');
                if (pollingIntervalRef.current) {
                    clearInterval(pollingIntervalRef.current);
                    pollingIntervalRef.current = null;
                }
            } else {
                setStatus('processing');
            }
        } catch (err) {
            console.error('Polling error:', err);
            // Don't immediately fail on a single network error
        }
    }, []);

    const startPolling = useCallback((taskId: string) => {
        if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);

        // Immediate first poll
        pollTaskStatus(taskId);

        pollingIntervalRef.current = window.setInterval(() => {
            pollTaskStatus(taskId);
        }, POLLING.INTERVAL_MS);
    }, [pollTaskStatus]);

    const transcribeFile = async (file: File, language: string) => {
        setStatus('processing');
        setProgress(0);
        setMessage('Uploading file...');
        setError(null);
        setResult(null);

        try {
            const response = await api.transcribeUpload(file, language);
            startPolling(response.task_id);
        } catch (err: any) {
            setStatus('error');
            setError(err.response?.data?.detail || err.message || 'Failed to start transcription');
        }
    };

    const transcribeUrl = async (url: string, language: string) => {
        setStatus('processing');
        setProgress(0);
        setMessage('Initializing URL transcription...');
        setError(null);
        setResult(null);

        try {
            const response = await api.transcribeYouTube(url, language);
            startPolling(response.task_id);
        } catch (err: any) {
            setStatus('error');
            setError(err.response?.data?.detail || err.message || 'Failed to start URL transcription');
        }
    };

    const reset = () => {
        if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
        }
        setStatus('idle');
        setProgress(0);
        setMessage('');
        setError(null);
        setResult(null);
    };

    useEffect(() => {
        return () => {
            if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);
        };
    }, []);

    return {
        status,
        progress,
        message,
        error,
        result,
        transcribeFile,
        transcribeUrl,
        reset,
    };
}
