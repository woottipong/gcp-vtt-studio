import React from 'react';

interface ProgressIndicatorProps {
    progress: number;
}

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
    progress,
}) => {
    return (
        <div className="w-full space-y-4">
            <div className="flex justify-between items-end">
                <div className="space-y-1">
                    <p className="text-sm font-medium text-slate-400">Progress</p>
                    <p className="text-2xl font-bold text-white tabular-nums">{progress}%</p>
                </div>
            </div>
            
            <div className="h-3 w-full bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                <div 
                    className="h-full bg-gradient-to-r from-brand-600 to-brand-400 transition-all duration-500 ease-out relative"
                    style={{ width: `${progress}%` }}
                >
                    <div className="absolute inset-0 bg-[linear-gradient(45deg,rgba(255,255,255,0.15)_25%,transparent_25%,transparent_50%,rgba(255,255,255,0.15)_50%,rgba(255,255,255,0.15)_72.5%,transparent_72.5%,transparent)] bg-[length:24px_24px] animate-[progress-stripe_1s_linear_infinite]" />
                </div>
            </div>
        </div>
    );
};
