import React from 'react';
import { LucideIcon } from 'lucide-react';

type ButtonVariant = 'primary' | 'secondary';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: ButtonVariant;
    icon?: LucideIcon;
    children: React.ReactNode;
}

const variantClasses: Record<ButtonVariant, string> = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
};

export const Button: React.FC<ButtonProps> = ({
    variant = 'primary',
    icon: Icon,
    children,
    className = '',
    ...props
}) => {
    return (
        <button
            className={`${variantClasses[variant]} flex items-center gap-2 ${className}`}
            {...props}
        >
            {Icon && <Icon className="w-5 h-5" />}
            {children}
        </button>
    );
};
