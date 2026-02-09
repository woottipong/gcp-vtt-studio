import React from 'react';
import { LanguageCode } from '../constants';

interface Language {
    code: LanguageCode;
    name: string;
}

const SUPPORTED_LANGUAGES: Language[] = [
    { code: 'th-TH', name: 'Thai' },
    { code: 'en-US', name: 'English' },
    { code: 'ja-JP', name: 'Japanese' },
];

interface LanguageSelectorProps {
    selected: LanguageCode;
    onSelect: (code: LanguageCode) => void;
    disabled?: boolean;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
    selected,
    onSelect,
    disabled = false,
}) => {
    return (
        <div className="grid grid-cols-3 gap-2">
            {SUPPORTED_LANGUAGES.map((lang) => (
                <button
                    key={lang.code}
                    onClick={() => onSelect(lang.code)}
                    disabled={disabled}
                    className={`
                        px-4 py-3 rounded-xl border text-sm font-medium transition-all
                        ${selected === lang.code 
                            ? 'bg-brand-500/10 border-brand-500/50 text-brand-400' 
                            : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'}
                        disabled:opacity-50 disabled:cursor-not-allowed
                    `}
                >
                    {lang.name}
                </button>
            ))}
        </div>
    );
};
