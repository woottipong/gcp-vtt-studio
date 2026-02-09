import { Youtube, FileAudio, Download, RotateCcw, Subtitles, Sparkles } from 'lucide-react';
import { useTranscription } from './hooks/useTranscription';
import {
    ProgressIndicator,
    FileUpload,
    LanguageSelector,
    BackgroundOrbs,
    InfoCard,
    TabButton,
    Button,
    Spinner,
} from './components';
import { TABS, TASK_STATUS, MESSAGES } from './constants';

function App() {
    const {
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
    } = useTranscription();

    const isSubmitDisabled =
        processing.isProcessing ||
        (activeTab === TABS.YOUTUBE && !youtubeUrl.trim()) ||
        (activeTab === TABS.UPLOAD && !selectedFile);

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-indigo-50 to-blue-50 relative overflow-hidden">
            <BackgroundOrbs />

            <header className="relative glass-card border-0 border-b border-white/30 shadow-lg">
                <div className="max-w-5xl mx-auto px-6 py-6">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-gradient-to-br from-indigo-600 to-blue-600 rounded-2xl shadow-lg animate-float">
                            <Subtitles className="w-8 h-8 text-white" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold gradient-text">Auto VTT Studio</h1>
                            <p className="text-sm text-gray-600 mt-0.5">
                                Generate VTT subtitles from YouTube or audio files • Powered by AI
                            </p>
                        </div>
                    </div>
                </div>
            </header>

            <main className="relative max-w-5xl mx-auto px-6 py-10">
                <div className="card">
                    <div className="flex gap-3 mb-8">
                        <TabButton
                            active={activeTab === TABS.YOUTUBE}
                            icon={Youtube}
                            label="YouTube URL"
                            onClick={() => setActiveTab(TABS.YOUTUBE)}
                            disabled={processing.isProcessing}
                        />
                        <TabButton
                            active={activeTab === TABS.UPLOAD}
                            icon={FileAudio}
                            label="Upload Audio File"
                            onClick={() => setActiveTab(TABS.UPLOAD)}
                            disabled={processing.isProcessing}
                        />
                    </div>

                    <div className="space-y-6">
                        {activeTab === TABS.YOUTUBE ? (
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-3">
                                        🎬 YouTube URL
                                    </label>
                                    <input
                                        type="url"
                                        value={youtubeUrl}
                                        onChange={(e) => setYoutubeUrl(e.target.value)}
                                        placeholder="https://www.youtube.com/watch?v=..."
                                        disabled={processing.isProcessing}
                                        className="input-field text-base"
                                    />
                                </div>
                            </div>
                        ) : (
                            <FileUpload
                                selectedFile={selectedFile}
                                onFileSelect={setSelectedFile}
                                disabled={processing.isProcessing}
                            />
                        )}

                        <LanguageSelector
                            languages={languages}
                            selectedLanguage={selectedLanguage}
                            onChange={setSelectedLanguage}
                            disabled={processing.isProcessing}
                        />

                        {(processing.isProcessing || processing.status) && (
                            <div className="animate-slide-up">
                                <ProgressIndicator
                                    progress={processing.progress}
                                    status={processing.status}
                                    message={processing.message}
                                />
                            </div>
                        )}

                        {processing.error && (
                            <div className="bg-gradient-to-r from-red-50 to-pink-50 border-l-4 border-red-400 rounded-lg p-4 animate-slide-up">
                                <p className="text-red-700 font-medium">
                                    <strong>❌ Error:</strong> {processing.error}
                                </p>
                            </div>
                        )}

                        <div className="flex flex-wrap gap-3 pt-4">
                            {processing.status === TASK_STATUS.COMPLETED ? (
                                <>
                                    <Button onClick={downloadVtt} icon={Download}>
                                        Download VTT
                                    </Button>
                                    <Button onClick={reset} variant="secondary" icon={RotateCcw}>
                                        Start New
                                    </Button>
                                </>
                            ) : (
                                <>
                                    <Button
                                        onClick={activeTab === TABS.YOUTUBE ? handleYouTubeSubmit : handleFileSubmit}
                                        disabled={isSubmitDisabled}
                                        icon={processing.isProcessing ? undefined : Sparkles}
                                    >
                                        {processing.isProcessing ? (
                                            <>
                                                <Spinner />
                                                {MESSAGES.PROCESSING}
                                            </>
                                        ) : (
                                            MESSAGES.GENERATE_SUBTITLES
                                        )}
                                    </Button>
                                    {processing.status === TASK_STATUS.FAILED && (
                                        <Button onClick={reset} variant="secondary" icon={RotateCcw}>
                                            Try Again
                                        </Button>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                </div>

                <div className="mt-10 grid md:grid-cols-3 gap-6 animate-fade-in">
                    <InfoCard
                        icon="🎬"
                        title="YouTube Support"
                        description="Paste any YouTube URL and we'll extract the audio for transcription."
                    />
                    <InfoCard
                        icon="🎤"
                        title="Multiple Formats"
                        description="Upload WAV, MP3, FLAC, OGG, M4A, AAC, or WMA audio files."
                    />
                    <InfoCard
                        icon="🌐"
                        title="Thai Language"
                        description="Optimized for Thai (th-TH) with support for multiple languages."
                    />
                </div>
            </main>

            <footer className="relative text-center py-8 text-sm text-gray-500">
                <p className="font-medium">✨ Powered by <span className="gradient-text font-semibold">Google Cloud Speech-to-Text V2</span></p>
            </footer>
        </div>
    );
}

export default App;
