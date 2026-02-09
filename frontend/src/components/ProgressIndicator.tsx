import React from 'react';

interface ProgressIndicatorProps {
    progress: number;
    status: string | null;
    message: string;
}

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
    progress,
    status,
    message,
}) => {
    const getStatusColor = () => {
        switch (status) {
            case 'completed':
                return 'bg-green-500';
            case 'failed':
                return 'bg-red-500';
            case 'transcribing':
                return 'bg-purple-500';
            default:
                return 'bg-primary-500';
        }
    };

    const getStatusIcon = () => {
        switch (status) {
            case 'downloading':
                return '⬇️';
            case 'converting':
                return '🔄';
            case 'uploading':
                return '⬆️';
            case 'transcribing':
                return '🎤';
            case 'completed':
                return '✅';
            case 'failed':
                return '❌';
            default:
                return '⏳';
        }
    };

    return (
        <div className="w-full space-y-3">
            <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2">
                    <span className="text-lg">{getStatusIcon()}</span>
                    <span className="font-medium text-gray-700">{message}</span>
                </span>
                <span className="font-semibold text-gray-600">{progress}%</span>
            </div>

            <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                <div
                    className={`h-full transition-all duration-500 ease-out ${getStatusColor()} ${status !== 'completed' && status !== 'failed' ? 'animate-pulse' : ''
                        }`}
                    style={{ width: `${progress}%` }}
                />
            </div>

            {status && status !== 'completed' && status !== 'failed' && (
                <p className="text-xs text-gray-500 text-center">
                    Please wait while we process your audio. This may take several minutes for longer files.
                </p>
            )}
        </div>
    );
};
