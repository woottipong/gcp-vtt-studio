import { Upload, X, FileAudio } from 'lucide-react';
import { useRef } from 'react';
import { FILE_UPLOAD } from '../constants';
import { formatFileSize, cn } from '../utils';

interface FileUploadProps {
    selectedFile: File | null;
    onFileSelect: (file: File | null) => void;
    disabled: boolean;
}

export const FileUpload = ({ selectedFile, onFileSelect, disabled }: FileUploadProps) => {
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleClick = () => {
        if (!disabled) {
            fileInputRef.current?.click();
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file && file.size <= FILE_UPLOAD.MAX_SIZE_MB * 1024 * 1024) {
            onFileSelect(file);
        } else if (file) {
            alert(`File size exceeds ${FILE_UPLOAD.MAX_SIZE_MB}MB limit`);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        if (disabled) return;

        const file = e.dataTransfer.files[0];
        if (file && file.size <= FILE_UPLOAD.MAX_SIZE_MB * 1024 * 1024) {
            onFileSelect(file);
        } else if (file) {
            alert(`File size exceeds ${FILE_UPLOAD.MAX_SIZE_MB}MB limit`);
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
    };

    const handleRemove = (e: React.MouseEvent) => {
        e.stopPropagation();
        onFileSelect(null);
    };

    return (
        <div className="space-y-2">
            <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept={FILE_UPLOAD.ACCEPTED_FORMATS}
                className="hidden"
                disabled={disabled}
            />

            <div
                onClick={handleClick}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                className={cn(
                    'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-200',
                    disabled && 'opacity-50 cursor-not-allowed',
                    selectedFile
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50'
                )}
            >
                {selectedFile ? (
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <FileAudio className="w-8 h-8 text-indigo-600" />
                            <div className="text-left">
                                <p className="font-medium text-gray-700">{selectedFile.name}</p>
                                <span className="text-sm text-gray-500">
                                    {formatFileSize(selectedFile.size)}
                                </span>
                            </div>
                        </div>
                        {!disabled && (
                            <button
                                onClick={handleRemove}
                                className="p-1 hover:bg-gray-200 rounded-full transition-colors"
                            >
                                <X className="w-4 h-4 text-gray-500" />
                            </button>
                        )}
                    </div>
                ) : (
                    <div className="flex flex-col items-center gap-3">
                        <Upload className="w-10 h-10 text-gray-400" />
                        <div>
                            <p className="font-medium text-gray-700">
                                Click to upload or drag and drop
                            </p>
                            <p className="text-sm text-gray-500 mt-1">
                                WAV, MP3, FLAC, OGG, M4A, AAC, WMA (max {FILE_UPLOAD.MAX_SIZE_MB}MB)
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
