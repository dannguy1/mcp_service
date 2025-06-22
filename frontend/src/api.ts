import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

interface LogFilters {
    startDate?: string;
    endDate?: string;
    severity?: string[];
    programs?: string[];
}

interface PaginatedResponse<T> {
    logs: {
        logs: T[];
        pagination: {
            total: number;
            per_page: number;
            current_page: number;
            total_pages: number;
            has_next: boolean;
            has_prev: boolean;
        };
    };
    total: number;
}

export interface LogEntry {
    id: number;
    device_id: number;
    device_ip: string;
    timestamp: string;
    level: string;
    program: string;
    message: string;
    raw_message: string;
    structured_data: any;
    pushed_to_ai: boolean;
    pushed_at: string | null;
    push_attempts: number;
    last_push_error: string | null;
}

export const fetchLogs = async (
    filters: LogFilters,
    page: number = 1,
    perPage: number = 25
): Promise<PaginatedResponse<LogEntry>> => {
    try {
        console.log('Fetching logs with filters:', filters);
        const params = new URLSearchParams();
        
        if (filters.startDate) params.append('startDate', filters.startDate);
        if (filters.endDate) params.append('endDate', filters.endDate);
        if (filters.severity?.length) params.append('severity', filters.severity.join(','));
        if (filters.programs?.length) params.append('program', filters.programs.join(','));
        params.append('page', page.toString());
        params.append('per_page', perPage.toString());

        console.log('API Request: GET /logs');
        const response = await axios.get(`${API_BASE_URL}/logs`, { params });
        console.log('API Response:', response.status, '/logs');
        
        return response.data;
    } catch (error) {
        console.error('Error fetching logs:', error);
        throw error;
    }
}; 