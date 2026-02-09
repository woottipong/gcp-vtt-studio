import React from 'react';
import { Language } from '../api';

interface LanguageSelectorProps {
    languages: Language[];
    selectedLanguage: string;
    onChange: (languageCode: string) => void;
    disabled?: boolean;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
    languages,
    selectedLanguage,
    onChange,
    disabled = false,
}) => {
    return (
        <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
                ภาษา
            </label>
            <div className="inline-flex items-center bg-gray-100 rounded-full p-1 gap-1">
                {languages.map((lang) => (
                    <button
                        key={lang.code}
                        onClick={() => onChange(lang.code)}
                        disabled={disabled}
                        className={`
                            px-6 py-2.5 rounded-full font-medium text-sm
                            transition-all duration-300 ease-in-out
                            ${selectedLanguage === lang.code
                                ? 'bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-600 text-white shadow-lg scale-105'
                                : 'text-gray-600 hover:text-gray-900 hover:bg-white/50'
                            }
                            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                        `}
                    >
                        {lang.name}
                    </button>
                ))}
            </div>
        </div>
    );
};
