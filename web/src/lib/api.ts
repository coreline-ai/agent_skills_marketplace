// Both server-side and client-side use the same public API URL on Render.
// NEXT_PUBLIC_API_URL is available on both sides.
function getApiBaseUrl() {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
}

export const API_BASE_URL = getApiBaseUrl();

type RequestMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export class ApiError extends Error {
    status: number;
    constructor(status: number, statusText: string) {
        super(`API Error: ${status} ${statusText}`);
        this.name = "ApiError";
        this.status = status;
    }
}

interface RequestOptions {
    method?: RequestMethod;
    headers?: Record<string, string>;
    body?: unknown;
    token?: string;
}

export async function fetchApi<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = "GET", headers = {}, body, token } = options;

    const config: RequestInit = {
        method,
        headers: {
            "Content-Type": "application/json",
            ...headers,
        },
        cache: 'no-store',
    };

    if (token) {
        config.headers = {
            ...config.headers,
            Authorization: `Bearer ${token}`,
        };
    }

    if (body !== undefined) {
        config.body = JSON.stringify(body);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    try {
        const fullUrl = `${API_BASE_URL}${endpoint}`;
        console.log(`[API Request] ${method} ${fullUrl}`); // Debug log

        const response = await fetch(fullUrl, {
            ...config,
            signal: controller.signal,
        });
        clearTimeout(timeoutId);

        if (!response.ok) {
            // 401 is an expected auth flow (token expired/missing) — not a real error
            if (response.status === 401) {
                throw new ApiError(response.status, response.statusText);
            }
            console.error(`[API Error] ${response.status} ${response.statusText} at ${fullUrl}`);
            throw new ApiError(response.status, response.statusText);
        }

        if (response.status === 204) {
            return {} as T;
        }

        return response.json();
    } catch (error) {
        clearTimeout(timeoutId);
        console.error(`[API Fetch Failed] ${endpoint}:`, error);
        throw error;
    }
}

// Helper methods
export const api = {
    get: <T>(endpoint: string, token?: string) => fetchApi<T>(endpoint, { method: "GET", token }),
    post: <T>(endpoint: string, body: unknown, token?: string) =>
        fetchApi<T>(endpoint, { method: "POST", body, token }),
    patch: <T>(endpoint: string, body: unknown, token?: string) =>
        fetchApi<T>(endpoint, { method: "PATCH", body, token }),
    delete: <T>(endpoint: string, token?: string) => fetchApi<T>(endpoint, { method: "DELETE", token }),
};
