import React from 'react';

interface SpinnerProps {
    className?: string;
    size?: 'sm' | 'md' | 'lg';
}

const sizeClasses = {
    sm: 'w-4 h-4 border',
    md: 'w-5 h-5 border-2',
    lg: 'w-8 h-8 border-2',
};

export const Spinner: React.FC<SpinnerProps> = ({ className = '', size = 'md' }) => {
    return (
        <div
            className={`${sizeClasses[size]} border-white border-t-transparent rounded-full animate-spin ${className}`}
        />
    );
};
