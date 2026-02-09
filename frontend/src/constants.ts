// Language codes
export type LanguageCode = 'th-TH' | 'en-US' | 'ja-JP';

// Tab types
export const TABS = {
    YOUTUBE: 'youtube',
    UPLOAD: 'upload',
} as const;

export type TabType = typeof TABS[keyof typeof TABS];

// Task status types
export const TASK_STATUS = {
    PENDING: 'pending',
    PROCESSING: 'processing',
    COMPLETED: 'completed',
    FAILED: 'failed',
} as const;

export type TaskStatus = typeof TASK_STATUS[keyof typeof TASK_STATUS];

// Polling configuration
export const POLLING = {
    INTERVAL_MS: 2000,
    MAX_ERRORS: 3,
} as const;

// File upload configuration
export const FILE_UPLOAD = {
    ACCEPTED_FORMATS: '.wav,.mp3,.flac,.ogg,.m4a,.aac,.wma',
    ACCEPTED_EXTENSIONS: ['wav', 'mp3', 'flac', 'ogg', 'm4a', 'aac', 'wma'],
    MAX_SIZE_MB: 500,
} as const;

// Animation delays for background orbs
export const ANIMATION_DELAYS = {
    ORB_1: '0s',
    ORB_2: '1s',
    ORB_3: '2s',
} as const;

// API endpoints are defined in api.ts

// UI Messages
export const MESSAGES = {
    TASK_NOT_FOUND: 'Task not found. The server may have restarted. Please try again.',
    CONNECTION_LOST: 'Lost connection to server. Please try again.',
    PROCESSING: 'Processing...',
    GENERATE_SUBTITLES: 'Generate Subtitles',
} as const;
