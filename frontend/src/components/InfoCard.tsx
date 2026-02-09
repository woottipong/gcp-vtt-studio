import React from 'react';

interface InfoCardProps {
    icon: string;
    title: string;
    description: string;
}

export const InfoCard: React.FC<InfoCardProps> = ({ icon, title, description }) => {
    return (
        <div className="glass-card p-6 hover:shadow-2xl transform hover:-translate-y-1 transition-all duration-300 group">
            <div className="text-4xl mb-3 group-hover:scale-110 transition-transform">
                {icon}
            </div>
            <h3 className="font-bold text-gray-900 mb-2 text-lg">{title}</h3>
            <p className="text-sm text-gray-600 leading-relaxed">{description}</p>
        </div>
    );
};
