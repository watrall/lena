import { AskResponse } from '../../lib/api';

export type ChatMessage =
    | {
        id: string;
        role: 'user';
        content: string;
        createdAt: Date;
    }
    | {
        id: string;
        role: 'assistant';
        content: string;
        createdAt: Date;
        response: AskResponse;
        showCitations: boolean;
        feedback?: 'helpful' | 'not_helpful';
        escalationStatus?: 'suggested' | 'opted_out' | 'submitted';
        questionText: string;
    };
