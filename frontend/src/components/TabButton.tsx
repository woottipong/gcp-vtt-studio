import React from 'react';
import { LucideIcon } from 'lucide-react';

interface TabButtonProps {
    active: boolean;
    icon: LucideIcon;
    label: string;
    onClick: () => void;
    disabled?: boolean;
}

export const TabButton: React.FC<TabButtonProps> = ({
    active,
    icon: Icon,
    label,
    onClick,
    disabled = false,
}) => {
    const baseClasses = 'flex items-center gap-2 px-6 py-3 font-semibold rounded-xl transition-all duration-200';
    const activeClasses = active
        ? 'bg-gradient-to-r from-indigo-600 to-blue-600 text-white shadow-lg scale-105'
        : 'bg-white/50 text-gray-600 hover:bg-white/80 hover:text-gray-900';
    const disabledClasses = disabled ? 'opacity-50 cursor-not-allowed' : '';

    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={`${baseClasses} ${activeClasses} ${disabledClasses}`}
        >
            <Icon className="w-5 h-5" />
            {label}
        </button>
    );
};
