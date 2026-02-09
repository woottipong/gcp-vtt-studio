import { Youtube, FileAudio, Download, RotateCcw, Subtitles } from 'lucide-react';
import { useTranscription } from './hooks/useTranscription';
import { ProgressIndicator, FileUpload, LanguageSelector } from './components';

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
        (activeTab === 'youtube' && !youtubeUrl.trim()) ||
        (activeTab === 'upload' && !selectedFile);

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-purple-50 to-pink-50 relative overflow-hidden">
            {/* Animated Background Orbs */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
                <div className="absolute top-20 left-20 w-72 h-72 bg-purple-300/30 rounded-full blur-3xl animate-float" />
                <div className="absolute bottom-20 right-20 w-96 h-96 bg-pink-300/30 rounded-full blur-3xl animate-float" style={{ animationDelay: '1s' }} />
                <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-red-300/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
            </div>

            {/* Header */}
            <header className="relative glass-card border-0 border-b border-white/30 shadow-lg">
                <div className="max-w-5xl mx-auto px-6 py-6">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl shadow-lg animate-float">
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

            {/* Main Content */}
            <main className="relative max-w-5xl mx-auto px-6 py-10">
                <div className="card">
                    {/* Tabs */}
                    <div className="flex border-b border-gray-200 mb-6">
                        <button
                            onClick={() => setActiveTab('youtube')}
                            disabled={processing.isProcessing}
                            className={`flex items-center gap-2 px-6 py-3 font-medium transition-colors border-b-2 -mb-px ${activeTab === 'youtube'
                                ? 'border-primary-600 text-primary-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700'
                                } ${processing.isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            <Youtube className="w-5 h-5" />
                            YouTube URL
                        </button>
                        <button
                            onClick={() => setActiveTab('upload')}
                            disabled={processing.isProcessing}
                            className={`flex items-center gap-2 px-6 py-3 font-medium transition-colors border-b-2 -mb-px ${activeTab === 'upload'
                                ? 'border-primary-600 text-primary-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700'
                                } ${processing.isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            <FileAudio className="w-5 h-5" />
                            Upload Audio File
                        </button>
                    </div>

                    {/* Tab Content */}
                    <div className="space-y-6">
                        {activeTab === 'youtube' ? (
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

                        {/* Language Selector */}
                        <LanguageSelector
                            languages={languages}
                            selectedLanguage={selectedLanguage}
                            onChange={setSelectedLanguage}
                            disabled={processing.isProcessing}
                        />

                        {/* Progress Indicator */}
                        {(processing.isProcessing || processing.status) && (
                            <div className="glass-card p-6 animate-slide-up">
                                <ProgressIndicator
                                    progress={processing.progress}
                                    status={processing.status}
                                    message={processing.message}
                                />
                            </div>
                        )}

                        {/* Error Message */}
                        {processing.error && (
                            <div className="bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-200/50 rounded-xl p-5 animate-slide-up">
                                <p className="text-red-700 font-medium">
                                    <strong>❌ Error:</strong> {processing.error}
                                </p>
                            </div>
                        )}

                        {/* Action Buttons */}
                        <div className="flex flex-wrap gap-3 pt-4">
                            {processing.status === 'completed' ? (
                                <>
                                    <button
                                        onClick={downloadVtt}
                                        className="btn-primary flex items-center gap-2"
                                    >
                                        <Download className="w-5 h-5" />
                                        Download VTT
                                    </button>
                                    <button
                                        onClick={reset}
                                        className="btn-secondary flex items-center gap-2"
                                    >
                                        <RotateCcw className="w-5 h-5" />
                                        Start New
                                    </button>
                                </>
                            ) : (
                                <>
                                    <button
                                        onClick={activeTab === 'youtube' ? handleYouTubeSubmit : handleFileSubmit}
                                        disabled={isSubmitDisabled}
                                        className="btn-primary flex items-center gap-2"
                                    >
                                        {processing.isProcessing ? (
                                            <>
                                                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                                Processing...
                                            </>
                                        ) : (
                                            <>
                                                <Subtitles className="w-5 h-5" />
                                                Generate Subtitles
                                            </>
                                        )}
                                    </button>
                                    {processing.status === 'failed' && (
                                        <button
                                            onClick={reset}
                                            className="btn-secondary flex items-center gap-2"
                                        >
                                            <RotateCcw className="w-5 h-5" />
                                            Try Again
                                        </button>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                </div>

                {/* Info Section */}
                <div className="mt-10 grid md:grid-cols-3 gap-6 animate-fade-in">
                    <div className="glass-card p-6 hover:shadow-2xl transform hover:-translate-y-1 transition-all duration-300 group">
                        <div className="text-4xl mb-3 group-hover:scale-110 transition-transform">🎬</div>
                        <h3 className="font-bold text-gray-900 mb-2 text-lg">YouTube Support</h3>
                        <p className="text-sm text-gray-600 leading-relaxed">
                            Paste any YouTube URL and we'll extract the audio for transcription.
                        </p>
                    </div>
                    <div className="glass-card p-6 hover:shadow-2xl transform hover:-translate-y-1 transition-all duration-300 group">
                        <div className="text-4xl mb-3 group-hover:scale-110 transition-transform">🎤</div>
                        <h3 className="font-bold text-gray-900 mb-2 text-lg">Multiple Formats</h3>
                        <p className="text-sm text-gray-600 leading-relaxed">
                            Upload WAV, MP3, FLAC, OGG, M4A, AAC, or WMA audio files.
                        </p>
                    </div>
                    <div className="glass-card p-6 hover:shadow-2xl transform hover:-translate-y-1 transition-all duration-300 group">
                        <div className="text-4xl mb-3 group-hover:scale-110 transition-transform">🌐</div>
                        <h3 className="font-bold text-gray-900 mb-2 text-lg">Thai Language</h3>
                        <p className="text-sm text-gray-600 leading-relaxed">
                            Optimized for Thai (th-TH) with support for multiple languages.
                        </p>
                    </div>
                </div>
            </main>

            {/* Footer */}
            <footer className="relative text-center py-8 text-sm text-gray-500">
                <p className="font-medium">✨ Powered by <span className="gradient-text font-semibold">Google Cloud Speech-to-Text V2</span></p>
            </footer>
        </div>
    );
}

export default App;
