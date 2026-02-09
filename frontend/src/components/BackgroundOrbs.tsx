import React from 'react';
import { ANIMATION_DELAYS } from '../constants';

export const BackgroundOrbs: React.FC = () => {
    return (
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
            <div
                className="absolute top-20 left-20 w-72 h-72 bg-indigo-300/20 rounded-full blur-3xl animate-float"
                style={{ animationDelay: ANIMATION_DELAYS.ORB_1 }}
            />
            <div
                className="absolute bottom-20 right-20 w-96 h-96 bg-blue-300/20 rounded-full blur-3xl animate-float"
                style={{ animationDelay: ANIMATION_DELAYS.ORB_2 }}
            />
            <div
                className="absolute top-1/2 left-1/2 w-80 h-80 bg-cyan-300/15 rounded-full blur-3xl animate-float"
                style={{ animationDelay: ANIMATION_DELAYS.ORB_3 }}
            />
        </div>
    );
};
