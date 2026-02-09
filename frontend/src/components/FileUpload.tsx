import { CloudArrowUpIcon, DocumentIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useRef } from 'react';
import { FILE_UPLOAD } from '../constants';
import { formatFileSize, cn } from '../utils';

interface FileUploadProps {
    selectedFile: File | null;
    onFileSelect: (file: File | null) => void;
    disabled?: boolean;
}

export const FileUpload = ({ selectedFile, onFileSelect, disabled = false }: FileUploadProps) => {
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
        <div className="space-y-4">
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
                    'group relative border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-300',
                    disabled && 'opacity-50 cursor-not-allowed',
                    selectedFile
                        ? 'border-brand-500/50 bg-brand-500/5'
                        : 'border-slate-800 bg-slate-900/50 hover:border-brand-500/30 hover:bg-slate-900'
                )}
            >
                {selectedFile ? (
                    <div className="flex items-center justify-between bg-slate-900/80 p-4 rounded-xl border border-brand-500/20">
                        <div className="flex items-center gap-4">
                            <div className="p-2 bg-brand-500/10 rounded-lg">
                                <DocumentIcon className="w-6 h-6 text-brand-400" />
                            </div>
                            <div className="text-left">
                                <p className="font-medium text-white truncate max-w-[200px]">{selectedFile.name}</p>
                                <p className="text-xs text-slate-400">
                                    {formatFileSize(selectedFile.size)}
                                </p>
                            </div>
                        </div>
                        {!disabled && (
                            <button
                                onClick={handleRemove}
                                className="p-1.5 hover:bg-red-500/10 text-slate-500 hover:text-red-400 rounded-lg transition-colors"
                            >
                                <XMarkIcon className="w-5 h-5" />
                            </button>
                        )}
                    </div>
                ) : (
                    <div className="flex flex-col items-center gap-4">
                        <div className="p-4 bg-slate-950 rounded-2xl border border-slate-800 group-hover:border-brand-500/30 transition-colors">
                            <CloudArrowUpIcon className="w-10 h-10 text-slate-500 group-hover:text-brand-400 transition-colors" />
                        </div>
                        <div>
                            <p className="text-lg font-semibold text-white">Upload your audio</p>
                            <p className="text-sm text-slate-400 mt-1">
                                Drag and drop or click to browse
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <span className="px-2 py-1 rounded bg-slate-950 border border-slate-800 text-[10px] text-slate-500 uppercase font-bold tracking-wider">MP3</span>
                            <span className="px-2 py-1 rounded bg-slate-950 border border-slate-800 text-[10px] text-slate-500 uppercase font-bold tracking-wider">WAV</span>
                            <span className="px-2 py-1 rounded bg-slate-950 border border-slate-800 text-[10px] text-slate-500 uppercase font-bold tracking-wider">M4A</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
