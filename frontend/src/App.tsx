import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    CloudArrowUpIcon,
    CheckCircleIcon,
    ArrowPathIcon,
    CpuChipIcon,
    SparklesIcon,
    LinkIcon
} from '@heroicons/react/24/outline';
import { FileUpload, LanguageSelector, ProgressIndicator } from './components';
import { useTranscription } from './hooks/useTranscription';
import { LanguageCode } from './constants';

const App: React.FC = () => {
    const [inputType, setInputType] = useState<'file' | 'url'>('url');
    const [file, setFile] = useState<File | null>(null);
    const [url, setUrl] = useState('');
    const [language, setLanguage] = useState<LanguageCode>('th-TH');
    const { status, progress, message, error, result, transcribeFile, transcribeUrl, reset } = useTranscription();

    const handleTranscribe = async () => {
        if (inputType === 'file') {
            if (!file) return;
            await transcribeFile(file, language);
        } else {
            if (!url) return;
            await transcribeUrl(url, language);
        }
    };

    return (
        <div className="min-h-screen relative overflow-hidden flex flex-col items-center py-12 px-4 sm:px-6 lg:px-8 bg-[#020617]">
            {/* Background Decorative Elements */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[500px] opacity-30 pointer-events-none">
                <div className="absolute inset-0 bg-gradient-to-b from-brand-500/20 to-transparent blur-[120px]" />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="relative z-10 w-full max-w-2xl text-center mb-16"
            >
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-sm font-medium mb-6 mx-auto">
                    <SparklesIcon className="w-4 h-4" />
                    <span>Next-gen VTT Generation</span>
                </div>
                <h1 className="text-5xl sm:text-6xl font-bold tracking-tight mb-6">
                    <span className="gradient-text">Auto VTT</span> Studio
                </h1>
                <p className="text-slate-400 text-lg sm:text-xl max-w-xl mx-auto leading-relaxed">
                    Transform your video and audio into professional subtitles using Google's Chirp 2 model and advanced NLP processing.
                </p>
            </motion.div>

            <motion.main
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
                className="relative z-10 w-full max-w-3xl"
            >
                <div className="premium-card">
                    <AnimatePresence mode="wait">
                        {status === 'idle' && (
                            <motion.div
                                key="upload-step"
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.95 }}
                                className="space-y-8"
                            >
                                {/* Tab Switcher */}
                                <div className="flex bg-slate-900/50 p-1 rounded-xl border border-slate-800">
                                    <button
                                        onClick={() => setInputType('url')}
                                        className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-medium transition-all duration-200 ${inputType === 'url'
                                            ? 'bg-slate-800 text-white shadow-lg border border-slate-700'
                                            : 'text-slate-400 hover:text-slate-200'
                                            }`}
                                    >
                                        <LinkIcon className="w-4 h-4" />
                                        YouTube / URL
                                    </button>
                                    <button
                                        onClick={() => setInputType('file')}
                                        className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-medium transition-all duration-200 ${inputType === 'file'
                                            ? 'bg-slate-800 text-white shadow-lg border border-slate-700'
                                            : 'text-slate-400 hover:text-slate-200'
                                            }`}
                                    >
                                        <CloudArrowUpIcon className="w-4 h-4" />
                                        File Upload
                                    </button>
                                </div>

                                {inputType === 'url' ? (
                                    <div className="space-y-4">
                                        <label className="block text-sm font-medium text-slate-400 ml-1">
                                            Video / Audio URL
                                        </label>
                                        <div className="relative group">
                                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-500 group-focus-within:text-brand-400">
                                                <LinkIcon className="w-5 h-5 transition-colors" />
                                            </div>
                                            <input
                                                type="text"
                                                value={url}
                                                onChange={(e) => setUrl(e.target.value)}
                                                placeholder="https://www.youtube.com/watch?v=..."
                                                className="w-full bg-slate-900/50 border border-slate-800 text-white pl-12 pr-4 py-4 rounded-2xl focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500 transition-all outline-none placeholder:text-slate-600 shadow-sm"
                                            />
                                        </div>
                                        <p className="text-xs text-slate-500 ml-1">
                                            Supports YouTube, Google Drive, and direct media links.
                                        </p>
                                    </div>
                                ) : (
                                    <FileUpload
                                        onFileSelect={setFile}
                                        selectedFile={file}
                                    />
                                )}

                                <div className="space-y-4">
                                    <label className="block text-sm font-medium text-slate-400 ml-1">
                                        Processing Language
                                    </label>
                                    <LanguageSelector
                                        selected={language}
                                        onSelect={setLanguage}
                                    />
                                </div>

                                <button
                                    onClick={handleTranscribe}
                                    disabled={inputType === 'file' ? !file : !url}
                                    className="btn-primary w-full group"
                                >
                                    <span className="relative flex items-center justify-center gap-2">
                                        Translate to Subtitles
                                        <SparklesIcon className="w-5 h-5 group-hover:rotate-12 transition-transform" />
                                    </span>
                                </button>
                            </motion.div>
                        )}

                        {status === 'processing' && (
                            <motion.div
                                key="processing-step"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="py-12 space-y-8"
                            >
                                <div className="flex justify-center">
                                    <div className="relative">
                                        <div className="absolute inset-0 bg-brand-500/20 blur-2xl rounded-full animate-pulse" />
                                        <div className="relative bg-slate-900 p-6 rounded-3xl border border-brand-500/30">
                                            <CpuChipIcon className="w-12 h-12 text-brand-400 animate-pulse" />
                                        </div>
                                    </div>
                                </div>
                                <div className="text-center space-y-2">
                                    <h3 className="text-xl font-semibold text-white">Refining Your Subtitles</h3>
                                    <p className="text-slate-400">{message || "Google Chirp 2 is processing your file..."}</p>
                                </div>
                                <ProgressIndicator progress={progress} />
                            </motion.div>
                        )}

                        {status === 'completed' && result && (
                            <motion.div
                                key="completed-step"
                                initial={{ opacity: 0, scale: 1.05 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="text-center space-y-8"
                            >
                                <div className="flex justify-center">
                                    <div className="bg-emerald-500/10 p-4 rounded-full border border-emerald-500/20">
                                        <CheckCircleIcon className="w-16 h-16 text-emerald-500" />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <h3 className="text-2xl font-bold text-white">Transcribed Successfully</h3>
                                    <p className="text-slate-400">Your VTT file is ready for download.</p>
                                </div>

                                <div className="bg-slate-900/50 rounded-2xl border border-slate-800 p-6">
                                    <p className="text-sm text-slate-500 mb-4 uppercase tracking-wider font-semibold">File Details</p>
                                    <div className="grid grid-cols-2 gap-4 text-left">
                                        <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/50">
                                            <p className="text-xs text-slate-500 mb-1">Duration</p>
                                            <p className="text-white font-medium">{result.duration_seconds.toFixed(2)}s</p>
                                        </div>
                                        <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/50">
                                            <p className="text-xs text-slate-500 mb-1">Segments</p>
                                            <p className="text-white font-medium">{result.segments_count}</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex flex-col gap-3">
                                    <a
                                        href={result.vtt_url}
                                        download
                                        className="btn-primary"
                                    >
                                        Download .VTT File
                                    </a>
                                    <button
                                        onClick={reset}
                                        className="btn-secondary"
                                    >
                                        Process New File
                                    </button>
                                </div>
                            </motion.div>
                        )}

                        {status === 'error' && (
                            <motion.div
                                key="error-step"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="text-center space-y-6 py-8"
                            >
                                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-500/10 text-red-500 mb-4">
                                    <ArrowPathIcon className="w-8 h-8" />
                                </div>
                                <div className="space-y-2">
                                    <h3 className="text-xl font-bold text-white">Something went wrong</h3>
                                    <p className="text-red-400 bg-red-500/5 py-2 px-4 rounded-lg border border-red-500/10">
                                        {error}
                                    </p>
                                </div>
                                <button
                                    onClick={reset}
                                    className="btn-secondary w-full"
                                >
                                    Try Again
                                </button>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Footer Info */}
                <div className="mt-8 flex justify-center gap-6 text-slate-500 text-sm">
                    <div className="flex items-center gap-1.5">
                        <div className="w-2 h-2 rounded-full bg-emerald-500" />
                        GCP Chirp 2 (v2) API
                    </div>
                    <div className="flex items-center gap-1.5">
                        <div className="w-2 h-2 rounded-full bg-brand-500" />
                        PyThaiNLP Optimized
                    </div>
                </div>
            </motion.main>
        </div>
    );
};

export default App;
